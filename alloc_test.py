import json

import streamlit as st

st.set_page_config(page_title="allocation.json 作成ツール", layout="wide")
st.title("採点用 allocation.json 作成アプリ")

st.markdown("### 設問構成を入力してください")

allocation = {}


def input_problem(level=1, prefix=""):
    max_items = 20
    items = {}
    count = st.number_input(
        f"{prefix} に含める項目数（最大{max_items}）", min_value=0, max_value=max_items, key=f"count_{prefix}"
    )

    for i in range(1, count + 1):
        sub_key = st.text_input(f"{prefix} の項目{i}のラベル", key=f"{prefix}_label_{i}")
        if not sub_key:
            continue

        if level < 3:
            nested = st.checkbox(f"{prefix} の項目{sub_key} に下位項目を追加", key=f"{prefix}_nested_{i}")
            if nested:
                with st.container():
                    st.markdown(f"##### {prefix} > {sub_key} の下位項目")
                    items[sub_key] = input_problem(level + 1, prefix + sub_key)
                    continue

        q_type = st.selectbox(
            f"{prefix} の項目{sub_key} の採点方法", ["full-or-zero", "partial"], key=f"{prefix}_type_{i}"
        )
        score = st.number_input(f"{prefix} の項目{sub_key} の配点", min_value=0, key=f"{prefix}_score_{i}")
        items[sub_key] = {"type": q_type, "score": score}
    return items


num_questions = st.number_input("設問数（例：問1, 問2 ...）", min_value=1, max_value=20)

for q_num in range(1, num_questions + 1):
    with st.container():
        st.markdown("---")
        q_label = st.text_input(f"問{q_num} のラベル（例：問1）", value=f"問{q_num}", key=f"top_label_{q_num}")
        has_subquestions = st.checkbox(f"{q_label} に小問を含める", key=f"has_sub_{q_label}")

        if has_subquestions:
            with st.container():
                st.markdown(f"#### {q_label} の小問入力")
                allocation[q_label] = input_problem(level=1, prefix=q_label)
        else:
            q_type = st.selectbox(f"{q_label} の採点方法", ["full-or-zero", "partial"], key=f"top_type_{q_label}")
            score = st.number_input(f"{q_label} の配点", min_value=0, key=f"top_score_{q_label}")
            allocation[q_label] = {"type": q_type, "score": score}

st.markdown("---")

if st.button("JSONを生成"):
    json_data = json.dumps(allocation, indent=2, ensure_ascii=False)
    st.json(json_data)
    st.download_button(
        "allocation.json をダウンロード", json_data, file_name="allocation.json", mime="application/json"
    )
