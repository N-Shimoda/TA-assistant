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

    @st.dialog("ベースディレクトリの変更")
    def change_base_dir_dialog(self):
        curr_dir = self.config.get("save", {}).get("dir", "")
        new_dir = st.text_input(
            "採点データを保存するフォルダを指定して下さい（**絶対パス**）",
            value=os.path.expanduser("~"),
            key="new_dir_input",
        )
        if new_dir:
            # check if the path is a valid directory and empty
            dir_valid = os.path.isdir(new_dir)
            dir_empty = not os.listdir(new_dir) if dir_valid else False
            if dir_valid and new_dir != curr_dir and dir_empty:
                st.write("有効なフォルダ")
            elif dir_valid and new_dir != curr_dir:
                st.warning("指定されたフォルダは空ではありません。", icon=":material/warning:")
                st.markdown(
                    '<span style="color: gray;">既存のコンテンツ : {}</span>'.format(
                        [f for f in os.listdir(new_dir) if not f.startswith(".")]
                    ),
                    unsafe_allow_html=True,
                )
            elif dir_valid:
                st.markdown("現在のフォルダが選択されました。")
                st.markdown(f"**`{new_dir}`**")
            else:
                st.error("指定されたパスはディレクトリではありません。")

            move_needed = self.has_assignments(curr_dir) and dir_valid and new_dir != curr_dir
            move_assign = False
            if move_needed:
                move_assign = st.checkbox("変更後のフォルダに既存のデータをコピーする", value=True)
            if st.button("保存", key="save_btn", disabled=(curr_dir == new_dir), icon=":material/check:"):
                # copy contents to the new directory
                if move_needed and move_assign:
                    with st.status("Copying assignments...", expanded=True):
                        for item in os.listdir(curr_dir):
                            st.write(f"Copying `{item}`...")
                            s = os.path.join(curr_dir, item)
                            d = os.path.join(new_dir, item)
                            if os.path.isdir(s):
                                shutil.copytree(s, d, dirs_exist_ok=True)
                            else:
                                shutil.copy2(s, d)
                        st.write("Done!")
                self.config["save"]["dir"] = new_dir
                self.save_config()
                st.session_state["just_saved"] = True
                st.rerun()

    @st.fragment
    def create_basedir_config(self):
        curr_dir = self.config.get("save", {}).get("dir", "")
        # badges to indicate the storage type
        if "OneDrive" in curr_dir:
            badge_str = ":blue-badge[:material/check: OneDrive]"
        elif "Google Drive" in curr_dir or "GoogleDrive" in curr_dir:
            badge_str = ":green-badge[:material/check: Google Drive]"
        elif "Mobile Documents" in curr_dir:
            badge_str = ":red-badge[:material/check: iCloud]"
        else:
            badge_str = ":gray-badge[:material/check: Local]"
        st.markdown("#### 課題データの保存先")
        st.markdown(
            f"現在のフォルダ：{badge_str}",
            help="採点データを保存するフォルダ。OneDrive や Google Drive で管理されたパスを指定すると、デバイス間での同期・バックアップが可能",
        )
        st.code(curr_dir, language="plaintext", wrap_lines=True)
        st.button("変更", on_click=self.change_base_dir_dialog, key="change_base_dir_btn", icon=":material/folder:")

    def create_height_config(self):
        """Configure window height of the Grading page."""
        st.markdown("#### Window Height")
        height = st.slider(
            "採点ページのウィンドウの高さ",
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

    def create_reset_button(self):
        """Reset the configuration to default values."""

        @st.dialog("設定をリセット")
        def reset_config_dialog():
            st.write("現在の設定がすべて初期値に戻ります。本当にリセットしますか？")
            st.write("デフォルトの設定：")
            st.code(toml.dumps(self.default_config), language="json", wrap_lines=True)
            if st.button("設定を初期化", key="confirm_reset_btn"):
                self.config = self.default_config
                self.save_config()
                st.session_state["just_saved"] = True
                st.session_state["subject"] = None
                st.session_state["assignment"] = None
                st.rerun()

        if st.button("設定をリセット", key="reset_config_btn", icon=":material/refresh:"):
            reset_config_dialog()

    def render(self):
        st.header("Configuration")
        self.create_basedir_config()
        self.create_height_config()
        with st.sidebar:
            self.create_reset_button()
            st.link_button(
                "GitHub",
                "https://github.com/N-Shimoda/TA-assistant",
                icon=":material/commit:",
            )


if __name__ == "__main__":
    st.set_page_config(page_title="Config")
    page = ConfigPage()
    page.render()
