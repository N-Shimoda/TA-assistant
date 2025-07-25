import json
from typing import Literal

import streamlit as st


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
        st.markdown(
            f"{'#' * (self.level + 3)} {self.index[-1]} <span style='color:gray'>(level {self.level})</span>",
            unsafe_allow_html=True,
        )
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
            print(self.index)
        with col2:
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
                if self.level < 2 and st.button("問題を追加", key=f"add_problem_{index_str}"):
                    new_problem = Allocation(index=(self.index + (len(self.children),)), box_type="problem")
                    self.children.append(new_problem)
                    print(self.children)
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


class AllocationPage:
    def __init__(self):
        self.max_level = 3
        self.max_width = 10
        st.session_state.setdefault("alloc_boxes", {})

    def render(self):
        st.title("配点の定義")
        self.create_alloc_box()
        if st.button("問題を追加"):
            self._on_add_problem()
        if st.button("配点を保存", icon=":material/playlist_add_check:"):
            allocation_data = {k: v.to_dict() for k, v in st.session_state["alloc_boxes"].items()}
            self._on_save(allocation_data)

        # clear button
        with st.sidebar:
            st.subheader("配点データを削除")
            if st.button("リセット", disabled=not st.session_state["alloc_boxes"], icon=":material/delete:"):
                st.session_state["alloc_boxes"] = {}
                st.rerun()

    def create_alloc_box(self):
        if not st.session_state["alloc_boxes"]:
            st.warning("配点ボックスを追加してください。")
        for k, v in st.session_state["alloc_boxes"].items():
            v.render()

    @st.dialog("問題を追加")
    def _on_add_problem(self):
        title = st.text_input("問題のタイトル", key="problem_title")
        valid_title = title not in st.session_state["alloc_boxes"]
        if not valid_title:
            st.error("同名の問題が既に存在します。別の名前を選択してください。")
        if title and st.button("追加", disabled=not valid_title):
            st.session_state["alloc_boxes"][title] = Allocation(index=(title,), box_type="parent")
            st.rerun()

    @st.dialog("確認画面")
    def _on_save(self, allocation_data):
        st.write("以下の配点でよろしいですか？")
        st.json(allocation_data)
        if st.button("確定"):
            with open("test/allocation.json", "w") as f:
                json.dump(allocation_data, f, indent=4, ensure_ascii=False)
            st.toast("配点が保存されました。", icon="✅")
            st.rerun()


if __name__ == "__main__":
    page = AllocationPage()
    page.render()
