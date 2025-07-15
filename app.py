# app.py

import streamlit as st
from datetime import datetime
from models.sprint import Sprint
from core.task_manager import criar_tarefa, alocar_slot_manual
from storage.file_store import salvar_sprint, carregar_sprint
import os

DATA_DIR = "data"

# ----------- SESSÃO -----------
st.set_page_config(page_title="Sprint Scheduler", layout="wide")
st.title("🕒 Sprint Scheduler Ágil")

# ----------- CARREGAR OU CRIAR SPRINT -----------

st.sidebar.header("Sprint")
sprint_ids = [f.replace(".json", "") for f in os.listdir(DATA_DIR) if f.endswith(".json")]

opcao = st.sidebar.selectbox("Selecione uma sprint ou crie nova", ["Nova Sprint"] + sprint_ids)

# Adicione este bloco para permitir apagar a sprint selecionada
if opcao != "Nova Sprint":
    if st.sidebar.button("🗑️ Apagar esta Sprint"):
        sprint_path = os.path.join(DATA_DIR, f"{opcao}.json")
        if os.path.exists(sprint_path):
            os.remove(sprint_path)
            st.sidebar.success(f"Sprint '{opcao}' apagada!")
            st.rerun()
        else:
            st.sidebar.error("Arquivo da sprint não encontrado.")

if opcao == "Nova Sprint":
    with st.sidebar.form("nova_sprint_form"):
        data_inicio = st.date_input("Data de início", value=datetime.today())
        bloco_min = st.number_input("Duração do bloco (min)", min_value=15, max_value=120, value=30, step=15)
        sprint_id = f"sprint_{data_inicio.strftime('%Y-%m-%d')}"
        criar_btn = st.form_submit_button("Criar Sprint")
        if criar_btn:
            sprint = Sprint(sprint_id, datetime.combine(data_inicio, datetime.min.time()), bloco_min)
            salvar_sprint(sprint)
            st.success(f"Sprint {sprint_id} criada. Recarregue a página para começar.")
            st.rerun()
else:
    sprint = carregar_sprint(opcao)
    st.sidebar.success(f"Sprint carregada: {sprint.id}")

# ----------- CADASTRO DE TAREFA -----------
st.subheader("➕ Nova Tarefa")
with st.form("form_tarefa"):
    nome = st.text_input("Nome da tarefa")
    tempo = st.number_input("Tempo estimado (horas)", min_value=0.5, step=0.5)
    cor = st.color_picker("Cor da tarefa", value="#1f77b4")
    add_task = st.form_submit_button("Adicionar")
    if add_task:
        criar_tarefa(sprint, nome, tempo, cor)
        salvar_sprint(sprint)
        st.success(f"Tarefa '{nome}' adicionada.")

# Só mostra o formulário de adicionar tarefa se a sprint existir
if 'sprint' in locals() and sprint is not None:
    # Código para mostrar o formulário de adicionar tarefa
    # Exemplo:
    # mostrar_formulario_adicionar_tarefa()
    pass
# Fora desse bloco, nada é exibido na parte central

