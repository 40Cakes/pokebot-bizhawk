import os
import logging
import fastjsonschema

from ruamel.yaml import YAML

from modules.Files import ReadFile, WriteFile

log = logging.getLogger(__name__)
yaml = YAML()
yaml.default_flow_style = False

block_schema = {
    "type": "object",
    "properties": {
        "block_list" : {"type": "array"}
    }
}

file = "stats\CatchBlockList.yml"
BlockListValidator = fastjsonschema.compile(block_schema)  # Validate the config file to ensure user didn't do a dumb

# Create block list file if doesn't exist
if not os.path.exists(file):
    WriteFile(file, "block_list: []")

def GetBlockList():
    CatchBlockListYml = ReadFile(file)
    if CatchBlockListYml:
        CatchBlockList = yaml.load(CatchBlockListYml)
        try:
            if BlockListValidator(CatchBlockList):
                return CatchBlockList
            return None
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
        data = yaml.load(ReadFile(file))
        data["block_list"] = blockList["block_list"]
        with open(file, "w") as fp:
            yaml.dump(data, fp)
    if not catch:
        # add pokemon to the block list
        blockList["block_list"].append(pkmName)
        
        # write back to yml
        data = yaml.load(ReadFile(file))
        data["block_list"] = blockList["block_list"]
        with open(file, "w") as fp:
            yaml.dump(data, fp)


    #add/remove as necessary depending on catch bool
    #write back to file
    
