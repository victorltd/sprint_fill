import streamlit as st
import os
import json
from uuid import uuid4

DATA_PATH = "pages\pi_data.json"

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"pis": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

st.title("PI Planning - Gerenciador de Program Increment")

menu = st.sidebar.radio(
    "Menu",
    ["Criar PI", "PIs", "Epics", "Features", "Tasks", "Visualizar Estrutura"]
)
data = load_data()

if menu == "PIs":
    st.header("Program Increments (PIs)")
    if 'show_add_pi' not in st.session_state:
        st.session_state['show_add_pi'] = False
    if st.button("➕ Adicionar PI"):
        st.session_state['show_add_pi'] = not st.session_state['show_add_pi']
    if st.session_state['show_add_pi']:
        with st.form("form_add_pi", clear_on_submit=True):
            nome = st.text_input("Nome do PI")
            capacidade = st.number_input("Capacidade total de horas do PI", min_value=1.0, step=1.0, value=40.0)
            data_inicio = st.date_input("Data de início do PI")
            data_fim = st.date_input("Data de fim do PI")
            criar = st.form_submit_button("Criar PI")
            if criar and nome.strip():
                pi_id = f"pi_{uuid4().hex[:8]}"
                novo_pi = {
                    "id": pi_id,
                    "nome": nome,
                    "capacidade_horas": capacidade,
                    "data_inicio": str(data_inicio),
                    "data_fim": str(data_fim),
                    "epics": []
                }
                data["pis"].append(novo_pi)
                save_data(data)
                st.success(f"PI '{nome}' criado com sucesso!")
                st.session_state['show_add_pi'] = False
                st.experimental_rerun()
    if not data["pis"]:
        st.info("Nenhum PI cadastrado ainda.")
    else:
        for idx, pi in enumerate(data["pis"]):
            col1, col2, col3 = st.columns([6,1,1])
            with col1:
                st.markdown(f"🟦 <b>{pi['nome']}</b> <span style='color:#888'>(ID: {pi['id']})</span> - <span style='color:#555'>{pi.get('capacidade_horas','-')}h</span>", unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key=f"edit_pi_{pi['id']}"):
                    st.session_state['edit_pi'] = idx
            with col3:
                if st.button("🗑️", key=f"del_pi_{pi['id']}"):
                    data["pis"].pop(idx)
                    save_data(data)
                    st.experimental_rerun()
        # Formulário de edição de PI
        edit_pi = st.session_state.get('edit_pi')
        if edit_pi is not None and 0 <= edit_pi < len(data["pis"]):
            pi = data["pis"][edit_pi]
            from datetime import date
            with st.form(f"edit_pi_form_{pi['id']}"):
                nome_pi = st.text_input("Nome do PI", value=pi['nome'])
                capacidade_pi = st.number_input("Capacidade total de horas do PI", min_value=1.0, step=1.0, value=float(pi.get('capacidade_horas', 40.0)))
                data_inicio = st.date_input("Data de início do PI", value=date.fromisoformat(pi.get('data_inicio', str(date.today()))))
                data_fim = st.date_input("Data de fim do PI", value=date.fromisoformat(pi.get('data_fim', str(date.today()))))
                salvar = st.form_submit_button("Salvar Alterações")
                if salvar:
                    pi['nome'] = nome_pi
                    pi['capacidade_horas'] = capacidade_pi
                    pi['data_inicio'] = str(data_inicio)
                    pi['data_fim'] = str(data_fim)
                    save_data(data)
                    st.session_state.pop('edit_pi')
                    st.success("PI editado com sucesso!")
                    st.experimental_rerun()

if menu == "Criar PI":
    # ...código de criação de PI...
    st.header("Criar novo PI")
    with st.form("form_pi"):
        nome = st.text_input("Nome do PI")
        capacidade = st.number_input("Capacidade total de horas do PI", min_value=1.0, step=1.0, value=40.0)
        criar = st.form_submit_button("Criar PI")
        if criar and nome.strip():
            pi_id = f"pi_{uuid4().hex[:8]}"
            novo_pi = {"id": pi_id, "nome": nome, "capacidade_horas": capacidade, "epics": []}
            data["pis"].append(novo_pi)
            save_data(data)
            st.success(f"PI '{nome}' criado com sucesso!")
            st.experimental_rerun()

