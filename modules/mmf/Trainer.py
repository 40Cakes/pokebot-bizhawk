import json
import fastjsonschema
from modules.Config import GetConfig
from modules.mmf.Common import LoadJsonMmap

config = GetConfig()

trainer_schema = {
    "type": "object",
    "properties": {
        "tid": { "type": "number" },
        "sid": { "type": "number" },
        "state": { "type": "number" },
        "mapId": { "type": "number" },
        "mapBank": { "type": "number" },
        "posX": { "type": "number" },
        "posY": { "type": "number" },
        "facing": { "type": "string" },
        "roamerMapId": { "type": "number" }
    }
}

TrainerValidator = fastjsonschema.compile(trainer_schema) # Validate the data from the mmf, sometimes it sends junk

def GetTrainer():
    try:
        trainer = LoadJsonMmap(4096, "bizhawk_trainer_data-" + config["bot_instance_id"])["trainer"]
        if trainer:
            if TrainerValidator(trainer):
                return trainer
        return None
    except Exception as e:
        print(str(e))
        return None
