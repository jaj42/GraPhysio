import configparser
from pathlib import Path

from platformdirs import user_config_dir

config_dir = Path(user_config_dir(appname="larib-data", appauthor="larib-data", roaming=True))
configfile = config_dir / "config.ini"


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(configfile)
    return config


def save_config(config: configparser.ConfigParser) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(configfile, "w") as f:
        config.write(f)
