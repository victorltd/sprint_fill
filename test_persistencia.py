# test_persistencia.py

from datetime import datetime
from models.sprint import Sprint
from core.task_manager import criar_tarefa, alocar_slot_manual
from storage.file_store import salvar_sprint, carregar_sprint

# Criar sprint e alocar tarefa
inicio = datetime(2025, 6, 30)
sprint = Sprint("sprint_2025-06-30", inicio)
tarefa = criar_tarefa(sprint, "Planejar conteúdo", 1.0, cor="roxo")

slot = sprint.get_slots_livres()[0]
alocar_slot_manual(sprint, tarefa.nome, slot.datetime)

# Salvar no arquivo
salvar_sprint(sprint)

# Carregar e mostrar
sprint_carregada = carregar_sprint("sprint_2025-06-30")
print(f"Sprint carregada: {sprint_carregada.id}")
print(f"Tarefa: {sprint_carregada.tarefas[0].nome}")
print(f"Slots ocupados: {[s.datetime.strftime('%H:%M') for s in sprint_carregada.slots if s.status == 'ocupado']}")
