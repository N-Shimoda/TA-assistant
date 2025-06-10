import os

import streamlit as st


class HomePage:
    def __init__(self, base_dir: str = "assignments"):
        self.base_dir = base_dir
        self.subjects = self._list_subdirs(self.base_dir)
        self.assignents = {sbj: self._list_subdirs(os.path.join(self.base_dir, sbj)) for sbj in self.subjects}

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

    def display(self):
        st.header("Home Page")
        st.button("新しい科目を追加", on_click=self._on_add_subject)
        for sbj, items in self.assignents.items():
            st.subheader(sbj)
            if items:
                for item in items:
                    st.page_link("pages/Grading.py", label=item)
            else:
                st.markdown("No assignments found.")

    @st.dialog("新しい科目を追加")
    def _on_add_subject(self):
        st.write("追加する科目名を入力してください")
        sbj_name = st.text_input("科目名", key="new_subject")
        if st.button("追加"):
            os.makedirs(os.path.join(self.base_dir, sbj_name), exist_ok=True)
            st.rerun()


if __name__ == "__main__":
    st.set_page_config(page_title="ホーム", layout="wide")
    home_page = HomePage()
    home_page.display()
