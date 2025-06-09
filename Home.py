import base64
import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


class SubmissionViewerApp:
    def __init__(self, base_dir: str = "assignments"):
        self.base_dir = base_dir
        self._ensure_base_dir()
        self.assignments = self._list_subdirs(self.base_dir)
        self.root_dir = None
        self.allocation = {}
        self.students = []
        self.selected_assignment = None
        self.selected_student = None
        self.scores = {}

    def _ensure_base_dir(self):
        if not os.path.isdir(self.base_dir):
            st.error(f"'{self.base_dir}' ディレクトリが見つかりません。")
            st.stop()

    def _list_subdirs(self, path: str):
        return sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])

    def _load_allocation(self, path: str):
        alloc_file = os.path.join(path, "allocation.json")
        if os.path.isfile(alloc_file):
            with open(alloc_file, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def render_sidebar(self):
        st.sidebar.title("設定")
        self.selected_assignment = st.sidebar.selectbox("課題を選択", self.assignments, key="assignment_select")
        self.root_dir = os.path.join(self.base_dir, self.selected_assignment)
        self.allocation = self._load_allocation(self.root_dir)

    def render_student_selection(self):
        # 学生リスト取得および選択
        self.students = self._list_subdirs(self.root_dir)
        self.selected_student = st.selectbox(
            "学生を選択", self.students, key="student_select", format_func=lambda x: x.split("(")[0]
        )

    def render_main_content(self):
        student_dir = os.path.join(self.root_dir, self.selected_student)
        htmls = list(Path(student_dir).glob("*_submissionText.html"))
        attachments_dir = os.path.join(student_dir, "提出物の添付ファイル")
        attachments = os.listdir(attachments_dir) if os.path.isdir(attachments_dir) else []
        pdfs = [f for f in attachments if Path(f).suffix.lower() == ".pdf"]

        col_main, col_grade = st.columns([3, 1])
        with col_main:
            tabs = st.tabs(["添付ファイル", "提出テキスト"] if pdfs else ["提出テキスト"])
            labels = ["添付ファイル", "提出テキスト"] if pdfs else ["提出テキスト"]
            for label, tab in zip(labels, tabs):
                with tab:
                    if label == "提出テキスト":
                        html_path = htmls[0]
                        components.html(Path(html_path).read_text(encoding="utf-8"), height=600, scrolling=True)
                    else:
                        fname = pdfs[0]
                        file_path = os.path.join(attachments_dir, fname)
                        with open(file_path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode("utf-8")
                        st.subheader(fname)
                        st.markdown(
                            f'<iframe src="data:application/pdf;base64,{b64}" width=100% height=800></iframe>',
                            unsafe_allow_html=True,
                        )
        with col_grade:
            self._render_grading_tab()

    def _render_grading_tab(self):
        st.header("採点結果")
        self.scores = {}

        def recurse(prefix: str, alloc: dict):
            # リーフ判定: score/typeキーがある場合
            if isinstance(alloc, dict) and "score" in alloc and "type" in alloc:
                max_score = int(alloc["score"])
                widget_key = f"{self.selected_student}_{prefix}".replace(" ", "_")
                if alloc["type"] == "partial":
                    val = st.number_input(prefix, min_value=0, max_value=max_score, step=1, key=widget_key)
                else:
                    checked = st.checkbox(prefix, key=widget_key)
                    val = max_score if checked else 0
                self.scores[prefix] = val
            elif isinstance(alloc, dict):
                for k, v in alloc.items():
                    new_pref = f"{prefix}_{k}" if prefix else k
                    recurse(new_pref, v)

        for q_key, q_val in self.allocation.items():
            recurse(q_key, q_val)

        total = sum(self.scores.values())
        st.markdown(f"**合計得点: {total} 点**")

        if st.button("保存", key="save_button"):
            self._save_scores()
            st.success("採点結果を保存しました。")

    def _save_scores(self):
        grades_file = os.path.join(self.root_dir, "detailed_grades.json")
        try:
            with open(grades_file, encoding="utf-8") as gf:
                data = json.load(gf)
        except FileNotFoundError:
            data = {}
        data[self.selected_student] = self.scores
        with open(grades_file, "w", encoding="utf-8") as gf:
            json.dump(data, gf, ensure_ascii=False, indent=2)

    def run(self):
        self.render_sidebar()
        self.render_student_selection()
        self.render_main_content()


if __name__ == "__main__":
    st.set_page_config(page_title="提出物ビューア", layout="wide")
    app = SubmissionViewerApp()
    app.run()
