# models/utils.py

from datetime import datetime, timedelta, time

def gerar_slots_uteis(data_inicio: datetime, bloco_min: int):
    slots = []
    dias_da_sprint = 10  # 10 dias úteis (2 semanas)
    dias_adicionados = 0
    dia_corrente = data_inicio

    while dias_adicionados < dias_da_sprint:
        if dia_corrente.weekday() < 5:  # 0 = segunda, 4 = sexta
            if dia_corrente.weekday() < 4:
                hora_fim = time(17, 30)
            else:
                hora_fim = time(16, 30)
            hora_ini = time(7, 30)

            dt_inicio = datetime.combine(dia_corrente.date(), hora_ini)
            dt_fim = datetime.combine(dia_corrente.date(), hora_fim)
            dt_slot = dt_inicio

            while dt_slot + timedelta(minutes=bloco_min) <= dt_fim:
                slots.append(dt_slot)
                dt_slot += timedelta(minutes=bloco_min)

            dias_adicionados += 1
        dia_corrente += timedelta(days=1)

    return slots