elif menu == "Epics":
    st.header("Epics em PIs")
    if not data["pis"]:
        st.info("Cadastre um PI antes de gerenciar Epics.")
    else:
        pi_nomes = [f"{pi['nome']} ({pi['id']})" for pi in data["pis"]]
        pi_idx = st.selectbox("Selecione o PI", range(len(data["pis"])), format_func=lambda i: pi_nomes[i])
        pi = data["pis"][pi_idx]
        if 'show_add_epic' not in st.session_state:
            st.session_state['show_add_epic'] = False
        if st.button("➕ Adicionar Epic"):
            st.session_state['show_add_epic'] = not st.session_state['show_add_epic']
        if st.session_state['show_add_epic']:
            with st.form("form_add_epic", clear_on_submit=True):
                nome_epic = st.text_input("Nome do Epic")
                criar_epic = st.form_submit_button("Adicionar Epic")
                if criar_epic and nome_epic.strip():
                    epic_id = f"epic_{uuid4().hex[:8]}"
                    novo_epic = {"id": epic_id, "nome": nome_epic, "features": []}
                    pi["epics"].append(novo_epic)
                    save_data(data)
                    st.success(f"Epic '{nome_epic}' criado!")
                    st.session_state['show_add_epic'] = False
                    st.experimental_rerun()
        st.subheader("Epics deste PI:")
        for idx, epic in enumerate(pi["epics"]):
            col1, col2, col3 = st.columns([6,1,1])
            with col1:
                st.markdown(f"🟩 <b>{epic['nome']}</b> <span style='color:#888'>(ID: {epic['id']})</span>", unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key=f"edit_epic_{epic['id']}"):
                    st.session_state['edit_epic'] = {'pi_idx': pi_idx, 'epic_idx': idx}
            with col3:
                if st.button("🗑️", key=f"del_epic_{epic['id']}"):
                    pi["epics"].pop(idx)
                    save_data(data)
                    st.experimental_rerun()
        # Formulário de edição de Epic
        edit_epic = st.session_state.get('edit_epic')
        if edit_epic and edit_epic['pi_idx'] == pi_idx:
            epic = pi['epics'][edit_epic['epic_idx']]
            with st.form(f"edit_epic_form_{epic['id']}"):
                nome_epic = st.text_input("Nome do Epic", value=epic['nome'])
                salvar = st.form_submit_button("Salvar Alterações")
                if salvar:
                    epic['nome'] = nome_epic
                    save_data(data)
                    st.session_state.pop('edit_epic')
                    st.success("Epic editado com sucesso!")
                    st.experimental_rerun()

