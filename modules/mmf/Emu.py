import logging

import fastjsonschema

from modules.Config import GetConfig
from modules.mmf.Common import LoadJsonMmap

log = logging.getLogger(__name__)
config = GetConfig()

emu_schema = {
    "type": "object",
    "properties": {
        "frameCount": {"type": "number"},
        "fps": {"type": "number"},
        "detectedGame": {"type": "string"},
        "rngState": {"type": "number"}
    }
}

EmuValidator = fastjsonschema.compile(emu_schema)  # Validate the data from the mmf, sometimes it sends junk


def LangISO(lang: int):
    match lang:
        case 1:
            return "en"
        case 2:
            return "jp"
        case 3:
            return "fr"
        case 4:
            return "es"
        case 5:
            return "de"
        case 6:
            return "it"


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


def GetEmu():
    while True:
        try:
            emu = LoadJsonMmap(4096, "bizhawk_emu_data-" + config["bot_instance_id"])["emu"]
            if EmuValidator(emu):
                emu["speed"] = clamp(emu["fps"] / 60, 0.06, 1000)
                emu["language"] = LangISO(emu["language"])
                return emu
        except Exception as e:
            log.debug("Failed to GetEmu(), trying again...")
            log.debug(str(e))
