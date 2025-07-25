import json
from typing import Literal

import streamlit as st


class Allocation:
    def __init__(self, index: tuple[int, ...], box_type: Literal["parent", "problem"]):
        self.box_type = box_type
        self.children = []
        self.index = index

    def render(self):
        st.markdown(f"{'#' * (len(self.index) + 1)} {self.index[-1]}")
        index_str = "_".join(map(str, self.index))
        box_type_li = ["parent", "problem"]
        self.box_type = st.selectbox(
            "ボックスの種類",
            box_type_li,
            index=box_type_li.index(self.box_type),
            key=f"allocation_box_type_{index_str}",
        )
        match self.box_type:
            case "parent":
                for c in self.children:
                    c.render()
                if st.button("問題を追加", key=f"add_problem_{index_str}"):
                    new_problem = Allocation(index=(self.index + (len(self.children),)), box_type="problem")
                    self.children.append(new_problem)
                    print(self.children)
                    st.rerun()
            case "problem":
                self.alloc_type = st.selectbox(
                    "配点の種類", ["full-or-zero", "partial"], key=f"allocation_type_{index_str}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    self.score = st.number_input(
                        "配点のスコア", value=10, min_value=0, key=f"allocation_score_{index_str}"
                    )
                with col2:
                    self.answer = st.text_input("略解", key=f"allocation_answer_{index_str}")
            case _:
                raise NotImplementedError(f"Unknown box type: {self.box_type}")

    def to_dict(self):
        match self.box_type:
            case "problem":
                return {
                    "type": getattr(self, "alloc_type", None),
                    "score": getattr(self, "score", None),
                    "answer": getattr(self, "answer", None),
                }
            case "parent":
                return {c.name: c.to_dict() for c in self.children}
            case _:
                raise ValueError(f"Unknown box type: {self.box_type}")


class AllocationPage:
    def __init__(self):
        self.max_level = 3
        self.max_width = 10
        self.allocation = {}
        if "allocation_boxes" not in st.session_state:
            st.session_state["allocation_boxes"] = {}

    def render(self):
        st.title("配点の定義")
        with st.container(border=True):
            self.create_alloc_box()
        st.button("配点を保存", on_click=self._on_confirm, args=(self.box.to_dict(),))

    @st.fragment
    def create_alloc_box(self):
        self.box = Allocation(index=(0,), box_type="parent")
        self.box.render()

    @st.dialog("確認画面")
    def _on_confirm(self, allocation_data):
        st.write("以下の配点でよろしいですか？")
        st.json(allocation_data)
        if st.button("確定"):
            with open("test/allocation.json", "w") as f:
                json.dump(allocation_data, f, indent=4)
            st.toast("配点が保存されました。", icon="✅")
            st.session_state["allocation_boxes"] = []


if __name__ == "__main__":
    page = AllocationPage()
    page.render()
