import json
import numpy
import fastjsonschema
from datetime import datetime
from modules.Config import GetConfig
from modules.mmf.Common import LoadJsonMmap
from modules.mmf.Trainer import GetTrainer

config = GetConfig()

with open("./data/items.json", mode="r", encoding="utf-8") as f:
    item_list = json.loads(f.read())
with open("./data/locations.json", mode="r", encoding="utf-8") as f:
    location_list = json.loads(f.read())
with open("./data/moves.json", mode="r", encoding="utf-8") as f:
    move_list = json.loads(f.read())
with open("./data/pokemon.json", mode="r", encoding="utf-8") as f:
    pokemon_list = json.loads(f.read())
with open("./data/placeholder_pokemon.json", mode="r", encoding="utf-8") as f:
    placeholder_pokemon = json.loads(f.read())

pokemon_schema = {
    "type": "object",
    "properties": {
        "altAbility": { "type": "number" },
        "attack": { "type": "number" },
        "attackEV": { "type": "number" },
        "attackIV": { "type": "number" },
        "defense": { "type": "number" },
        "defenseEV": { "type": "number" },
        "defenseIV": { "type": "number" },
        "eventLegal": { "type": "number" },
        "experience": { "type": "number" },
        "friendship": { "type": "number" },
        "hasSpecies": { "type": "number" },
        "heldItem": { "type": "number" },
        "hp": { "type": "number" },
        "hpEV": { "type": "number" },
        "hpIV": { "type": "number" },
        "isBadEgg": { "type": "number" },
        "isEgg": { "type": "number" },
        "language": { "type": "number" },
        "level": { "type": "number" },
        "magicWord": { "type": "number" },
        "mail": { "type": "number" },
        "markings": { "type": "number" },
        "maxHP": { "type": "number" },
        "metGame": { "type": "number" },
        "metLevel": { "type": "number" },
        "metLocation": { "type": "number" },
        "moves": { "type": "array", "maxItems": 4 },
        "name": { "type": "string" },
        "otGender": { "type": "number" },
        "otId": { "type": "number" },
        "personality": { "type": "number" },
        "pokeball": { "type": "number" },
        "pokerus": { "type": "number" },
        "pp": { "type": "array", "maxItems": 4 },
        "ppBonuses": { "type": "number" },
        "shiny": { "type": "number" },
        "spAttack": { "type": "number" },
        "spAttackEV": { "type": "number" },
        "spAttackIV": { "type": "number" },
        "spDefense": { "type": "number" },
        "spDefenseEV": { "type": "number" },
        "spDefenseIV": { "type": "number" },
        "species": { "type": "number" },
        "speed": { "type": "number" },
        "speedEV": { "type": "number" },
        "speedIV": { "type": "number" },
        "status": { "type": "number" }
    }
}

PokemonValidator = fastjsonschema.compile(pokemon_schema) # Validate the data from the mmf, sometimes it sends junk

Natures = [
    "Hardy",
    "Lonely",
    "Brave",
    "Adamant",
    "Naughty",
    "Bold",
    "Docile",
    "Relaxed",
    "Impish",
    "Lax",
    "Timid",
    "Hasty",
    "Serious",
    "Jolly",
    "Naive",
    "Modest",
    "Mild",
    "Quiet",
    "Bashful",
    "Rash",
    "Calm",
    "Gentle",
    "Sassy",
    "Careful",
    "Quirky"
]

HiddenPowers = [
    "Fighting",
    "Flying",
    "Poison",
    "Ground",
    "Rock",
    "Bug",
    "Ghost",
    "Steel",
    "Fire",
    "Water",
    "Grass",
    "Electric",
    "Psychic",
    "Ice",
    "Dragon",
    "Dark"
]

