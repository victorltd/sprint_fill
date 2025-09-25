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


# # ----------- AUTENTICAÇÃO -----------
# if not check_auth():
#     login()
#     st.stop()

# user = get_current_user()
# st.sidebar.success(f"Logado como: {user.email}")
# if st.sidebar.button("🚪 Logout"):
#     logout()


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
    # --- Integração com PI Planning ---
    # Carrega os PIs e tasks do PI
    import json
    PI_DATA_PATH = "pages\pi_data.json"    
    if os.path.exists(PI_DATA_PATH):        
        with open(PI_DATA_PATH, "r", encoding="utf-8") as f:            
            try:                
                pi_data = json.load(f)            
            except Exception:                
                pi_data = {"pis": []}    
    else:        
        pi_data = {"pis": []}    

    if not pi_data["pis"]:
        st.sidebar.info("Nenhum PI cadastrado. Cadastre um PI na página de PI Planning.")
    else:
        pi_options = [f"{pi['nome']} ({pi['id']})" for pi in pi_data["pis"]]
        with st.sidebar.form("nova_sprint_form_sidebar"):
            data_inicio = st.date_input("Data de início", value=datetime.today())
            bloco_min = st.number_input("Duração do bloco (min)", min_value=15, max_value=120, value=30, step=15)
            sprint_id = f"sprint_{data_inicio.strftime('%Y-%m-%d')}"
            pi_idx = st.selectbox("Selecionar PI para importar tasks", ["Nenhum"] + pi_options)
            st.form_submit_button("Avançar")

        # Exibe a tabela de seleção de tasks na tela principal
        if pi_idx != "Nenhum":
            pi_index = pi_options.index(pi_idx)
            pi_sel = pi_data["pis"][pi_index]
            pi_tasks = []
            for epic in pi_sel["epics"]:
                for feat in epic["features"]:
                    for t in feat["tasks"]:
                        pi_tasks.append({
                            "nome": t["nome"],
                            "estimativa": t.get("estimativa_horas", 1.0),
                            "cor": "#1f77b4",
                            "epic": epic["nome"],
                            "feature": feat["nome"]
                        })
            if pi_tasks:
                st.markdown("### Seleção de Tasks do PI")
                import pandas as pd
                import io
                import csv
                # Inicializa tabela editável na sessão
                if "pi_task_table" not in st.session_state:
                    st.session_state.pi_task_table = pd.DataFrame([
                        {"Task": t["nome"], "Feature": t["feature"], "Epic": t["epic"], "Horas": float(t["estimativa"]), "Selecionar": False}
                        for t in pi_tasks
                    ])
                # Renderiza tabela editável com st.data_editor
                edited_df = st.data_editor(
                    st.session_state.pi_task_table,
                    column_config={
                        "Task": "Task",
                        "Feature": "Feature",
                        "Epic": "Epic",
                        "Horas": st.column_config.NumberColumn("Horas", min_value=0.5, step=0.5, format="%.2f"),
                        "Selecionar": st.column_config.CheckboxColumn("Selecionar")
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="pi_task_table_editor"
                )
                # Soma instantânea
                soma_horas = edited_df.loc[edited_df["Selecionar"], "Horas"].sum()
                st.markdown(f"<div style='background:#e3f2fd;padding:10px 20px;border-radius:8px;font-size:20px;font-weight:bold;color:#1565c0;margin-bottom:10px'>Total de horas das tasks selecionadas: {soma_horas:.2f}h</div>", unsafe_allow_html=True)

                # Botão para exportar CSV Azure DevOps
                selected_tasks = edited_df[edited_df["Selecionar"]]
                if not selected_tasks.empty:
                    csv_buffer = io.StringIO()
                    writer = csv.writer(csv_buffer)
                    writer.writerow([
                        "Work Item Type", "Title", "Feature", "Epic", "Estimated Hours", "State", "Priority", "Tags"
                    ])
                    for _, row in selected_tasks.iterrows():
                        writer.writerow([
                            "Task",
                            row["Task"],
                            row["Feature"],
                            row["Epic"],
                            row["Horas"],
                            "To Do",
                            2,
                            ""
                        ])
                    st.download_button(
                        label="Exportar tasks para Azure DevOps (CSV)",
                        data=csv_buffer.getvalue().encode("utf-8"),
                        file_name=f"tasks_sprint_{sprint_id}.csv",
                        mime="text/csv"
                    )

                # Botão para criar sprint
                if st.button("Criar Sprint com tasks selecionadas"):
                    sprint = Sprint(sprint_id, datetime.combine(data_inicio, datetime.min.time()), bloco_min)
                    for _, t in edited_df.iterrows():
                        if t["Selecionar"]:
                            criar_tarefa(sprint, t["Task"], t["Horas"], "#1f77b4")
                    salvar_sprint(sprint)
                    st.success(f"Sprint {sprint_id} criada. Recarregue a página para começar.")
                    del st.session_state.pi_task_table
                    st.rerun()
                # Atualiza sessão para manter edição
                st.session_state.pi_task_table = edited_df.copy()
            else:
                st.info("Nenhuma task cadastrada neste PI.")
else:
    sprint = carregar_sprint(opcao)
    st.sidebar.success(f"Sprint carregada: {sprint.id}")

    # --- Importar tasks do PI após criar sprint ---
    if st.sidebar.button("Importar tasks do PI nesta Sprint"):
        st.session_state.show_import_pi_tasks = True

    if st.session_state.get("show_import_pi_tasks"):
        st.markdown("### Importar tasks do PI para esta Sprint")
        import json
        PI_DATA_PATH = "pages\pi_data.json"
        if os.path.exists(PI_DATA_PATH):
            with open(PI_DATA_PATH, "r", encoding="utf-8") as f:
                try:
                    pi_data = json.load(f)
                except Exception:
                    pi_data = {"pis": []}
        else:
            pi_data = {"pis": []}

        if not pi_data["pis"]:
            st.info("Nenhum PI cadastrado. Cadastre um PI na página de PI Planning.")
        else:
            pi_options = [f"{pi['nome']} ({pi['id']})" for pi in pi_data["pis"]]
            pi_idx = st.selectbox("Selecionar PI para importar tasks", ["Nenhum"] + pi_options, key="import_pi_select")
            if pi_idx != "Nenhum":
                pi_index = pi_options.index(pi_idx)
                pi_sel = pi_data["pis"][pi_index]
                # Tasks já existentes na sprint
                nomes_existentes = set(t.nome for t in sprint.tarefas)
                pi_tasks = []
                for epic in pi_sel["epics"]:
                    for feat in epic["features"]:
                        for t in feat["tasks"]:
                            if t["nome"] not in nomes_existentes:
                                pi_tasks.append({
                                    "nome": t["nome"],
                                    "estimativa": t.get("estimativa_horas", 1.0),
                                    "cor": "#1f77b4",
                                    "epic": epic["nome"],
                                    "feature": feat["nome"]
                                })
                if pi_tasks:
                    import pandas as pd
                    if "import_pi_task_table" not in st.session_state:
                        st.session_state.import_pi_task_table = pd.DataFrame([
                            {"Task": t["nome"], "Feature": t["feature"], "Horas": float(t["estimativa"]), "Selecionar": False}
                            for t in pi_tasks
                        ])
                    edited_df = st.data_editor(
                        st.session_state.import_pi_task_table,
                        column_config={
                            "Task": "Task",
                            "Feature": "Feature",
                            "Horas": st.column_config.NumberColumn("Horas", min_value=0.5, step=0.5, format="%.2f"),
                            "Selecionar": st.column_config.CheckboxColumn("Selecionar")
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="import_pi_task_table_editor"
                    )
                    soma_horas = edited_df.loc[edited_df["Selecionar"], "Horas"].sum()
                    st.markdown(f"<div style='background:#e3f2fd;padding:10px 20px;border-radius:8px;font-size:20px;font-weight:bold;color:#1565c0;margin-bottom:10px'>Total de horas das tasks selecionadas: {soma_horas:.2f}h</div>", unsafe_allow_html=True)
                    if st.button("Importar tasks selecionadas nesta Sprint"):
                        for _, t in edited_df.iterrows():
                            if t["Selecionar"]:
                                criar_tarefa(sprint, t["Task"], t["Horas"], "#1f77b4")
                        salvar_sprint(sprint)
                        st.success("Tasks importadas para a sprint!")
                        del st.session_state.import_pi_task_table
                        st.session_state.show_import_pi_tasks = False
                        st.rerun()
                    st.session_state.import_pi_task_table = edited_df.copy()
                else:
                    st.info("Nenhuma task disponível para importar deste PI.")
            if st.button("Cancelar importação de tasks do PI"):
                st.session_state.show_import_pi_tasks = False

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
    # Exportar todas as tasks da sprint para Azure DevOps CSV
    import io
    import csv
    if sprint.tarefas:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow([
            "Work Item Type", "Title", "Feature", "Epic", "Estimated Hours", "State", "Priority", "Tags"
        ])
        for t in sprint.tarefas:
            # Tenta buscar feature/epic se existirem como atributos, senão deixa vazio
            feature = getattr(t, 'feature', getattr(t, 'Feature', '')) if hasattr(t, 'feature') or hasattr(t, 'Feature') else ''
            epic = getattr(t, 'epic', getattr(t, 'Epic', '')) if hasattr(t, 'epic') or hasattr(t, 'Epic') else ''
            writer.writerow([
                "Task",
                t.nome,
                feature,
                epic,
                getattr(t, 'tempo_estimado', ''),
                "To Do",
                2,
                ""
            ])
        st.download_button(
            label="Exportar todas as tasks da Sprint (CSV Azure DevOps)",
            data=csv_buffer.getvalue().encode("utf-8"),
            file_name=f"tasks_{sprint.id}.csv",
            mime="text/csv"
        )
    # Código para mostrar o formulário de adicionar tarefa
    # Exemplo:
    # mostrar_formulario_adicionar_tarefa()
    pass
# Fora desse bloco, nada é exibido na parte central

# ----------- LISTAGEM DE TAREFAS E SLOTS LIVRES -----------
if 'sprint' in locals():
    st.subheader("📋 Tarefas cadastradas e alocação")

    with st.expander("📋 Tarefas cadastradas e alocação"):
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
    from collections import defaultdict

    pdf = FPDF()
    pdf.add_page()
    # Logo (opcional)
    # pdf.image("logo.png", x=10, y=8, w=33)
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(30, 77, 147)
    pdf.cell(0, 12, f"Relatório da Sprint: {sprint.id}", ln=True, align="C")
    pdf.set_draw_color(30, 77, 147)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Data de início: {sprint.data_inicio.strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(0, 8, f"Duração do bloco: {sprint.bloco_min} min", ln=True)
    pdf.cell(0, 8, f"Total de tarefas: {len(sprint.tarefas)}", ln=True)
    pdf.ln(4)

    # Tarefas
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(220, 230, 241)
    pdf.cell(0, 10, "Tarefas", ln=True, fill=True)
    pdf.set_font("Arial", "", 12)
    for t in sprint.tarefas:
        pdf.cell(0, 8, f"- {t.nome} | Estimado: {t.tempo_estimado}h | Gasto: {t.tempo_gasto:.1f}h | Restante: {t.blocos_restantes * (sprint.bloco_min / 60):.1f}h", ln=True)
    pdf.ln(2)

    # Slots ocupados
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(220, 241, 220)
    pdf.cell(0, 10, "Slots Ocupados", ln=True, fill=True)
    pdf.set_font("Arial", "", 12)
    for s in sprint.slots:
        if s.status == "ocupado":
            pdf.cell(0, 8, f"{s.datetime.strftime('%Y-%m-%d %H:%M')} -> {s.tarefa}", ln=True)
    pdf.ln(2)

    # Reports diários
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(241, 241, 220)
    pdf.cell(0, 10, "Reports Diários", ln=True, fill=True)
    pdf.set_font("Arial", "", 12)
    for dia, tarefas in sprint.daily_reports.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Dia: {dia}", ln=True)
        pdf.set_font("Arial", "", 12)
        for tarefa_nome, texto in tarefas.items():
            pdf.multi_cell(0, 8, f"  {tarefa_nome}: {texto}")
        pdf.ln(1)
    pdf.ln(2)

    # Resumo diário de tarefas realizadas
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(230, 220, 241)
    pdf.cell(0, 10, "Resumo Diário de Tarefas Realizadas", ln=True, fill=True)
    pdf.set_font("Arial", "", 12)
    from collections import defaultdict
    slots_por_dia = defaultdict(list)
    for slot in sprint.slots:
        if slot.status == "ocupado":
            dia = slot.datetime.strftime("%Y-%m-%d")
            slots_por_dia[dia].append(slot)
    for dia in sorted(slots_por_dia.keys()):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Dia: {dia}", ln=True)
        pdf.set_font("Arial", "", 12)
        blocos_por_tarefa = defaultdict(int)
        for slot in slots_por_dia[dia]:
            blocos_por_tarefa[slot.tarefa] += 1
        for tarefa_nome, blocos in blocos_por_tarefa.items():
            horas = blocos * (sprint.bloco_min / 60)
            pdf.cell(0, 8, f"  {tarefa_nome}: {blocos} blocos ({horas:.2f}h)", ln=True)
        pdf.ln(1)

    # --- Visualização estilo calendário (blocos por dia/horário) ---
    from collections import defaultdict
    slots_por_dia = defaultdict(list)
    for slot in sprint.slots:
        dia = slot.datetime.strftime("%Y-%m-%d")
        slots_por_dia[dia].append(slot)

    dias_ordenados = sorted(slots_por_dia.keys())
    horas_padrao = [f"{h:02d}:{m:02d}" for h in range(7, 18) for m in (30, 0)]  # 7:30 até 17:30

    # Divide os dias em blocos de 5
    blocos_dias = [dias_ordenados[i:i+5] for i in range(0, len(dias_ordenados), 5)]

    for idx, dias_bloco in enumerate(blocos_dias):
        if idx > 0:
            pdf.add_page()
        pdf.set_font("Arial", "B", 13)
        pdf.set_fill_color(220, 230, 241)
        pdf.cell(0, 10, f"Calendário de Blocos ({idx*5+1} a {idx*5+len(dias_bloco)})", ln=True, fill=True)
        pdf.set_font("Arial", "", 9)

        # Cabeçalho da tabela
        pdf.set_fill_color(200, 200, 220)
        pdf.cell(20, 8, "Hora", 1, 0, "C", 1)
        for dia in dias_bloco:
            pdf.cell(30, 8, dia, 1, 0, "C", 1)
        pdf.ln()

        # Corpo da tabela
        for hora in horas_padrao:
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(20, 8, hora, 1, 0, "C", 1)
            for dia in dias_bloco:
                slot_match = next((s for s in slots_por_dia[dia] if s.datetime.strftime("%H:%M") == hora), None)
                if slot_match:
                    if slot_match.status == "ocupado":
                        tarefa_nome = slot_match.tarefa[:12]
                        pdf.set_fill_color(100, 180, 100)
                        pdf.cell(30, 8, tarefa_nome, 1, 0, "C", 1)
                    else:
                        pdf.set_fill_color(240, 240, 240)
                        pdf.cell(30, 8, "Livre", 1, 0, "C", 1)
                else:
                    pdf.cell(30, 8, "-", 1, 0, "C")
            pdf.ln()

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

if 'sprint' in locals() and sprint is not None:
    st.markdown("### 📅 Resumo diário de tarefas realizadas")
    from collections import defaultdict
    slots_por_dia = defaultdict(list)
    for slot in sprint.slots:
        if slot.status == "ocupado":
            dia = slot.datetime.strftime("%Y-%m-%d")
            slots_por_dia[dia].append(slot)

    for dia in sorted(slots_por_dia.keys()):
        st.markdown(f"**Dia: {dia}**")
        blocos_por_tarefa = defaultdict(int)
        for slot in slots_por_dia[dia]:
            blocos_por_tarefa[slot.tarefa] += 1
        for tarefa_nome, blocos in blocos_por_tarefa.items():
            horas = blocos * (sprint.bloco_min / 60)
            st.markdown(f"- {tarefa_nome}: {blocos} blocos ({horas:.2f}h)")
        st.markdown("---")
