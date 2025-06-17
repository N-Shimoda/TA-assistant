import io
import os
import shutil
import zipfile

import streamlit as st

from pages.Page import AppPage


class HomePage(AppPage):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()

        self.base_dir = self.config["save"]["dir"]
        os.makedirs(self.base_dir, exist_ok=True)
        self.subjects = self._list_subdirs(self.base_dir)
        self.assignments = {sbj: self._list_subdirs(os.path.join(self.base_dir, sbj)) for sbj in self.subjects}

        # initialize session states as None
        st.session_state.setdefault("uploaded_assignment")
        st.session_state.setdefault("subject")
        st.session_state.setdefault("assignment")

        if st.session_state.get("uploaded_assignment"):
            title = st.session_state["uploaded_assignment"]
            st.toast(f"課題「{title}」を追加しました。", icon="✅")
            st.session_state["uploaded_assignment"] = None

    def create_widgets(self):
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

        # navigation for the first time
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
                    if st.button(
                        item,
                        key=f"{sbj}_{item}",
                        type="tertiary",
                    ):
                        st.session_state["subject"] = sbj
                        st.session_state["assignment"] = item
                        st.switch_page("pages/Grading.py")
            else:
                st.markdown('<span style="color: gray;">課題がありません。</span>', unsafe_allow_html=True)

    @st.dialog("新しい科目を追加")
    def _on_add_subject(self):
        st.write("追加する科目名を入力してください")
        sbj_name = st.text_input("科目名", key="new_subject")
        if st.button("追加"):
            os.makedirs(os.path.join(self.base_dir, sbj_name), exist_ok=True)
            st.rerun()

    @st.dialog("新しい課題を追加")
    def _on_add_assignment(self):
        if self.subjects:
            st.write("課題の科目を選択してください")
            sbj_name = st.selectbox("科目", self.subjects, key="subject_selection")
        else:
            st.warning("科目が存在しません。先に科目を追加してください。")
            st.rerun()

        st.write("アップロード")
        zip_file = st.file_uploader(
            "課題ファイルを選択",
            type=["zip"],
            key="assignment_file",
            help="PandA から課題フォルダをダウンロードし、zip ファイルとしてアップロードして下さい。",
        )

        if zip_file and st.button("追加"):
            # extract assignment title from zip file name
            assignment_name = os.path.splitext(zip_file.name)[0]
            assignment_dir = os.path.join(self.base_dir, sbj_name)
            os.makedirs(assignment_dir, exist_ok=True)

            # Decompress the zip file
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
                    dest_path = os.path.join(assignment_dir, filename)
                    dest_dir = os.path.dirname(dest_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    with zf.open(info) as src, open(dest_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            st.session_state["uploaded_assignment"] = assignment_name
            st.rerun()

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


if __name__ == "__main__":
    st.set_page_config(page_title="ホーム", layout="wide")
    home_page = HomePage()
    home_page.create_widgets()
