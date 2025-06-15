import os
import shutil

import streamlit as st
import toml


class ConfigPage:
    def __init__(self):
        self.CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "config.toml")
        self.current_dir = self.load_config()

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

    @st.dialog("Change assignments base directory")
    def change_base_dir_dialog(self):
        new_dir = st.text_input(
            "データを保存するディレクトリを指定して下さい（**絶対パス**）",
            key="new_dir_input",
        )
        if new_dir:
            dir_valid = os.path.isdir(new_dir)
            dir_empty = not os.listdir(new_dir) if dir_valid else False
            if dir_valid and dir_empty:
                st.success("有効なディレクトリ")
            elif dir_valid:
                st.warning("指定されたディレクトリは空ではありません。")
            else:
                st.error("指定されたパスはディレクトリではありません。")
            move_needed = self.has_assignments(self.current_dir) and dir_valid and new_dir != self.current_dir
            move_assign = False
            if move_needed:
                move_assign = st.checkbox("変更後のディレクトリに既存データをコピーする", value=True)
            if st.button("Save", key="save_btn"):
                if not dir_valid:
                    st.error("指定されたパスはディレクトリではありません。")
                else:
                    if move_needed and move_assign:
                        self.copy_assignments(self.current_dir, new_dir)
                        st.success("既存の課題が新しいディレクトリに移動されました。")
                    self.save_config(new_dir)
                    st.success(f"ベースディレクトリが更新されました: {new_dir}")

    def render(self):
        st.set_page_config(page_title="Config", layout="wide")
        st.title("Configuration")
        st.markdown("#### Base Directory")
        st.markdown(f"現在のディレクトリ : `{self.current_dir}`")
        st.button("変更", on_click=self.change_base_dir_dialog, key="change_base_dir_btn")


def main():
    page = ConfigPage()
    page.render()


if __name__ == "__main__":
    main()
