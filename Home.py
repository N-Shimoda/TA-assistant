import base64
import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# アプリケーション設定
st.set_page_config(page_title="提出物ビューア", layout="wide")


# サブディレクトリ一覧取得関数
def list_subdirs(root):
    return sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))])


# assignments 配下から課題選択（サイドバー）
def select_assignment():
    base_dir = "assignments"
    if not os.path.isdir(base_dir):
        st.error(f"'{base_dir}' ディレクトリが見つかりません。")
        st.stop()
    assignments = list_subdirs(base_dir)
    selected = st.sidebar.selectbox("課題を選択", assignments, key="assignment_select")
    return os.path.join(base_dir, selected)


# 画面上部で学生選択・ナビゲーション
def select_student_ui(students):
    if "student_index" not in st.session_state:
        st.session_state.student_index = 0

    sel = st.selectbox(
        "学生を選択",
        students,
        index=st.session_state.student_index,
        key="student_select",
        format_func=lambda x: x.split("(")[0],
    )

    if sel != students[st.session_state.student_index]:
        st.session_state.student_index = students.index(sel)

    return students[st.session_state.student_index]


# allocation.json 読み込み
def load_allocation(path):
    alloc_file = os.path.join(path, "allocation.json")
    if os.path.isfile(alloc_file):
        with open(alloc_file, encoding="utf-8") as f:
            return json.load(f)
    return {}


# メイン実行
def main():
    # 課題フォルダ選択
    root_dir = select_assignment()
    # 配点定義読み込み
    allocation = load_allocation(root_dir)
    # 学生リスト取得
    students = list_subdirs(root_dir)
    selected_student = select_student_ui(students)
    student_dir = os.path.join(root_dir, selected_student)

    # 提出テキストとPDF検出
    submission_html = list(Path(student_dir).glob("*_submissionText.html"))
    attachments_dir = os.path.join(student_dir, "提出物の添付ファイル")
    attachments = os.listdir(attachments_dir) if os.path.isdir(attachments_dir) else []
    pdfs = [f for f in attachments if Path(f).suffix.lower() == ".pdf"]

    # レイアウト: メイン領域と採点領域の2カラム
    col_main, col_grade = st.columns([3, 1], border=True)

    # メイン領域: 提出テキスト／PDF表示タブ
    with col_main:
        tab_labels = ["添付ファイル", "提出テキスト"] if pdfs else ["提出テキスト"]
        tabs = st.tabs(tab_labels)
        for label, tab in zip(tab_labels, tabs):
            with tab:
                if label == "提出テキスト":
                    html_path = submission_html[0]
                    html_content = Path(html_path).read_text(encoding="utf-8")
                    components.html(html_content, height=600, scrolling=True)
                else:
                    fname = pdfs[0]
                    file_path = os.path.join(attachments_dir, fname)
                    with open(file_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    iframe = f'<iframe src="data:application/pdf;base64,{b64}" width=100% height=800></iframe>'
                    st.subheader(fname)
                    st.markdown(iframe, unsafe_allow_html=True)

    # 採点領域: 採点タブと結果保存
    with col_grade:
        tabs = st.tabs(["採点結果"])
        with tabs[0]:
            # 問題ラベルをキーにスコアを保持
            scores = {}

            def render_inputs(prefix, alloc):
                # リーフノード判定: allocにscore,typeがある場合
                if isinstance(alloc, dict) and "score" in alloc and "type" in alloc:
                    max_score = int(alloc["score"])
                    widget_key = f"{selected_student}_{prefix}".replace(" ", "_")
                    label = prefix
                    if alloc["type"] == "partial":
                        val = st.number_input(label, min_value=0, max_value=max_score, step=1, key=widget_key)
                    else:  # full-or-zero
                        checked = st.checkbox(label, key=widget_key)
                        val = max_score if checked else 0
                    # 保存用のキーは問題ラベルのみ
                    scores[prefix] = val
                elif isinstance(alloc, dict):
                    for key, val in alloc.items():
                        new_prefix = f"{prefix}_{key}" if prefix else key
                        render_inputs(new_prefix, val)

            # 配点定義に基づきウィジェット生成
            for q_key, q_val in allocation.items():
                render_inputs(q_key, q_val)

            # 合計計算
            total = sum(scores.values())
            st.markdown(f"**合計得点: {total} 点**")

            # 保存ボタン
            if st.button("保存", key="save_button"):
                grades_file = os.path.join(root_dir, "detailed_grades.json")
                try:
                    with open(grades_file, encoding="utf-8") as gf:
                        all_grades = json.load(gf)
                except FileNotFoundError:
                    all_grades = {}
                # 学生別に保存。キーは学生名、値は問題ラベル=>スコア辞書
                all_grades[selected_student] = scores
                with open(grades_file, "w", encoding="utf-8") as gf:
                    json.dump(all_grades, gf, ensure_ascii=False, indent=2)
                st.success(f"採点結果を '{grades_file}' に保存しました。")


if __name__ == "__main__":
    main()
