import os
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False

def GetConfig():
    file = "config.yml"
    if os.path.exists(file):
        with open(file, mode="r", encoding="utf-8") as f:
            config = yaml.load(f)
            config["bot_mode"] = config["bot_mode"].lower()
            return config
    else:
        return False # TODO temp add config validation here or move to UI
