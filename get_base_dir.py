import os

import toml


def get_base_dir_from_config():
    """
    Get the base directory for saving assignments from the config.toml file.

    Returns
    -------
    str
        The base directory specified in the config file, or 'assignments' if not set or config is missing.

    Notes
    -----
    If the config.toml file does not exist, it will be created as an empty file and the default value will be returned.
    """
    config_path = os.path.join(os.path.dirname(__file__), ".streamlit", "config.toml")
    if not os.path.exists(config_path):
        # config.tomlがなければ空で作成
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            f.write("")
        return "assignments"  # デフォルト値
    try:
        config = toml.load(config_path)
        return config.get("save", {}).get("dir", "assignments")
    except Exception:
        return "assignments"
