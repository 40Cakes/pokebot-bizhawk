import logging

import fastjsonschema

from modules.Config import GetConfig
from modules.mmf.Common import LoadJsonMmap

log = logging.getLogger(__name__)
config = GetConfig()

bag_schema = {
    "type": "object",
    "properties": {
        "type": {"type": "number"},
        "name": {"type": "string"},
        "quantity": {"type": "number"}
    }
}

BagValidator = fastjsonschema.compile(bag_schema)  # Validate the data from the mmf, sometimes it sends junk


def GetBag():
    while True:
        try:
            bag = LoadJsonMmap(8192, "bizhawk_bag_data-" + config["bot_instance_id"])["bag"]
            return bag # Validator throws an exception: Data must be object
            # if BagValidator(bag):
            #     return bag
        except Exception as e:
            log.debug("Failed to GetBag(), trying again...")
            log.debug(str(e))
