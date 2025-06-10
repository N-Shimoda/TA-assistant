import base64
import csv
import json
import os
import shutil
import tempfile
from pathlib import Path

import streamlit as st


class GradingPage:
    def __init__(self, base_dir: str = "assignments"):
        # directories
        os.makedirs(base_dir, exist_ok=True)
        self.base_dir = base_dir
        self.root_dir = None

        # data for each assignment
        self.allocation = {}
        self.students = []

        # data for each student (i.e. submission)
        self.scores = {}
        self.saved_scores = {}
        self.comment_text = ""

        # initialize selections
        self.selected_subject = st.session_state.get("subject") if "subject" in st.session_state else None
        self.selected_assignment = st.session_state.get("assignment") if "assignment" in st.session_state else None
        self.selected_student = None

        self.subjects = self._list_subdirs(self.base_dir)
        self.assignments = {
            subject: self._list_subdirs(os.path.join(self.base_dir, subject)) for subject in self.subjects
        }

    def run(self):
        st.header("提出物ビューア")
        self.create_sidebar()
        self.create_widgets()

    def create_sidebar(self):
        with st.sidebar:
            st.markdown("### 提出物の選択")
            # selecttion of subject and assignment
            self.selected_subject = st.selectbox(
                "科目", self.subjects, index=self.subjects.index(self.selected_subject), key="subject_select"
            )
            assignment_li = self.assignments[self.selected_subject]
            self.selected_assignment = st.selectbox(
                "課題名",
                assignment_li,
                index=assignment_li.index(self.selected_assignment),
                key="assignment_select",
            )
            self.root_dir = os.path.join(self.base_dir, self.selected_subject, self.selected_assignment)
            self.allocation = self._load_allocation(self.root_dir)

            # student
            self.create_student_selection()

            # download button
            st.markdown("---")
            st.markdown("### ダウンロード")
            include_json = st.checkbox(
                "アプリ固有のjsonファイルを含める",
                value=True,
                key="include_json_files",
                help="PandA へアップロードする場合は、チェックを外してください",
            )
            if st.button("採点結果をダウンロード", key="download_grades"):
                self._on_download_click(include_json)

    def create_student_selection(self):
        self.students = self._list_subdirs(self.root_dir)
        if "student_index" not in st.session_state:
            st.session_state["student_index"] = 0
        sel = st.selectbox(
            "学生氏名",
            self.students,
            index=st.session_state["student_index"],
            key="student_select",
            format_func=lambda x: x.split("(")[0],
        )
        if sel != self.students[st.session_state["student_index"]]:
            st.session_state["student_index"] = self.students.index(sel)
        self.selected_student = self.students[st.session_state["student_index"]]

        # load saved scores
        try:
            grades_file = os.path.join(self.root_dir, "detailed_grades.json")
            with open(grades_file, encoding="utf-8") as gf:
                all_data = json.load(gf)
            self.saved_scores = all_data.get(self.selected_student, {})
        except FileNotFoundError:
            self.saved_scores = {}

        # load comments as HTML
        comments_path = os.path.join(self.root_dir, self.selected_student, "comments.txt")
        if os.path.isfile(comments_path):
            self.comment_text = Path(comments_path).read_text(encoding="utf-8")
        else:
            self.comment_text = ""

    def create_widgets(self):
        student_dir = os.path.join(self.root_dir, self.selected_student)
        htmls = list(Path(student_dir).glob("*_submissionText.html"))
        html_content = htmls and Path(htmls[0]).read_text(encoding="utf-8").strip() or None

        attachments_dir = os.path.join(student_dir, "提出物の添付ファイル")
        attachments = os.listdir(attachments_dir) if os.path.isdir(attachments_dir) else []
        pdfs = [f for f in attachments if Path(f).suffix.lower() == ".pdf"]

        col_main, col_grade = st.columns([3, 1], border=True)
        with col_main:
            self.create_submission_tab(pdfs, html_content, attachments_dir)
        with col_grade:
            self.create_grading_tab()

        self.display_progress()

    def create_submission_tab(self, pdfs: list, html_content: str | None, attachments_dir: str):
        """Create tabs for displaying submitted materials."""
        labels = []
        if pdfs and len(pdfs) > 1:
            labels.extend([f"添付ファイル : {i + 1}" for i in range(len(pdfs))])
        elif pdfs:
            labels.append("添付ファイル")
        if html_content:
            labels.append("提出テキスト")
        if not labels:
            labels.append("未提出")

        tabs = st.tabs(labels)
        # display PDFs
        for idx, pdf in enumerate(pdfs):
            with tabs[idx]:
                file_path = os.path.join(attachments_dir, pdf)
                b64 = base64.b64encode(open(file_path, "rb").read()).decode("utf-8")
                st.subheader(pdf)
                st.markdown(
                    f'<iframe src="data:application/pdf;base64,{b64}" width=100% height=720></iframe>',
                    unsafe_allow_html=True,
                )
        # submitted texts
        if html_content:
            idx = labels.index("提出テキスト")
            with tabs[idx]:
                st.components.v1.html(html_content, height=600, scrolling=True)
        # display "未提出" if no submissions
        if "未提出" in labels:
            with tabs[-1]:
                st.warning("課題が未提出です。")

    def create_grading_tab(self):
        tabs = st.tabs(["採点結果"])
        with tabs[0]:
            st.markdown("#### 採点結果")
            self.scores = {}

            def recurse(prefix: str, alloc: dict):
                if isinstance(alloc, dict) and "score" in alloc and "type" in alloc:
                    max_score = int(alloc["score"])
                    key = prefix
                    widget_key = f"{self.selected_student}_{prefix}".replace(" ", "_")
                    prev_val = self.saved_scores.get(key, 0)
                    if alloc["type"] == "partial":
                        val = st.number_input(
                            prefix, min_value=0, max_value=max_score, value=prev_val, step=1, key=widget_key
                        )
                    else:
                        checked = st.checkbox(prefix, value=(prev_val == max_score), key=widget_key)
                        val = max_score if checked else 0
                    self.scores[key] = val
                elif isinstance(alloc, dict):
                    for k, v in alloc.items():
                        new_pref = f"{prefix}_{k}" if prefix else k
                        recurse(new_pref, v)

            for q_key, q_val in self.allocation.items():
                recurse(q_key, q_val)

            total = sum(self.scores.values())
            st.markdown(f"**合計得点: {total} 点**")

            # display comments
            st.markdown("#### コメント")
            if self.comment_text:
                st.html(self.comment_text)
            else:
                st.markdown('<span style="color: gray;">コメントはありません。</span>', unsafe_allow_html=True)
            st.button("コメントを編集", on_click=self._on_edit_comment_click, icon="✏️")

            # save button
            st.button("保存して次へ", key="save_button", on_click=self._on_save_click, args=(total,), icon="🚀")
            if st.session_state.get("just_saved"):
                st.toast("採点結果を保存しました！", icon="🎉")
                st.session_state["just_saved"] = False

    def display_progress(self):
        """Display the overall progress of grading."""
        grades_file = os.path.join(self.root_dir, "detailed_grades.json")
        try:
            with open(grades_file, encoding="utf-8") as gf:
                graded = json.load(gf)
            graded_count = len(graded)
        except FileNotFoundError:
            graded_count = 0
        total_count = len(self.students)
        st.divider()
        st.markdown(f"#### 進捗状況: {graded_count} / {total_count}")
        st.progress(graded_count / total_count if total_count else 0)

    def _on_download_click(self, include_json: bool):
        """
        Create a zip file of the assignment directory and provide a download button in Streamlit.

        Parameters
        ----------
        include_json : bool
            If True, include app-specific JSON files (detailed_grades.json, allocation.json) in the zip archive.
            If False, exclude these files from the archive (for PandA upload, etc).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            for item in os.listdir(self.root_dir):
                s = os.path.join(self.root_dir, item)
                d = os.path.join(tmpdir, item)
                if not include_json and item in ["detailed_grades.json", "allocation.json"]:
                    continue
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            zip_path = shutil.make_archive(
                base_name=os.path.join(tmpdir, "grading_result"), format="zip", root_dir=tmpdir
            )
            with open(zip_path, "rb") as f:
                zip_bytes = f.read()
            st.download_button(
                label="zipファイルをダウンロード",
                data=zip_bytes,
                file_name="grading_result.zip",
                mime="application/zip",
            )

    @st.dialog("コメントを編集")
    def _on_edit_comment_click(self):
        st.write("採点コメントを編集してください。")
        if self.comment_text:
            st.components.v1.html(self.comment_text, height=40, scrolling=True)
        self.comment_text = st.text_input("コメント", placeholder="ここにコメントを入力...")
        if st.button("保存"):
            with open(os.path.join(self.root_dir, self.selected_student, "comments.txt"), "w", encoding="utf-8") as f:
                f.write("<p>" + self.comment_text + "</p>")
            st.success("コメントを保存しました！")
            st.rerun()

    def _on_save_click(self, total_score: int):
        self._save_scores(total_score)
        st.session_state["student_index"] = (st.session_state["student_index"] + 1) % len(self.students)
        st.session_state["just_saved"] = True

    def _save_scores(self, total_score: int):
        """
        Save the current scores and comments to files.

        Parameters
        ----------
        total_score : int
            The total score for the selected student.
        """
        # save detailed grades to JSON (original file for this app)
        grades_file = os.path.join(self.root_dir, "detailed_grades.json")
        try:
            with open(grades_file, "r", encoding="utf-8") as gf:
                data: dict[str, dict] = json.load(gf)
        except FileNotFoundError:
            data: dict[str, dict] = {}
        data[self.selected_student] = self.scores
        with open(grades_file, "w", encoding="utf-8") as gf:
            json.dump(data, gf, ensure_ascii=False, indent=2)

        # save overall grades to CSV (official file from PandA)
        csv_path = os.path.join(self.root_dir, "grades.csv")
        student_id = self.selected_student.split("(")[-1].rstrip(")")
        lines = []
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                lines.append(row)
        try:
            header_idx = next(i for i, r in enumerate(lines) if r and r[0] == "学生番号")
        except StopIteration:
            st.error("grades.csv に '学生番号' ヘッダー行が見つかりません。ファイル形式を確認してください。")
            return
        header = lines[header_idx]
        grade_idx = header.index("成績")
        for i in range(header_idx + 1, len(lines)):
            if lines[i] and lines[i][0] == student_id:
                lines[i][grade_idx] = str(total_score)
                break
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(lines)

    def _list_subdirs(self, path: str) -> list[str]:
        """
        List all subdirectories in the given path.

        Parameters
        ----------
        path : str
            The directory path to list subdirectories from.

        Returns
        -------
        list[str]
            A sorted list of subdirectory names, or None if the path does not exist or is not a directory.
        """
        return sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])

    def _load_allocation(self, path: str):
        alloc_file = os.path.join(path, "allocation.json")
        if os.path.isfile(alloc_file):
            with open(alloc_file, encoding="utf-8") as f:
                return json.load(f)
        return {}


if __name__ == "__main__":
    st.set_page_config(page_title="提出物ビューア", layout="wide")
    app = GradingPage()
    app.run()