elif menu == "Features":
    st.header("Features em Epics")
    if not data["pis"]:
        st.info("Cadastre um PI antes de gerenciar Features.")
    else:
        pi_nomes = [f"{pi['nome']} ({pi['id']})" for pi in data["pis"]]
        pi_idx = st.selectbox("Selecione o PI", range(len(data["pis"])), format_func=lambda i: pi_nomes[i])
        pi = data["pis"][pi_idx]
        if not pi["epics"]:
            st.info("Cadastre um Epic neste PI antes de gerenciar Features.")
        else:
            epic_nomes = [f"{epic['nome']} ({epic['id']})" for epic in pi["epics"]]
            epic_idx = st.selectbox("Selecione o Epic", range(len(pi["epics"])), format_func=lambda i: epic_nomes[i])
            epic = pi["epics"][epic_idx]
            if 'show_add_feat' not in st.session_state:
                st.session_state['show_add_feat'] = False
            if st.button("➕ Adicionar Feature"):
                st.session_state['show_add_feat'] = not st.session_state['show_add_feat']
            if st.session_state['show_add_feat']:
                with st.form("form_add_feat", clear_on_submit=True):
                    nome_feat = st.text_input("Nome da Feature")
                    estimativa_total = st.number_input("Estimativa total de horas da Feature", min_value=0.0, step=0.5, value=0.0)
                    criar_feat = st.form_submit_button("Adicionar Feature")
                    if criar_feat and nome_feat.strip():
                        feat_id = f"feature_{uuid4().hex[:8]}"
                        nova_feat = {"id": feat_id, "nome": nome_feat, "estimativa_horas_total": estimativa_total, "horas_reais": 0, "pull": False, "tasks": []}
                        epic["features"].append(nova_feat)
                        save_data(data)
                        st.success(f"Feature '{nome_feat}' criada!")
                        st.session_state['show_add_feat'] = False
                        st.experimental_rerun()
            st.subheader("Features deste Epic:")
            for idx, feat in enumerate(epic["features"]):
                # Inicializa campos se não existirem
                if 'estimativa_horas_total' not in feat:
                    feat['estimativa_horas_total'] = feat.get('estimativa_horas', 0)
                if 'horas_reais' not in feat:
                    feat['horas_reais'] = sum(t.get('estimativa_horas', 0) for t in feat.get('tasks', []))
                # Atualiza horas reais sempre
                feat['horas_reais'] = sum(t.get('estimativa_horas', 0) for t in feat.get('tasks', []))
                col1, col2, col3 = st.columns([6,1,1])
                with col1:
                    st.markdown(f"🟨 <b>{feat['nome']}</b> <span style='color:#888'>(ID: {feat['id']})</span> - <span style='color:#555'>Estimado: {feat['estimativa_horas_total']}h | Real: {feat['horas_reais']}h</span>", unsafe_allow_html=True)
                with col2:
                    if st.button("✏️", key=f"edit_feat_{feat['id']}"):
                        st.session_state['edit_feat'] = {'pi_idx': pi_idx, 'epic_idx': epic_idx, 'feat_idx': idx}
                with col3:
                    if st.button("🗑️", key=f"del_feat_{feat['id']}"):
                        epic["features"].pop(idx)
                        save_data(data)
                        st.experimental_rerun()
            # Formulário de edição de Feature
            edit_feat = st.session_state.get('edit_feat')
            if edit_feat and edit_feat['pi_idx'] == pi_idx and edit_feat['epic_idx'] == epic_idx:
                feat = epic['features'][edit_feat['feat_idx']]
                if 'estimativa_horas_total' not in feat:
                    feat['estimativa_horas_total'] = feat.get('estimativa_horas', 0)
                with st.form(f"edit_feat_form_{feat['id']}"):
                    nome_feat = st.text_input("Nome da Feature", value=feat['nome'])
                    estimativa_total = st.number_input("Estimativa total de horas da Feature", min_value=0.0, step=0.5, value=float(feat.get('estimativa_horas_total', 0)))
                    salvar = st.form_submit_button("Salvar Alterações")
                    if salvar:
                        feat['nome'] = nome_feat
                        feat['estimativa_horas_total'] = estimativa_total
                        save_data(data)
                        st.session_state.pop('edit_feat')
                        st.success("Feature editada com sucesso!")
                        st.experimental_rerun()

