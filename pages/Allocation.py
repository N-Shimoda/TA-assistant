import json
import os
from typing import Literal

import streamlit as st

from pages.Page import AppPage


class Allocation:
    def __init__(self, index: tuple[int, ...], box_type: Literal["parent", "problem"]):
        self.box_type = box_type
        self.children = []
        self.index = index
        self.level = len(index) - 1

    def render(self):
        if self.level == 0:
            with st.expander(self.index[-1], expanded=True):
                self.create_widgets()
        else:
            self.create_widgets()

    def create_widgets(self):
        st.markdown(f"{'#' * (self.level + 3)} {self.index[-1]}")
        index_str = "_".join(map(str, self.index))
        box_type_li = ["parent", "problem"] if self.level < 2 else ["problem"]
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input(
                "問題のタイトル",
                value=self.index[-1],
                key=f"title_input_{index_str}",
            )
            self.index = self.index[:-1] + (title,)
        with col2:
            self.box_type = st.selectbox(
                "種類",
                box_type_li,
                index=box_type_li.index(self.box_type),
                key=f"allocation_box_type_{index_str}",
            )
        match self.box_type:
            case "parent":
                for c in self.children:
                    c.render()
                if self.level < 2 and st.button("問題を追加", key=f"add_problem_{index_str}"):
                    new_problem = Allocation(index=(self.index + (len(self.children),)), box_type="problem")
                    self.children.append(new_problem)
                    st.rerun()
            case "problem":
                col1, col2, col3 = st.columns(3)
                with col1:
                    self.alloc_type = st.selectbox(
                        "配点の種類", ["full-or-zero", "partial"], key=f"allocation_type_{index_str}"
                    )
                with col2:
                    self.score = st.number_input(
                        "配点のスコア", value=10, min_value=0, key=f"allocation_score_{index_str}"
                    )
                with col3:
                    self.answer = st.text_input("略解", key=f"allocation_answer_{index_str}")
            case _:
                raise NotImplementedError(f"Unknown box type: {self.box_type}")

        if st.session_state.get("updated_title"):
            st.session_state["updated_title"] = False
            self.update_children(self.index[:-1])
            st.rerun()

    def to_dict(self):
        match self.box_type:
            case "problem":
                return {
                    "type": getattr(self, "alloc_type", None),
                    "score": getattr(self, "score", None),
                    "answer": getattr(self, "answer", None),
                }
            case "parent":
                return {c.index[-1]: c.to_dict() for c in self.children}
            case _:
                raise ValueError(f"Unknown box type: {self.box_type}")

    def update_children(self, new_head_index):
        print(self.box_type)
        match self.box_type:
            case "parent":
                for c in self.children:
                    print("updating", c)
                    c.update_children(new_head_index)
            case "problem":
                self.index = new_head_index + (self.index[-1],)


class AllocationPage(AppPage):
    def __init__(self):
        super().__init__()

        self.max_level = 3
        self.max_width = 10

        subjects = self._list_subdirs(self.base_dir)
        self.assignments = {sbj: self._list_subdirs(os.path.join(self.base_dir, sbj)) for sbj in subjects}
        self.selected_subject = st.session_state.get("subject")
        self.selected_assignment = st.session_state.get("assignment")

        self.alloc_path = (
            os.path.join(self.base_dir, self.selected_subject, self.selected_assignment, "allocation.json")
            if self.selected_subject and self.selected_assignment
            else None
        )
        st.session_state.setdefault("alloc_boxes", {})

    def render(self):
        st.header(
            "配点の定義（beta版）",
            divider="orange",
        )
        st.info(
            "本機能は **beta 版** です。配点は課題の追加時に `allocation.json` としてアップロードすることを推奨します",
            icon="📌",
        )
        try:
            with open(self.alloc_path, "r") as f:
                alloc_data = json.load(f)
            st.success("配点がすでに定義されています。", icon=":material/check:")
            st.write("JSONファイルの内容：")
            st.json(alloc_data, expanded=True)
        except (FileNotFoundError, TypeError):
            self.create_alloc_box()

        with st.sidebar:
            self.create_sidebar()

    def create_sidebar(self):
        st.subheader("課題の選択")
        subjects = list(self.assignments.keys())
        self.selected_subject = st.selectbox(
            "科目",
            subjects,
            index=(subjects.index(self.selected_subject) if self.selected_subject else None),
            key="subject_select",
        )
        assignment_li = self.assignments[self.selected_subject] if self.selected_subject else []
        self.selected_assignment = st.selectbox(
            "課題名",
            assignment_li,
            index=(assignment_li.index(self.selected_assignment) if self.selected_assignment else None),
            key="assignment_select",
        )
        # update session state for switching between Allocation and Grading pages
        st.session_state["subject"] = self.selected_subject
        st.session_state["assignment"] = self.selected_assignment

        st.subheader("配点データを削除")
        if st.button("リセット", disabled=not st.session_state["alloc_boxes"], icon=":material/delete:"):
            st.session_state["alloc_boxes"] = {}
            st.rerun()

    def create_alloc_box(self):
        if not st.session_state["alloc_boxes"]:
            st.warning("配点ボックスを追加してください。")
        for k, v in st.session_state["alloc_boxes"].items():
            v.render()

        if st.button("問題を追加"):
            self._on_add_problem()
        if st.button("配点を保存", icon=":material/playlist_add_check:"):
            allocation_data = {k: v.to_dict() for k, v in st.session_state["alloc_boxes"].items()}
            self._on_save(allocation_data)

    @st.dialog("問題を追加")
    def _on_add_problem(self):
        title = st.text_input("問題のタイトル", help="問1, 設問Aなど", key="problem_title")
        valid_title = title not in st.session_state["alloc_boxes"]
        if not valid_title:
            st.error("同名の問題が既に存在します。別の名前を選択してください。")
        if title and st.button("追加", disabled=not valid_title):
            st.session_state["alloc_boxes"][title] = Allocation(index=(title,), box_type="parent")
            st.rerun()

    @st.dialog("確認画面", width="large")
    def _on_save(self, allocation_data):
        st.write("以下の配点でよろしいですか？")
        st.json(allocation_data)
        st.write("保存先ファイル")
        st.code(self.alloc_path, language="shell", wrap_lines=True)
        if st.button("確定"):
            with open(self.alloc_path, "w") as f:
                json.dump(allocation_data, f, indent=4, ensure_ascii=False)
            st.rerun()


if __name__ == "__main__":
    st.set_page_config(page_title="配点の定義")
    page = AllocationPage()
    page.render()
