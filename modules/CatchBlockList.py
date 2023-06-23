import os
import sys
import logging
import fastjsonschema
from ruamel.yaml import YAML
log = logging.getLogger(__name__)
yaml = YAML()
yaml.default_flow_style = False

block_schema = {
    "type": "object",
    "properties": {
        "block_list" : {"type": "array"}
    }
}
YmlValidator = fastjsonschema.compile(block_schema)  # Validate the config file to ensure user didn't do a dumb


def GetBlockList():
    if os.path.exists("modules\data\CatchBlockList.yml"):
        with open("modules\data\CatchBlockList.yml", mode="r", encoding="utf-8") as f:
            blocklist = yaml.load(f)
            try:
                YmlValidator(blocklist)
                return blocklist
            except fastjsonschema.exceptions.JsonSchemaDefinitionException as e:
                log.error(str(e))
                log.error("Block list is invalid!")
                return None

def BlockListManagement(pkmName, catch):
    # read current block list into array
    blockList = GetBlockList()
    if catch:
        for i,x in enumerate(blockList["block_list"]):
            if pkmName == x:
                # remove the selected mon from the array
                blockList["block_list"].pop(i)
        # write back to yml
        with open("modules\data\CatchBlockList.yml") as fp:
            data = yaml.load(fp)
            data["block_list"] = blockList["block_list"]
        with open("modules\data\CatchBlockList.yml", "w") as fp:
            yaml.dump(data, fp)
    if not catch:
        # add pokemon to the block list
        blockList["block_list"].append(pkmName)
        
        # write back to yml
        with open("modules\data\CatchBlockList.yml") as fp:
            data = yaml.load(fp)
            data["block_list"] = blockList["block_list"]
        with open("modules\data\CatchBlockList.yml", "w") as fp:
            yaml.dump(data, fp)


    #add/remove as necessary depending on catch bool
    #write back to file
    
