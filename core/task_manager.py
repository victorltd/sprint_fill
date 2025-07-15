# core/task_manager.py

from models.sprint import Task, Slot, Sprint
from datetime import datetime

def criar_tarefa(sprint: Sprint, nome: str, tempo_estimado_horas: float, cor: str = "azul"):
    nova_task = Task(nome, tempo_estimado_horas, cor)
    sprint.adicionar_tarefa(nova_task)
    return nova_task

def alocar_slot_manual(sprint: Sprint, tarefa_nome: str, datetime_slot: datetime):
    tarefa = next((t for t in sprint.tarefas if t.nome == tarefa_nome), None)
    if not tarefa:
        raise ValueError(f"Tarefa '{tarefa_nome}' não encontrada na sprint.")

    slot = next((s for s in sprint.slots if s.datetime == datetime_slot), None)
    if not slot:
        raise ValueError(f"Slot {datetime_slot} não encontrado.")
    if slot.status == "ocupado":
        raise ValueError(f"Slot {datetime_slot} já está ocupado.")

    slot.ocupar(tarefa_nome)
    tarefa.alocar_bloco(sprint.bloco_min)
