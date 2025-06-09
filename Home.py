import base64
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# アプリケーション設定
st.set_page_config(page_title="提出物ビューア", layout="wide")


# assignmentsフォルダから課題ディレクトリを選択
def list_subdirs(root):
    return sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))])


base_dir = "assignments"
if not os.path.isdir(base_dir):
    st.error(f"'{base_dir}' ディレクトリが見つかりません。")
    st.stop()

assignments = list_subdirs(base_dir)
selected_assignment = st.sidebar.selectbox("課題を選択", assignments)
root_dir = os.path.join(base_dir, selected_assignment)

# 学生ディレクトリ一覧取得
students = list_subdirs(root_dir)
selected_student = st.sidebar.selectbox("学生を選択", students)
student_dir = os.path.join(root_dir, selected_student)

# 提出ファイルと添付ファイルを検出
submission_html = list(Path(student_dir).glob("*_submissionText.html"))
attachments_dir = os.path.join(student_dir, "提出物の添付ファイル")
attachments = os.listdir(attachments_dir) if os.path.isdir(attachments_dir) else []
# PDF があるか判定
pdfs = [f for f in attachments if Path(f).suffix.lower() == ".pdf"]

# タブ設定: PDF がある場合のみ添付ファイルタブを表示
if pdfs:
    tab_labels = ["添付ファイル", "提出テキスト"]
else:
    tab_labels = ["提出テキスト"]

tabs = st.tabs(tab_labels)

for label, tab in zip(tab_labels, tabs):
    with tab:
        if label == "提出テキスト":
            st.header(f"{selected_student} の提出テキスト")
            # submissionText.html は必ず存在
            html_path = submission_html[0]
            html_content = Path(html_path).read_text(encoding="utf-8")
            components.html(html_content, height=600, scrolling=True)
        else:  # 添付ファイルタブ
            st.header(f"{selected_student} の添付ファイル")
            if pdfs:
                # 最初の PDF を埋め込み表示
                fname = pdfs[0]
                file_path = os.path.join(attachments_dir, fname)
                with open(file_path, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width=100% height=800></iframe>'
                st.subheader(fname)
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.info("PDF ファイルがありません。")