elif menu == "Tasks":
    st.header("Todas as Tasks do PI")
    if not data["pis"]:
        st.info("Cadastre um PI antes de visualizar Tasks.")
    else:
        pi_nomes = [f"{pi['nome']} ({pi['id']})" for pi in data["pis"]]
        pi_idx = st.selectbox("Selecione o PI", range(len(data["pis"])), format_func=lambda i: pi_nomes[i])
        pi = data["pis"][pi_idx]
        # Botão para adicionar nova Task
        if 'show_add_task' not in st.session_state:
            st.session_state['show_add_task'] = False
        if st.button("➕ Adicionar Task"):
            st.session_state['show_add_task'] = not st.session_state['show_add_task']
        if st.session_state['show_add_task']:
            # Selecionar Epic e Feature para a nova Task
            epic_options = [(e['nome'], idx) for idx, e in enumerate(pi['epics'])]
            if not epic_options:
                st.warning("Cadastre um Epic antes de adicionar Tasks.")
            else:
                epic_idx = st.selectbox("Selecione o Epic", [i for _, i in epic_options], format_func=lambda i: pi['epics'][i]['nome'])
                epic = pi['epics'][epic_idx]
                feature_options = [(f['nome'], idx) for idx, f in enumerate(epic['features'])]
                if not feature_options:
                    st.warning("Cadastre uma Feature neste Epic antes de adicionar Tasks.")
                else:
                    feat_idx = st.selectbox("Selecione a Feature", [i for _, i in feature_options], format_func=lambda i: epic['features'][i]['nome'])
                    feat = epic['features'][feat_idx]
                    with st.form("form_add_task_tasks_tab", clear_on_submit=True):
                        nome_task = st.text_input("Nome da Task")
                        tipo_task = st.selectbox("Tipo da Task", ["Dev", "QA", "Design", "Outros"])
                        produtividade = st.radio("Produtividade", ["Produtiva", "Improdutiva"], index=0, horizontal=True)
                        estimativa = st.number_input("Estimativa (horas)", min_value=0.5, step=0.5, value=1.0)
                        pull = st.checkbox("Pull?", value=False)
                        criar_task = st.form_submit_button("Adicionar Task")
                        if criar_task and nome_task.strip():
                            task_id = f"task_{uuid4().hex[:8]}"
                            nova_task = {
                                "id": task_id,
                                "nome": nome_task,
                                "tipo": tipo_task,
                                "produtividade": produtividade,
                                "estimativa_horas": estimativa,
                                "pull": pull
                            }
                            feat["tasks"].append(nova_task)
                            save_data(data)
                            st.success(f"Task '{nome_task}' adicionada à Feature '{feat['nome']}'!")
                            st.session_state['show_add_task'] = False
                            st.experimental_rerun()
        # Coletar todas as tasks do PI
        all_tasks = []
        for epic in pi["epics"]:
            for feat in epic["features"]:
                for t in feat["tasks"]:
                    all_tasks.append({
                        "Task": t["nome"],
                        "Feature": feat["nome"],
                        "Epic": epic["nome"],
                        "Tipo": t.get("tipo", "-"),
                        "Produtividade": t.get("produtividade", "-"),
                        "Estimativa (h)": t.get("estimativa_horas", "-"),
                        "Pull": "Sim" if t.get("pull") else "Não"
                    })
        if not all_tasks:
            st.info("Nenhuma Task cadastrada neste PI.")
        else:
            import pandas as pd
            df = pd.DataFrame(all_tasks)
            # Estatísticas gerais
            total_tasks = len(df)
            total_horas = df["Estimativa (h)"].sum() if not df.empty else 0
            n_prod = (df["Produtividade"] == "Produtiva").sum()
            n_improd = (df["Produtividade"] == "Improdutiva").sum()
            perc_prod = (n_prod / total_tasks * 100) if total_tasks else 0
            perc_improd = (n_improd / total_tasks * 100) if total_tasks else 0
            media_horas = df["Estimativa (h)"].mean() if not df.empty else 0
            st.markdown(f"**Total de Tasks:** {total_tasks}  ")
            st.markdown(f"**Soma de Horas:** {total_horas:.2f} h  ")
            st.markdown(f"**% Produtivas:** {perc_prod:.1f}%  ")
            st.markdown(f"**% Improdutivas:** {perc_improd:.1f}%  ")
            st.markdown(f"**Média de Horas por Task:** {media_horas:.2f} h  ")
            st.markdown("---")
            # Filtros
            search_col, col1, col2, col3, col4 = st.columns([2,2,2,2,2])
            with search_col:
                search_text = st.text_input("Buscar por nome ou string", "")
            with col1:
                epic_filter = st.selectbox("Filtrar por Epic", ["Todos"] + sorted(df["Epic"].unique().tolist()))
            with col2:
                feature_filter = st.selectbox("Filtrar por Feature", ["Todos"] + sorted(df["Feature"].unique().tolist()))
            with col3:
                tipo_filter = st.selectbox("Filtrar por Tipo", ["Todos"] + sorted(df["Tipo"].unique().tolist()))
            with col4:
                prod_filter = st.selectbox("Filtrar por Produtividade", ["Todos"] + sorted(df["Produtividade"].unique().tolist()))

            df_filtered = df.copy()
            if search_text.strip():
                df_filtered = df_filtered[df_filtered["Task"].str.contains(search_text, case=False, na=False)]
            if epic_filter != "Todos":
                df_filtered = df_filtered[df_filtered["Epic"] == epic_filter]
            if feature_filter != "Todos":
                df_filtered = df_filtered[df_filtered["Feature"] == feature_filter]
            if tipo_filter != "Todos":
                df_filtered = df_filtered[df_filtered["Tipo"] == tipo_filter]
            if prod_filter != "Todos":
                df_filtered = df_filtered[df_filtered["Produtividade"] == prod_filter]

            st.dataframe(df_filtered, use_container_width=True)

