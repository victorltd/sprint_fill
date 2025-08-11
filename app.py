# app.py

import streamlit as st
from datetime import datetime
from models.sprint import Sprint
from core.task_manager import criar_tarefa, alocar_slot_manual
from storage.file_store import salvar_sprint, carregar_sprint
from storage.db_store import salvar_sprint_db, carregar_sprint_db
from core.auth import login, check_auth, get_current_user, logout
import os
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Sprint Scheduler", layout="wide")  # <-- PRIMEIRO comando Streamlit

DATA_DIR = "data"

'''
# ----------- AUTENTICAÇÃO -----------
if not check_auth():
    login()
    st.stop()

user = get_current_user()
st.sidebar.success(f"Logado como: {user.email}")
if st.sidebar.button("🚪 Logout"):
    logout()
'''

# ----------- SESSÃO -----------
#st.set_page_config(page_title="Sprint Scheduler", layout="wide")

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

            # Botão Editar ativa o modo de edição
            if col2.button("✏️ Editar", key=f"edit_{tarefa.nome}"):
                st.session_state.edit_task = tarefa.nome

            # Botão Apagar
            if col3.button("🗑️ Apagar", key=f"del_{tarefa.nome}"):
                for slot in sprint.slots:
                    if slot.tarefa == tarefa.nome:
                        slot.status = "livre"
                        slot.tarefa = None
                sprint.tarefas = [t for t in sprint.tarefas if t.nome != tarefa.nome]
                salvar_sprint(sprint)
                st.warning(f"Tarefa '{tarefa.nome}' apagada e slots liberados.")
                st.rerun()

            # Alocação de slots (igual ao seu código)
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

        # FORMULÁRIO DE EDIÇÃO FORA DO LOOP
        if "edit_task" in st.session_state:
            tarefa_edit = next((t for t in sprint.tarefas if t.nome == st.session_state.edit_task), None)
            if tarefa_edit:
                st.markdown("---")
                st.subheader(f"✏️ Editando tarefa: {tarefa_edit.nome}")
                with st.form(f"edit_form_{tarefa_edit.nome}"):
                    novo_nome = st.text_input("Novo nome", value=tarefa_edit.nome)
                    novo_tempo = st.number_input("Novo tempo estimado (horas)", min_value=0.5, step=0.5, value=tarefa_edit.tempo_estimado)
                    nova_cor = st.color_picker("Nova cor", value=tarefa_edit.cor)
                    submit_edit = st.form_submit_button("Salvar alterações")
                    cancelar = st.form_submit_button("Cancelar")
                    if submit_edit:
                        tarefa_edit.nome = novo_nome
                        tarefa_edit.tempo_estimado = novo_tempo
                        tarefa_edit.cor = nova_cor
                        # Atualize blocos_restantes se o tempo mudou
                        tarefa_edit.blocos_restantes = int((novo_tempo * 60) / sprint.bloco_min) - int(tarefa_edit.tempo_gasto / (sprint.bloco_min / 60))
                        if tarefa_edit.blocos_restantes < 0:
                            tarefa_edit.blocos_restantes = 0
                        salvar_sprint(sprint)
                        st.success("Tarefa alterada com sucesso!")
                        del st.session_state.edit_task
                        st.rerun()
                    if cancelar:
                        del st.session_state.edit_task
                        st.rerun()

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
            # Somatório de horas alocadas no dia
            horas_alocadas = sum(
                sprint.bloco_min / 60
                for slot in slots_por_dia[dia]
                if slot.status == "ocupado"
            )
            colunas[i+1].markdown(f"**{dia}**<br><span style='font-size:13px;color:#1f77b4'>Alocadas: <b>{horas_alocadas:.1f}h</b></span>", unsafe_allow_html=True)

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

if 'sprint' in locals() and sprint is not None:
    slots_restantes = len(sprint.get_slots_livres())
    duracao_total_horas = len(sprint.slots) * (sprint.bloco_min / 60)
    st.markdown(f"**Slots livres restantes:** {slots_restantes}")
    st.markdown(f"**Duração total da sprint:** {duracao_total_horas:.1f} horas")
    horas_restantes = sum(t.blocos_restantes for t in sprint.tarefas) * (sprint.bloco_min / 60)
    horas_performadas = sum(t.tempo_gasto for t in sprint.tarefas)
    st.markdown("---")
    st.markdown(f"**⏳ Horas restantes a alocar:** {horas_restantes:.1f} h")
    st.markdown(f"**✅ Horas já performadas:** {horas_performadas:.1f} h")

def gerar_relatorio_sprint(sprint):
    total_slots = len(sprint.slots)
    slots_ocupados = len([s for s in sprint.slots if s.status == "ocupado"])
    slots_livres = len([s for s in sprint.slots if s.status == "livre"])
    duracao_total_horas = total_slots * (sprint.bloco_min / 60)
    horas_performadas = sum(t.tempo_gasto for t in sprint.tarefas)
    horas_restantes = sum(t.blocos_restantes for t in sprint.tarefas) * (sprint.bloco_min / 60)
    tarefas_total = len(sprint.tarefas)
    tarefas_concluidas = len([t for t in sprint.tarefas if t.blocos_restantes == 0])
    tarefas_pendentes = tarefas_total - tarefas_concluidas

    st.header("📊 Relatório da Sprint")
    st.markdown(f"- **ID da Sprint:** `{sprint.id}`")
    st.markdown(f"- **Data de início:** `{sprint.data_inicio.strftime('%Y-%m-%d')}`")
    st.markdown(f"- **Duração total:** `{duracao_total_horas:.1f} horas`")
    st.markdown(f"- **Total de slots:** `{total_slots}`")
    st.markdown(f"- **Slots ocupados:** `{slots_ocupados}`")
    st.markdown(f"- **Slots livres:** `{slots_livres}`")
    st.markdown(f"- **Horas já performadas:** `{horas_performadas:.1f} h`")
    st.markdown(f"- **Horas restantes a alocar:** `{horas_restantes:.1f} h`")
    st.markdown(f"- **Total de tarefas:** `{tarefas_total}`")
    st.markdown(f"- **Tarefas concluídas:** `{tarefas_concluidas}`")
    st.markdown(f"- **Tarefas pendentes:** `{tarefas_pendentes}`")

    st.subheader("⏱️ Detalhes das tarefas")
    for t in sprint.tarefas:
        st.markdown(
            f"- **{t.nome}** | Estimado: `{t.tempo_estimado} h` | Gasto: `{t.tempo_gasto:.1f} h` | Restante: `{t.blocos_restantes * (sprint.bloco_min / 60):.1f} h`"
        )