def EnrichMonData(pokemon: dict): # Function to add information to the pokemon data extracted from Bizhawk
    try:
        if pokemon["speciesName"].isalpha():
            trainer = GetTrainer()
            pokemon["name"] = pokemon["speciesName"].capitalize() # Capitalise name
            pokemon["metLocationName"] = location_list[pokemon["metLocation"]] # Add a human readable location
            pokemon["type"] = pokemon_list[pokemon["name"]]["type"] # Get pokemon types
            pokemon["ability"] = pokemon_list[pokemon["name"]]["ability"][0] # Get pokemon abilities
            pokemon["hiddenPowerType"] = HiddenPowers[int(numpy.floor((((pokemon["hpIV"] % 2)+(2*(pokemon["attackIV"] % 2))+(4*(pokemon["defenseIV"] % 2))+(8*(pokemon["speedIV"] % 2))+(16*(pokemon["spAttackIV"] % 2))+(32*(pokemon["spDefenseIV"] % 2)))*15)/63))]
            pokemon["nature"] = Natures[pokemon["personality"] % 25] # Get pokemon nature
            pokemon["zeroPadNumber"] = f"{pokemon_list[pokemon['name']]['number']:03}" # Get zero pad number - e.g.: #5 becomes #005
            pokemon["itemName"] = item_list[pokemon["heldItem"]] # Get held item's name

            pBin = format(pokemon["personality"], "032b") # Convert personality ID to binary
            pokemon["shinyValue"] = int(bin(int(pBin[:16], 2) ^ int(pBin[16:], 2) ^ trainer["tid"] ^ trainer["sid"])[2:], 2) # https://bulbapedia.bulbagarden.net/wiki/Personality_value#Shininess
            pokemon["shiny"] = True if pokemon["shinyValue"] < 8 else False

            pokemon["move_1"] = pokemon["moves"][0]
            pokemon["move_2"] = pokemon["moves"][1]
            pokemon["move_3"] = pokemon["moves"][2]
            pokemon["move_4"] = pokemon["moves"][3]
            pokemon["move_1_pp"] = pokemon["pp"][0]
            pokemon["move_2_pp"] = pokemon["pp"][1]
            pokemon["move_3_pp"] = pokemon["pp"][2]
            pokemon["move_4_pp"] = pokemon["pp"][3]
            pokemon["type_1"] = pokemon["type"][0]

            pokemon["type_2"] = "None"
            if len(pokemon["type"]) == 2:
                pokemon["type_2"] = pokemon["type"][1]

            pokemon["enrichedMoves"] = []
            for move in pokemon["moves"]:
                pokemon["enrichedMoves"].append(move_list[move])

            if pokemon["pokerus"] != 0: # TODO get number of days infectious, see - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9rus#Technical_information
                if pokemon["pokerus"] % 10: 
                    pokemon["pokerusStatus"] = "infected"
                else: 
                    pokemon["pokerusStatus"] = "cured"
            else: 
                pokemon["pokerusStatus"] = "none"

            now = datetime.now()
            year = f"{now.year}"
            month = f"{(now.month):02}"
            day = f"{(now.day):02}"
            hour = f"{(now.hour):02}"
            minute = f"{(now.minute):02}"
            second = f"{(now.second):02}"

            pokemon["date"] = (f"{year}-{month}-{day}")
            pokemon["time"] = (f"{hour}:{minute}:{second}")

            return pokemon
        else:
            return placeholder_pokemon
    except Exception as e:
        print(str(e))
        return None

def GetOpponent():
    try:
        opponent = LoadJsonMmap(4096, "bizhawk_opponent_data-" + config["bot_instance_id"])["opponent"]
        if opponent:
            if PokemonValidator(opponent):
                return EnrichMonData(opponent)
        else:
            return placeholder_pokemon
        return None
    except Exception as e:
        print(str(e))
        return placeholder_pokemon

def GetParty():
    try:
        party = LoadJsonMmap(8192, "bizhawk_party_data-" + config["bot_instance_id"])["party"]
        if party:
            party_list = [pokemon for pokemon in party if PokemonValidator(pokemon)]
            return party_list
        return None
    except Exception as e:
        print(str(e))
        return None