elif menu == "Visualizar Estrutura":
    st.header("Estrutura de PIs")
    if not data["pis"]:
        st.info("Nenhum PI cadastrado ainda.")
    else:
        import streamlit as st
        import pandas as pd
        import plotly.express as px
        for pi in data["pis"]:
            with st.expander(f"🟦 PI: {pi['nome']} ({pi['id']})"):
                st.markdown(f"<b>Capacidade total de horas:</b> {pi.get('capacidade_horas','-')}h", unsafe_allow_html=True)
                # Estatísticas de produtividade do PI
                tasks_pi = []
                for epic in pi["epics"]:
                    for feat in epic["features"]:
                        for t in feat["tasks"]:
                            tasks_pi.append(t)
                capacidade = float(pi.get('capacidade_horas', 0))
                horas_alocadas = 0.0
                horas_prod = {"Produtiva": 0.0, "Improdutiva": 0.0}
                for t in tasks_pi:
                    horas_alocadas += float(t.get("estimativa_horas", 0))
                    key = t.get("produtividade", "Produtiva")
                    if key in horas_prod:
                        horas_prod[key] += float(t.get("estimativa_horas", 0))
                    else:
                        horas_prod[key] = float(t.get("estimativa_horas", 0))
                horas_reservadas = max(0.0, capacidade - horas_alocadas)
                graf_labels = list(horas_prod.keys()) + (["Capacidade Reservada"] if capacidade > 0 else [])
                graf_values = list(horas_prod.values()) + ([horas_reservadas] if capacidade > 0 else [])
                graf_colors = ["#2ecc40" if l=="Produtiva" else ("#ff4136" if l=="Improdutiva" else "#888") for l in graf_labels]
                if capacidade > 0:
                    fig = px.pie(
                        names=graf_labels,
                        values=graf_values,
                        color=graf_labels,
                        color_discrete_map={"Produtiva": "#2ecc40", "Improdutiva": "#ff4136", "Capacidade Reservada": "#888"},
                        title="Distribuição de Horas do PI",
                        hole=0.3
                    )
                    fig.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                if not pi["epics"]:
                    st.info("Nenhum Epic neste PI.")
                for epic in pi["epics"]:
                    st.markdown(f"<div style='margin-left:20px'><b>🟩 Epic:</b> {epic['nome']} <span style='color:#888'>(ID: {epic['id']})</span></div>", unsafe_allow_html=True)
                    if not epic["features"]:
                        st.markdown("<div style='margin-left:40px;color:#888'>Nenhuma Feature neste Epic.</div>", unsafe_allow_html=True)
                    for feat in epic["features"]:
                        # Inicializa campos se não existirem
                        if 'estimativa_horas_total' not in feat:
                            feat['estimativa_horas_total'] = feat.get('estimativa_horas', 0)
                        if 'horas_reais' not in feat:
                            feat['horas_reais'] = sum(t.get('estimativa_horas', 0) for t in feat.get('tasks', []))
                        # Atualiza horas reais sempre
                        feat['horas_reais'] = sum(t.get('estimativa_horas', 0) for t in feat.get('tasks', []))
                        st.markdown(f"<div style='margin-left:40px'><b>🟨 Feature:</b> {feat['nome']} <span style='color:#888'>(ID: {feat['id']})</span> - <span style='color:#555'>Estimado: {feat['estimativa_horas_total']}h | Real: {feat['horas_reais']}h</span></div>", unsafe_allow_html=True)
                        if not feat["tasks"]:
                            st.markdown("<div style='margin-left:60px;color:#888'>Nenhuma Task nesta Feature.</div>", unsafe_allow_html=True)
                        for idx, t in enumerate(feat["tasks"]):
                            cor_prod = "#2ecc40" if t.get("produtividade", "Produtiva") == "Produtiva" else "#ff4136"
                            col1, col2, col3 = st.columns([6,1,1])
                            with col1:
                                st.markdown(f"<div style='margin-left:60px'>📝 <b>Task:</b> <span style='color:{cor_prod}'>{t['nome']}</span> <span style='color:#888'>(ID: {t['id']})</span> - <b>{t['tipo']}</b>, <b>{t['estimativa_horas']}h</b>, Pull: <b>{'Sim' if t['pull'] else 'Não'}</b> | <b>Produtividade:</b> <span style='color:{cor_prod}'>{t.get('produtividade','Produtiva')}</span></div>", unsafe_allow_html=True)
                            with col2:
                                if st.button("✏️", key=f"edit_{feat['id']}_{t['id']}"):
                                    st.session_state['edit_task'] = {'pi_id': pi['id'], 'epic_id': epic['id'], 'feat_id': feat['id'], 'task_idx': idx}
                            with col3:
                                if st.button("🗑️", key=f"del_{feat['id']}_{t['id']}"):
                                    # Remover a task
                                    feat["tasks"].pop(idx)
                                    save_data(data)
                                    st.experimental_rerun()
                        # Formulário para criar nova Task nesta Feature
                        with st.form(f"form_add_task_{feat['id']}", clear_on_submit=True):
                            st.markdown(f"<div style='margin-left:60px'><b>Adicionar nova Task nesta Feature</b></div>", unsafe_allow_html=True)
                            nome_task = st.text_input("Nome da Task", key=f"nome_task_{feat['id']}")
                            tipo_task = st.selectbox("Tipo da Task", ["Dev", "QA", "Design", "Outros"], key=f"tipo_task_{feat['id']}")
                            produtividade = st.radio("Produtividade", ["Produtiva", "Improdutiva"], index=0, horizontal=True, key=f"prod_{feat['id']}")
                            estimativa = st.number_input("Estimativa (horas)", min_value=0.5, step=0.5, value=1.0, key=f"estimativa_{feat['id']}")
                            pull = st.checkbox("Pull?", value=False, key=f"pull_{feat['id']}")
                            criar_task = st.form_submit_button("Adicionar Task")
                            if criar_task and nome_task.strip():
                                task_id = f"task_{uuid4().hex[:8]}"
                                nova_task = {
                                    "id": task_id,
                                    "nome": nome_task,
                                    "tipo": tipo_task,
                                    "produtividade": produtividade,
                                    "estimativa_horas": estimativa,
                                    "pull": pull
                                }
                                feat["tasks"].append(nova_task)
                                save_data(data)
                                st.success(f"Task '{nome_task}' adicionada à Feature!")
                                st.experimental_rerun()
                        # Formulário de edição de task
                        edit_task = st.session_state.get('edit_task')
                        if edit_task and edit_task['pi_id'] == pi['id'] and edit_task['epic_id'] == epic['id'] and edit_task['feat_id'] == feat['id']:
                            t = feat['tasks'][edit_task['task_idx']]
                            with st.form(f"edit_form_{feat['id']}_{t['id']}"):
                                nome_task = st.text_input("Nome da Task", value=t['nome'])
                                tipo_task = st.selectbox("Tipo da Task", ["Dev", "QA", "Design", "Outros"], index=["Dev", "QA", "Design", "Outros"].index(t['tipo']))
                                produtividade = st.radio("Produtividade", ["Produtiva", "Improdutiva"], index=0 if t.get('produtividade','Produtiva')=="Produtiva" else 1, horizontal=True)
                                estimativa = st.number_input("Estimativa (horas)", min_value=0.5, step=0.5, value=float(t['estimativa_horas']))
                                pull = st.checkbox("Pull?", value=t['pull'])
                                salvar = st.form_submit_button("Salvar Alterações")
                                if salvar:
                                    t['nome'] = nome_task
                                    t['tipo'] = tipo_task
                                    t['produtividade'] = produtividade
                                    t['estimativa_horas'] = estimativa
                                    t['pull'] = pull
                                    # Atualiza estimativa da feature
                                    feat["estimativa_horas"] = sum(task["estimativa_horas"] for task in feat["tasks"])
                                    save_data(data)
                                    st.session_state.pop('edit_task')
                                    st.success("Task editada com sucesso!")
                                    st.experimental_rerun()
