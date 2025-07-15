# storage/file_store.py

import os
import json
from datetime import datetime
from models.sprint import Sprint, Task, Slot

DATA_DIR = "data"

def salvar_sprint(sprint: Sprint):
    path = os.path.join(DATA_DIR, f"{sprint.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sprint_to_dict(sprint), f, indent=2, default=str)

def carregar_sprint(sprint_id: str) -> Sprint:
    path = os.path.join(DATA_DIR, f"{sprint_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sprint {sprint_id} não encontrada.")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return dict_to_sprint(data)

# ---- Serialização/Deserialização ----

def sprint_to_dict(sprint: Sprint):
    return {
        "id": sprint.id,
        "data_inicio": sprint.data_inicio.strftime("%Y-%m-%d"),
        "bloco_min": sprint.bloco_min,
        "tarefas": [
            {
                "nome": t.nome,
                "tempo_estimado": t.tempo_estimado,
                "tempo_gasto": t.tempo_gasto,
                "blocos_restantes": t.blocos_restantes,
                "cor": t.cor
            } for t in sprint.tarefas
        ],
        "slots": [
            {
                "datetime": slot.datetime.strftime("%Y-%m-%d %H:%M"),
                "status": slot.status,
                "tarefa": slot.tarefa
            } for slot in sprint.slots
        ]
    }

def dict_to_sprint(data: dict) -> Sprint:
    data_inicio = datetime.strptime(data["data_inicio"], "%Y-%m-%d")
    sprint = Sprint(data["id"], data_inicio, data["bloco_min"])

    # Substitui as tarefas e slots gerados pelos salvos
    sprint.tarefas = [
        Task(
            nome=t["nome"],
            tempo_estimado_horas=t["tempo_estimado"],
            cor=t.get("cor", "azul")
        ) for t in data["tarefas"]
    ]
    for i, t in enumerate(data["tarefas"]):
        sprint.tarefas[i].tempo_gasto = t["tempo_gasto"]
        sprint.tarefas[i].blocos_restantes = t["blocos_restantes"]

    sprint.slots = []
    for s in data["slots"]:
        dt = datetime.strptime(s["datetime"], "%Y-%m-%d %H:%M")
        slot = Slot(dt)
        slot.status = s["status"]
        slot.tarefa = s["tarefa"]
        sprint.slots.append(slot)

    return sprint