def gerar_pdf_sprint(sprint):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório da Sprint: {sprint.id}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Data de início: {sprint.data_inicio.strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(0, 10, f"Duração do bloco: {sprint.bloco_min} min", ln=True)
    pdf.cell(0, 10, f"Total de tarefas: {len(sprint.tarefas)}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Tarefas:", ln=True)
    pdf.set_font("Arial", "", 12)
    for t in sprint.tarefas:
        pdf.cell(0, 8, f"- {t.nome} | Estimado: {t.tempo_estimado}h | Gasto: {t.tempo_gasto:.1f}h | Restante: {t.blocos_restantes * (sprint.bloco_min / 60):.1f}h", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Slots ocupados:", ln=True)
    pdf.set_font("Arial", "", 12)
    for s in sprint.slots:
        if s.status == "ocupado":
            pdf.cell(0, 8, f"{s.datetime.strftime('%Y-%m-%d %H:%M')} -> {s.tarefa}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Reports diários:", ln=True)
    pdf.set_font("Arial", "", 12)
    for dia, tarefas in sprint.daily_reports.items():
        pdf.cell(0, 8, f"Dia: {dia}", ln=True)
        for tarefa_nome, texto in tarefas.items():
            pdf.multi_cell(0, 8, f"  {tarefa_nome}: {texto}")
        pdf.ln(2)
    return pdf

# ...no final do app.py, após todas as visualizações...
if 'sprint' in locals() and sprint is not None:
    gerar_relatorio_sprint(sprint)

# ...depois de carregar a sprint...
if opcao != "Nova Sprint":
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Sincronizar para Supabase"):
        sprint = carregar_sprint(opcao)  # carrega do JSON local
        salvar_sprint_db(sprint)         # salva no Supabase
        st.sidebar.success("Sincronizado com Supabase!")
    if st.sidebar.button("⬇️ Atualizar localmente do Supabase"):
        sprint = carregar_sprint_db(opcao)  # carrega do Supabase
        from storage.file_store import sprint_to_dict
        with open(os.path.join(DATA_DIR, f"{opcao}.json"), "w", encoding="utf-8") as f:
            import json
            json.dump(sprint_to_dict(sprint), f, indent=2, default=str)
        st.sidebar.success("Atualizado localmente com dados do Supabase!")
        st.rerun()

    if st.button("📄 Baixar relatório em PDF"):
        pdf = gerar_pdf_sprint(sprint)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                st.download_button(
                    label="Clique aqui para baixar o PDF",
                    data=f.read(),
                    file_name=f"relatorio_{sprint.id}.pdf",
                    mime="application/pdf"
                )

if 'sprint' in locals() and sprint is not None:
    st.markdown("---")
    st.header("📝 Report Diário da Sprint")

    dias_ordenados = sorted(set(slot.datetime.strftime("%Y-%m-%d") for slot in sprint.slots))
    dia_selecionado = st.selectbox("Selecione o dia para reportar", dias_ordenados)

    # Inicializa o dict se não existir
    if not hasattr(sprint, "daily_reports"):
        sprint.daily_reports = {}

    if dia_selecionado not in sprint.daily_reports:
        sprint.daily_reports[dia_selecionado] = {}

    st.subheader(f"Report do dia {dia_selecionado}")

    # Filtra tarefas alocadas para o dia selecionado
    tarefas_alocadas = set(
        slot.tarefa for slot in sprint.slots
        if slot.status == "ocupado" and slot.datetime.strftime("%Y-%m-%d") == dia_selecionado
    )
    tarefas_alocadas = [t for t in sprint.tarefas if t.nome in tarefas_alocadas]

    if not tarefas_alocadas:
        st.info("Nenhuma tarefa alocada para este dia.")
    else:
        for tarefa in tarefas_alocadas:
            texto = sprint.daily_reports[dia_selecionado].get(tarefa.nome, "")
            with st.expander(f"Tarefa: {tarefa.nome}"):
                novo_texto = st.text_area(f"Observações para '{tarefa.nome}'", value=texto, key=f"report_{dia_selecionado}_{tarefa.nome}")
                col1, col2 = st.columns([1,1])
                if col1.button("Salvar", key=f"save_{dia_selecionado}_{tarefa.nome}"):
                    sprint.daily_reports[dia_selecionado][tarefa.nome] = novo_texto
                    salvar_sprint(sprint)
                    st.success("Report salvo!")
                if col2.button("Excluir", key=f"del_{dia_selecionado}_{tarefa.nome}"):
                    sprint.daily_reports[dia_selecionado].pop(tarefa.nome, None)
                    salvar_sprint(sprint)
                    st.warning("Report excluído!")
                    st.rerun()
