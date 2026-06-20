import configparser
import logging
from pathlib import Path
from typing import Optional, Union


class ConfigHandler:
    def __init__(self, config_path: Union[str, Path]) -> None:
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        self.config_is_set = False

        self.defaults = {
            "SRC_PATH": str(Path.home() / "Downloads"),
            "DEST_PATH": str(Path.home() / "KiCad"),
            "debug_log": "False",
        }

        logging.info(f"ConfigHandler: loading config from {config_path}")

        try:
            read_ok = self.config.read(self.config_path)
            if read_ok:
                logging.info(f"ConfigHandler: config read successfully from {config_path}, sections={self.config.sections()}")
                if "config" not in self.config:
                    self.config.add_section("config")

                for key, default_value in self.defaults.items():
                    if key not in self.config["config"] or not self.config["config"][key]:
                        self.config["config"][key] = default_value

                self.config_is_set = True
                logging.info(f"ConfigHandler: SRC_PATH={self.config['config'].get('SRC_PATH')}, DEST_PATH={self.config['config'].get('DEST_PATH')}")
            else:
                logging.warning(f"ConfigHandler: config read returned empty from {config_path}, creating defaults")
                self._create_default_config()
        except Exception as e:
            logging.error(f"ConfigHandler: error reading config: {e}")
            self._create_default_config()

        if not self.config_is_set:
            logging.info("ConfigHandler: saving default config")
            self.save_config()

    def _create_default_config(self) -> None:
        self.config = configparser.ConfigParser()
        self.config.add_section("config")

        for key, value in self.defaults.items():
            self.config["config"][key] = value

        self.config_is_set = False
        logging.info(f"ConfigHandler: created default config: SRC_PATH={self.defaults['SRC_PATH']}, DEST_PATH={self.defaults['DEST_PATH']}")

    def get_DEBUG_LOG(self) -> bool:
        val = self.config["config"].get("debug_log", "False")
        return val.lower() == "true"

    def set_DEBUG_LOG(self, val: bool) -> None:
        logging.info(f"ConfigHandler: set_DEBUG_LOG to {val}")
        self.config["config"]["debug_log"] = str(val)
        self.save_config()

    def get_SRC_PATH(self) -> str:
        return self.config["config"]["SRC_PATH"]

    def set_SRC_PATH(self, var: str) -> None:
        self.config["config"]["SRC_PATH"] = var
        self.save_config()

    def get_DEST_PATH(self) -> str:
        path = self.config["config"]["DEST_PATH"]
        logging.debug(f"ConfigHandler: get_DEST_PATH -> {path}")
        return path

    def set_DEST_PATH(self, var: str) -> None:
        logging.info(f"ConfigHandler: set_DEST_PATH from {self.config['config'].get('DEST_PATH')} to {var}")
        self.config["config"]["DEST_PATH"] = var
        self.save_config()

    def get_value(self, key: str, section: str = "config") -> Optional[str]:
        try:
            return self.config[section][key]
        except KeyError:
            return None

    def set_value(self, key: str, value: str, section: str = "config") -> None:
        if section not in self.config:
            self.config.add_section(section)

        self.config[section][key] = value
        self.save_config()

    def save_config(self) -> None:
        try:
            logging.info(f"ConfigHandler: saving config to {self.config_path}")
            with open(self.config_path, "w") as configfile:
                self.config.write(configfile)
            logging.info(f"ConfigHandler: config saved successfully (DEST_PATH={self.config['config'].get('DEST_PATH')})")
        except Exception as e:
            logging.error(f"ConfigHandler: error saving config to {self.config_path}: {e}")
