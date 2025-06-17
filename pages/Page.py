import os

import toml


class AppPage:
    """Common operations for all pages in the application. eg. Loading configurations."""

    def __init__(self):
        self.CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "config.toml")
        self.default_config = {
            "save": {"dir": "/Users/naoki/OneDrive - Kyoto University/assignments"},
            "window": {"grading_height": 740},
        }
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.CONFIG_PATH):
            os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
            with open(self.CONFIG_PATH, "w") as f:
                toml.dump(self.default_config, f)
            return self.default_config
        try:
            curr_config = toml.load(self.CONFIG_PATH)
            return self.merge_dicts(self.default_config, curr_config)
        except Exception:
            return self.default_config

    def merge_dicts(self, default: dict, override: dict) -> dict:
        """
        Recursively merges two dictionaries, with values from the override dictionary
        taking precedence. If both dictionaries contain a value for the same key and
        both values are dictionaries, they are merged recursively.

        Parameters
        ----------
        default : dict
            The base dictionary to merge into.
        override : dict
            The dictionary whose values will override those in the base dictionary.

        Returns
        -------
        dict
            A new dictionary containing the merged keys and values.
        """
        result = default.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self.merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