# ----------- LISTAGEM DE TAREFAS E SLOTS LIVRES -----------
if 'sprint' in locals():
    st.subheader("📋 Tarefas e Alocação")

    if len(sprint.tarefas) == 0:
        st.info("Nenhuma tarefa cadastrada ainda.")
    else:
        for tarefa in sprint.tarefas:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.markdown(f"**{tarefa.nome}** – ⏱️ {tarefa.tempo_gasto:.1f}h de {tarefa.tempo_estimado:.1f}h")
            
            # Botão Editar
            if col2.button("✏️ Editar", key=f"edit_{tarefa.nome}"):
                with st.form(f"edit_form_{tarefa.nome}"):
                    novo_nome = st.text_input("Novo nome", value=tarefa.nome)
                    novo_tempo = st.number_input("Novo tempo estimado (horas)", min_value=0.5, step=0.5, value=tarefa.tempo_estimado)
                    nova_cor = st.color_picker("Nova cor", value=tarefa.cor)
                    submit_edit = st.form_submit_button("Salvar alterações")
                    if submit_edit:
                        tarefa.nome = novo_nome
                        tarefa.tempo_estimado = novo_tempo
                        tarefa.cor = nova_cor
                        salvar_sprint(sprint)
                        st.success("Tarefa alterada com sucesso!")
                        st.rerun()
            
            # Botão Apagar
            if col3.button("🗑️ Apagar", key=f"del_{tarefa.nome}"):
                # Libera todos os slots ocupados por essa tarefa
                for slot in sprint.slots:
                    if slot.tarefa == tarefa.nome:
                        slot.status = "livre"
                        slot.tarefa = None
                # Remove a tarefa da lista
                sprint.tarefas = [t for t in sprint.tarefas if t.nome != tarefa.nome]
                salvar_sprint(sprint)
                st.warning(f"Tarefa '{tarefa.nome}' apagada e slots liberados.")
                st.rerun()
            
            with col4:
                if tarefa.blocos_restantes > 0:
                    slots_livres = sprint.get_slots_livres()
                    opcoes = [s.datetime.strftime("%Y-%m-%d %H:%M") for s in slots_livres]
                    selecionados = st.multiselect(f"Alocar blocos para '{tarefa.nome}'", opcoes, key=tarefa.nome)

                    if st.button(f"Confirmar alocação", key="btn_"+tarefa.nome):
                        for slot_str in selecionados:
                            dt_slot = datetime.strptime(slot_str, "%Y-%m-%d %H:%M")
                            alocar_slot_manual(sprint, tarefa.nome, dt_slot)
                        salvar_sprint(sprint)
                        st.rerun()
                else:
                    st.markdown("✅ **Tarefa alocada por completo**")

        # ----------- VISÃO DOS SLOTS OCUPADOS -----------
        st.subheader("📆 Slots Alocados")
        ocupados = [s for s in sprint.slots if s.status == "ocupado"]
        livres = [s for s in sprint.slots if s.status == "livre"]

        st.markdown(f"**Total de slots ocupados:** {len(ocupados)}")
        st.markdown(f"**Slots livres restantes:** {len(livres)}")

        with st.expander("Ver todos os slots ocupados"):
            for slot in ocupados:
                col1, col2 = st.columns([4, 1])
                col1.write(f"{slot.datetime.strftime('%Y-%m-%d %H:%M')} → {slot.tarefa}")
                if col2.button("🗑️ Remover", key=f"del_slot_{slot.datetime}"):
                    # Encontra a tarefa associada ao slot
                    tarefa = next((t for t in sprint.tarefas if t.nome == slot.tarefa), None)
                    if tarefa:
                        tarefa.tempo_gasto = max(0, tarefa.tempo_gasto - (sprint.bloco_min / 60))
                    slot.status = "livre"
                    slot.tarefa = None
                    salvar_sprint(sprint)
                    st.success("Slot desalocado!")
                    st.rerun()
        with st.expander("Ver todos os slots livres"):
            for slot in livres:
                st.write(slot.datetime.strftime('%Y-%m-%d %H:%M'))

    if 'sprint' in locals() and sprint is not None:
        st.subheader("🗓️ Visualização Estilo Calendário")

        from collections import defaultdict

        # Organiza slots por dia
        slots_por_dia = defaultdict(list)
        for slot in sprint.slots:
            dia = slot.datetime.strftime("%Y-%m-%d")
            slots_por_dia[dia].append(slot)

        dias_ordenados = sorted(slots_por_dia.keys())
        horas_padrao = [f"{h:02d}:{m:02d}" for h in range(7, 18) for m in (30, 0)]  # 7:30 até 17:30

        # Tabela visual
        colunas = st.columns([1] + [1]*len(dias_ordenados))  # primeira coluna: horas

        colunas[0].markdown("**Hora**")
        for i, dia in enumerate(dias_ordenados):
            colunas[i+1].markdown(f"**{dia}**")

        for hora in horas_padrao:
            colunas = st.columns([1] + [1]*len(dias_ordenados))
            colunas[0].write(hora)
            for i, dia in enumerate(dias_ordenados):
                slot_match = next((s for s in slots_por_dia[dia] if s.datetime.strftime("%H:%M") == hora), None)
                if slot_match:
                    if slot_match.status == "ocupado":
                        cor = next((t.cor for t in sprint.tarefas if t.nome == slot_match.tarefa), "#666")
                        colunas[i+1].markdown(
                            f"<div style='background-color:{cor};padding:4px;border-radius:5px;color:white;text-align:center'>{slot_match.tarefa}</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        colunas[i+1].markdown(
                            "<div style='background-color:#ddd;padding:4px;border-radius:5px;text-align:center'>Livre</div>",
                            unsafe_allow_html=True
                        )
                else:
                    colunas[i+1].markdown("—")
