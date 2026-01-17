import os
from dotenv import load_dotenv

load_dotenv()  # Isso carrega as variáveis do .env

from supabase import create_client, Client
from models.sprint import Sprint, Task, Slot
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def salvar_sprint_db(sprint: Sprint):
    sprint_data = {
        "id": sprint.id,
        "data_inicio": sprint.data_inicio.strftime("%Y-%m-%d"),
        "bloco_min": sprint.bloco_min,
    }
    supabase.table("sprints").upsert(sprint_data).execute()
    for t in sprint.tarefas:
        task_data = {
            "sprint_id": sprint.id,
            "nome": t.nome,
            "tempo_estimado": t.tempo_estimado,
            "tempo_gasto": t.tempo_gasto,
            "blocos_restantes": t.blocos_restantes,
            "cor": t.cor,
        }
        supabase.table("tasks").upsert(task_data).execute()
    for slot in sprint.slots:
        slot_data = {
            "sprint_id": sprint.id,
            "datetime": slot.datetime.isoformat(),
            "status": slot.status,
            "tarefa": slot.tarefa,
        }
        supabase.table("slots").upsert(slot_data).execute()
    # Salva daily_reports
    for dia, tarefas in sprint.daily_reports.items():
        for tarefa_nome, texto in tarefas.items():
            report_data = {
                "sprint_id": sprint.id,
                "dia": dia,
                "tarefa_nome": tarefa_nome,
                "texto": texto,
            }
            supabase.table("daily_reports").upsert(report_data).execute()

def carregar_sprint_db(sprint_id: str) -> Sprint:
    sprint_resp = supabase.table("sprints").select("*").eq("id", sprint_id).execute()
    sprint_data = sprint_resp.data[0]
    sprint = Sprint(sprint_data["id"], datetime.strptime(sprint_data["data_inicio"], "%Y-%m-%d"), sprint_data["bloco_min"])
    # Carrega Tasks
    tasks_resp = supabase.table("tasks").select("*").eq("sprint_id", sprint_id).execute()
    sprint.tarefas = []
    for t in tasks_resp.data:
        task = Task(t["nome"], t["tempo_estimado"], t.get("cor", "azul"))
        task.tempo_gasto = t["tempo_gasto"]
        task.blocos_restantes = t["blocos_restantes"]
        sprint.tarefas.append(task)
    # Carrega Slots
    slots_resp = supabase.table("slots").select("*").eq("sprint_id", sprint_id).execute()
    sprint.slots = []
    from dateutil.parser import parse
    for s in slots_resp.data:
        dt = parse(s["datetime"])
        slot = Slot(dt)
        slot.status = s["status"]
        slot.tarefa = s["tarefa"]
        sprint.slots.append(slot)
    # Carrega daily_reports
    reports_resp = supabase.table("daily_reports").select("*").eq("sprint_id", sprint_id).execute()
    sprint.daily_reports = {}
    for r in reports_resp.data:
        dia = r["dia"]
        tarefa_nome = r["tarefa_nome"]
        texto = r["texto"]
        if dia not in sprint.daily_reports:
            sprint.daily_reports[dia] = {}
        sprint.daily_reports[dia][tarefa_nome] = texto
    return sprint