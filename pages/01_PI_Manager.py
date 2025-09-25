import streamlit as st
import json
import os
from uuid import uuid4

DATA_PATH = "pi_data.json"

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"epics": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

st.title("Gerenciador de PI (Program Increment)")

menu = st.sidebar.radio("Menu", ["Criar Epic", "Criar Task", "Visualizar Estrutura"])
data = load_data()


if menu == "Criar Epic":
    st.header("Criar novo Epic")
    with st.form("form_epic"):
        nome = st.text_input("Nome do Epic")
        criar = st.form_submit_button("Criar Epic")
        if criar and nome.strip():
            epic_id = f"epic_{uuid4().hex[:8]}"
            novo_epic = {"id": epic_id, "nome": nome, "features": []}
            data["epics"].append(novo_epic)
            save_data(data)
            st.success(f"Epic '{nome}' criado com sucesso!")
            st.experimental_rerun()
    st.subheader("Epics existentes:")
    for epic in data["epics"]:
        st.markdown(f"- **{epic['nome']}** (ID: `{epic['id']}`)")

    st.header("Criar Feature em uma Epic")
    if not data["epics"]:
        st.info("Cadastre um Epic antes de criar Features.")
    else:
        epic_nomes = [f"{epic['nome']} ({epic['id']})" for epic in data["epics"]]
        epic_idx = st.selectbox("Selecione o Epic", range(len(data["epics"])), format_func=lambda i: epic_nomes[i])
        with st.form("form_feature"):
            nome_feat = st.text_input("Nome da Feature")
            criar_feat = st.form_submit_button("Criar Feature")
            if criar_feat and nome_feat.strip():
                feat_id = f"feature_{uuid4().hex[:8]}"
                nova_feat = {
                    "id": feat_id,
                    "nome": nome_feat,
                    "estimativa_horas": 0,
                    "pull": False,
                    "tasks": []
                }
                data["epics"][epic_idx]["features"].append(nova_feat)
                save_data(data)
                st.success(f"Feature '{nome_feat}' criada no Epic '{data['epics'][epic_idx]['nome']}'!")
                st.experimental_rerun()

elif menu == "Criar Task":
    st.header("Criar Task em uma Feature")
    if not data["epics"]:
        st.info("Cadastre um Epic antes de criar Tasks.")
    else:
        epic_nomes = [f"{epic['nome']} ({epic['id']})" for epic in data["epics"]]
        epic_idx = st.selectbox("Selecione o Epic", range(len(data["epics"])), format_func=lambda i: epic_nomes[i])
        epic = data["epics"][epic_idx]
        if not epic["features"]:
            st.info("Cadastre uma Feature neste Epic antes de criar Tasks.")
        else:
            feat_nomes = [f"{feat['nome']} ({feat['id']})" for feat in epic["features"]]
            feat_idx = st.selectbox("Selecione a Feature", range(len(epic["features"])), format_func=lambda i: feat_nomes[i])
            feature = epic["features"][feat_idx]
            with st.form("form_task"):
                nome_task = st.text_input("Nome da Task")
                tipo_task = st.selectbox("Tipo", ["produtiva", "improdutiva", "reservada"])
                estimativa_task = st.number_input("Estimativa (horas)", min_value=0.0, step=0.5)
                pull_task = st.checkbox("Pull (pode ser puxada para sprint)", value=False)
                criar_task = st.form_submit_button("Criar Task")
                if criar_task and nome_task.strip():
                    from uuid import uuid4
                    task_id = f"task_{uuid4().hex[:8]}"
                    nova_task = {
                        "id": task_id,
                        "nome": nome_task,
                        "tipo": tipo_task,
                        "estimativa_horas": estimativa_task,
                        "pull": pull_task
                    }
                    feature["tasks"].append(nova_task)
                    # Atualiza estimativa da feature
                    feature["estimativa_horas"] = sum(t["estimativa_horas"] for t in feature["tasks"])
                    save_data(data)
                    st.success(f"Task '{nome_task}' criada na Feature '{feature['nome']}'!")
                    st.experimental_rerun()
            st.subheader("Tasks existentes nesta Feature:")
            if not feature["tasks"]:
                st.write("Nenhuma task cadastrada.")
            else:
                for t in feature["tasks"]:
                    st.markdown(f"- **{t['nome']}** (ID: `{t['id']}`) | Tipo: {t['tipo']} | Estimativa: {t['estimativa_horas']}h | Pull: {t['pull']}")

elif menu == "Visualizar Estrutura":
    st.header("Estrutura de Epics")
    if not data["epics"]:
        st.info("Nenhum Epic cadastrado ainda.")
    else:
        for epic in data["epics"]:
            with st.expander(f"Epic: {epic['nome']} ({epic['id']})"):
                st.write("Features:")
                if not epic["features"]:
                    st.write("Nenhuma feature cadastrada.")
                else:
                    for feat in epic["features"]:
                        st.markdown(f"- **{feat['nome']}** (ID: `{feat['id']}`)")
