import os
import shutil

import streamlit as st
import toml


class ConfigPage:
    def __init__(self):
        self.CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "config.toml")
        self.current_dir = self.load_config()

        st.session_state.setdefault("just_saved", False)

    def load_config(self):
        if not os.path.exists(self.CONFIG_PATH):
            os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
            with open(self.CONFIG_PATH, "w") as f:
                f.write("")
            return "assignments"
        try:
            config = toml.load(self.CONFIG_PATH)
            return config.get("save", {}).get("dir", "assignments")
        except Exception:
            return "assignments"

    def save_config(self, new_dir):
        config = {"save": {"dir": new_dir}}
        with open(self.CONFIG_PATH, "w") as f:
            toml.dump(config, f)

    def has_assignments(self, path):
        if not os.path.isdir(path):
            return False
        for entry in os.listdir(path):
            if not entry.startswith("."):
                return True
        return False

    def copy_assignments(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst, exist_ok=True)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    @st.dialog("ベースディレクトリの変更")
    def change_base_dir_dialog(self):
        new_dir = st.text_input(
            "採点データを保存するフォルダを指定して下さい（**絶対パス**）",
            key="new_dir_input",
        )
        if new_dir:
            # check if the path is a valid directory and empty
            dir_valid = os.path.isdir(new_dir)
            dir_empty = not os.listdir(new_dir) if dir_valid else False
            if dir_valid and dir_empty:
                st.write("有効なフォルダ")
            elif dir_valid:
                st.warning("指定されたフォルダは空ではありません。")
                st.markdown(
                    '<span style="color: gray;">現在のコンテンツ : {}</span>'.format(
                        [path for path in os.listdir(new_dir) if not path.startswith(".")]
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.error("指定されたパスはディレクトリではありません。")

            move_needed = self.has_assignments(self.current_dir) and dir_valid and new_dir != self.current_dir
            move_assign = False
            if move_needed:
                move_assign = st.checkbox("変更後のフォルダに既存のデータをコピーする", value=True)
            if st.button("保存", key="save_btn"):
                if move_needed and move_assign:
                    self.copy_assignments(self.current_dir, new_dir)
                self.save_config(new_dir)
                st.session_state["just_saved"] = True
                st.rerun()

    def render(self):
        st.set_page_config(page_title="Config", layout="wide")
        st.title("Configuration")
        st.markdown("#### Base Directory")
        st.markdown(f"現在のディレクトリ : `{self.current_dir}`")
        st.button("変更", on_click=self.change_base_dir_dialog, key="change_base_dir_btn")

        if st.session_state.get("just_saved"):
            st.toast("設定を保存しました。", icon="✅")
            st.session_state["just_saved"] = False


if __name__ == "__main__":
    page = ConfigPage()
    page.render()
