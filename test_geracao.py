# test_alocacao.py
from datetime import datetime
from models.sprint import Sprint
from core.task_manager import criar_tarefa, alocar_slot_manual

inicio = datetime(2025, 6, 30)
sprint = Sprint("sprint_2025-06-30", inicio)

# Cria tarefa
tarefa = criar_tarefa(sprint, "Estudar Python", 2.0, cor="verde")

# Aloca dois blocos manualmente
slots_livres = sprint.get_slots_livres()
alocar_slot_manual(sprint, "Estudar Python", slots_livres[0].datetime)
alocar_slot_manual(sprint, "Estudar Python", slots_livres[1].datetime)

print(f"Tarefa: {tarefa.nome}")
print(f"Tempo estimado: {tarefa.tempo_estimado} h")
print(f"Tempo gasto: {tarefa.tempo_gasto:.2f} h")
print(f"Blocos restantes: {tarefa.blocos_restantes}")
