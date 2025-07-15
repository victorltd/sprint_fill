# models/sprint.py

from datetime import datetime, timedelta, time
from models.utils import gerar_slots_uteis

class Slot:
    def __init__(self, dt: datetime):
        self.datetime = dt
        self.status = "livre"
        self.tarefa = None

    def ocupar(self, nome_tarefa: str):
        self.status = "ocupado"
        self.tarefa = nome_tarefa

class Task:
    def __init__(self, nome: str, tempo_estimado_horas: float, cor: str = "azul"):
        self.nome = nome
        self.tempo_estimado = tempo_estimado_horas
        self.tempo_gasto = 0.0
        self.blocos_restantes = int((tempo_estimado_horas * 60) / 30)
        self.cor = cor

    def alocar_bloco(self, minutos: int):
        self.tempo_gasto += minutos / 60
        self.blocos_restantes -= 1

class Sprint:
    def __init__(self, id_sprint: str, data_inicio: datetime, bloco_min: int = 30):
        self.id = id_sprint
        self.data_inicio = data_inicio
        self.bloco_min = bloco_min
        self.slots = self._gerar_slots()
        self.tarefas = []

    def _gerar_slots(self):
        return [Slot(dt) for dt in gerar_slots_uteis(self.data_inicio, self.bloco_min)]

    def adicionar_tarefa(self, task: Task):
        self.tarefas.append(task)

    def get_slots_por_tarefa(self, tarefa_nome: str):
        return [slot for slot in self.slots if slot.tarefa == tarefa_nome]

    def get_slots_livres(self):
        return [slot for slot in self.slots if slot.status == "livre"]
   
