import os
import shutil

import streamlit as st
import toml

from pages.Page import AppPage


class ConfigPage(AppPage):
    def __init__(self):
        super().__init__()
        st.session_state.setdefault("just_saved", False)
        if st.session_state.get("just_saved"):
            st.toast("設定を保存しました。", icon="✅")
            st.session_state["just_saved"] = False

    def save_config(self):
        """Saves the current configuration to the config file."""
        with open(self.CONFIG_PATH, "w") as f:
            toml.dump(self.config, f)
        print("Saved current config", self.config)

    def has_assignments(self, path):
        if not os.path.isdir(path):
            return False
        for entry in os.listdir(path):
            if not entry.startswith("."):
                return True
        return False

    def copy_assignments(self, src, dst):
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
                    '<span style="color: gray;">既存のコンテンツ : {}</span>'.format(os.listdir(new_dir)),
                    unsafe_allow_html=True,
                )
            else:
                st.error("指定されたパスはディレクトリではありません。")

            curr_dir = self.config.get("save", {}).get("dir", "")
            move_needed = self.has_assignments(curr_dir) and dir_valid and new_dir != curr_dir
            move_assign = False
            if move_needed:
                move_assign = st.checkbox("変更後のフォルダに既存のデータをコピーする", value=True)
            if st.button("保存", key="save_btn"):
                if move_needed and move_assign:
                    with st.status("Copying assignments..."):
                        st.write(f"Copying assignments from `{curr_dir}` to `{new_dir}`")
                        self.copy_assignments(curr_dir, new_dir)
                        st.write("Done!")
                self.config["save"]["dir"] = new_dir
                self.save_config()
                st.session_state["just_saved"] = True
                st.rerun()

    @st.fragment
    def create_basedir_config(self):
        curr_dir = self.config.get("save", {}).get("dir", "")
        st.markdown("#### 課題データの保存先")
        st.markdown(
            f"現在のフォルダ：**`{curr_dir}`**",
            help="採点データを保存するフォルダ。OneDrive や iCloud で管理されたパスを指定すると、デバイス間での同期が可能です。",
        )
        # badges to indicate the storage type
        if "OneDrive" in curr_dir:
            st.badge("OneDrive", icon=":material/check:")
        elif "Google Drive" in curr_dir or "GoogleDrive" in curr_dir:
            st.badge("Google Drive", icon=":material/check:", color="green")
        elif "Mobile Documents" in curr_dir:
            st.badge("iCloud", icon=":material/check:", color="red")
        else:
            st.badge("Local", icon=":material/check:", color="gray")
        st.button("変更", on_click=self.change_base_dir_dialog, key="change_base_dir_btn", icon=":material/folder:")

    def create_height_config(self):
        """Configure window height of the Grading page."""
        st.markdown("#### Window Height")
        height = st.slider(
            "採点ページの高さ",
            min_value=100,
            max_value=1600,
            value=self.config["window"]["grading_height"],
            step=10,
            key="window_height",
        )
        if st.button("保存", key="save_height_btn", icon=":material/check:"):
            # Update the config with the new height
            self.config["window"]["grading_height"] = height
            self.save_config()
            st.session_state["just_saved"] = True

    def create_reset_config(self):
        """Reset the configuration to default values."""

        @st.dialog("設定をリセット")
        def reset_config_dialog():
            st.write("設定をリセットすると、現在の設定がすべて初期値に戻ります。本当にリセットしますか？")
            st.write("デフォルトの設定：")
            st.code(toml.dumps(self.default_config), language="json", wrap_lines=True)
            if st.button("はい、リセットします", key="confirm_reset_btn"):
                self.config = self.default_config
                self.save_config()
                st.session_state["just_saved"] = True
                st.rerun()

        if st.button("設定をリセット", key="reset_config_btn", icon=":material/refresh:"):
            reset_config_dialog()

    def render(self):
        st.title("Configuration")
        self.create_basedir_config()
        self.create_height_config()
        with st.sidebar:
            self.create_reset_config()


if __name__ == "__main__":
    st.set_page_config(page_title="Config")
    page = ConfigPage()
    page.render()
