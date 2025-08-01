import io
import os
import shutil
import zipfile

import streamlit as st

from pages.Page import AppPage


class HomePage(AppPage):
    def __init__(self):
        super().__init__()

        os.makedirs(self.base_dir, exist_ok=True)
        self.subjects = self._list_subdirs(self.base_dir)
        self.assignments = {sbj: self._list_subdirs(os.path.join(self.base_dir, sbj)) for sbj in self.subjects}

        # initialize session states as None
        st.session_state.setdefault("need_allocation", False)
        st.session_state.setdefault("uploaded_assignment")
        st.session_state.setdefault("subject")
        st.session_state.setdefault("assignment")

        # point allocation after uploading an assignment
        if st.session_state.get("need_allocation"):
            st.session_state["need_allocation"] = False
            self._on_define_points()

        elif st.session_state.get("uploaded_assignment"):
            title = st.session_state["uploaded_assignment"]
            st.toast(f"課題「{title}」を追加しました。", icon="✅")
            st.session_state["uploaded_assignment"] = None

    def render(self):
        """Create widgets for the home page."""
        st.header("プロジェクト一覧")
        with st.sidebar:
            st.button("新規科目", on_click=self._on_add_subject, icon="🎓")
            st.button(
                "課題を追加する",
                on_click=self._on_add_assignment,
                disabled=not bool(self.assignments),
                icon="📚",
            )
        # navigation for the first activation
        if not self.assignments:
            st.markdown(
                '<span style="color: gray;">科目が登録されていません。サイドバーから新しい科目を追加してください。</span>',
                unsafe_allow_html=True,
            )
            return
        # display subjects and assignments
        for sbj, items in self.assignments.items():
            st.subheader(sbj, divider="orange")
            if items:
                for item in items:
                    if st.button(item, key=f"{sbj}_{item}", type="tertiary"):
                        st.session_state["subject"] = sbj
                        st.session_state["assignment"] = item
                        st.switch_page("pages/Grading.py")
            else:
                st.markdown('<span style="color: gray;">課題がありません。</span>', unsafe_allow_html=True)

    @st.dialog("新しい科目を追加")
    def _on_add_subject(self):
        st.write("追加する科目名を入力してください")
        sbj_name = st.text_input("科目名", key="new_subject")
        if sbj_name and st.button("追加"):
            os.makedirs(os.path.join(self.base_dir, sbj_name), exist_ok=True)
            st.rerun()

    @st.dialog("新しい課題を追加")
    def _on_add_assignment(self):
        st.subheader("科目")
        sbj_name = st.selectbox("課題の科目を選択してください", self.subjects, key="subject_selection")

        st.subheader("アップロード")
        zip_file = st.file_uploader(
            "課題ファイル",
            type=["zip"],
            key="assignment_file",
            help="PandA から課題フォルダをダウンロードし、圧縮した zip ファイルをアップロードして下さい。",
        )
        if zip_file:
            assignment_name = st.text_input("課題名", key="assignment_name", value=os.path.splitext(zip_file.name)[0])

        # Proceed only if a subject name and zip file are provided
        if sbj_name and zip_file and st.button("次へ"):
            assignment_dir = os.path.join(self.base_dir, sbj_name)
            os.makedirs(assignment_dir, exist_ok=True)

            # Decompress the zip file
            outdir = os.path.join(assignment_dir, assignment_name)
            self.decompress_zip(zip_file, outdir)

            st.session_state["subject"] = sbj_name
            st.session_state["assignment"] = assignment_name
            st.session_state["uploaded_assignment"] = assignment_name
            st.session_state["need_allocation"] = True
            st.rerun()

    @st.dialog("配点を定義")
    def _on_define_points(self):
        json_file = st.file_uploader(
            "配点データをアップロード",
            type=["json"],
            key="allocation_file",
            help="配点データを JSON 形式でアップロードしてください。",
        )
        if json_file:
            st.json(json_file.getvalue().decode("utf-8"))
        if json_file and st.button("完了"):
            # Create destination directory
            subject = st.session_state.get("subject")
            assignment = st.session_state.get("assignment")
            save_dir = os.path.join(self.base_dir, subject, assignment)

            # Save the JSON file
            save_path = os.path.join(save_dir, os.path.basename(json_file.name))
            with open(save_path, "wb") as f:
                f.write(json_file.read())
            st.session_state["uploaded_assignment"] = assignment
            st.rerun()

    def decompress_zip(self, zip_file, outdir):
        """
        Decompress a zip file into a subdirectory under assignment_dir named after the zip file (without extension).

        Parameters
        ----------
        zip_file : file-like object
            A file-like object representing the zip file to decompress.
        assignment_dir : str
            The directory path where the contents of the zip file will be extracted.

        Returns
        -------
        str
            The directory where the files were extracted.

        Notes
        -----
        - Skips hidden files and `__MACOSX` directories.
        - Attempts to decode filenames as UTF-8 to prevent garbled characters.
        - Removes the common top-level directory from extracted paths, if present.
        """
        os.makedirs(outdir, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(zip_file.read())) as zf:
            # Detect the common prefix (top-level directory) in the zip file
            names = [info.filename for info in zf.infolist() if not info.is_dir()]
            common_prefix = os.path.commonprefix(names)
            # Split by directory separator to avoid partial matches
            if common_prefix and not common_prefix.endswith("/"):
                common_prefix = os.path.dirname(common_prefix) + "/"

            for info in zf.infolist():
                # Skip __MACOSX and hidden files
                if (
                    info.filename.startswith("__MACOSX")
                    or info.filename.startswith(".")
                    or "/__MACOSX" in info.filename
                    or "/." in info.filename
                ):
                    continue
                if info.is_dir():
                    continue
                # Prevent garbled characters: decode as UTF-8 (cp437→utf-8)
                try:
                    filename = info.filename.encode("cp437").decode("utf-8")
                except Exception:
                    filename = info.filename
                # Remove the common prefix
                if common_prefix and filename.startswith(common_prefix):
                    filename = filename[len(common_prefix) :]
                if not filename:
                    continue
                # Swap the base directory with outdir
                parts = filename.split(os.sep)
                dest_path = os.path.join(outdir, *parts[1:])
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with zf.open(info) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

        return outdir


if __name__ == "__main__":
    st.set_page_config(page_title="ホーム", layout="wide")
    home_page = HomePage()
    home_page.render()
