# Import modules
import io
import os
import re
import array
import sys
import glob
import json
import math
import mmap
import time
import atexit
import random
from pathlib import Path
from datetime import datetime
from threading import Thread
import logging
from logging.handlers import RotatingFileHandler

# Parsing modules
import fastjsonschema
# Data logging
import pandas as pd
# Integrations
from discord_webhook import DiscordWebhook, DiscordEmbed

from data.GameState import GameState
from data.MapData import mapRSE #mapFRLG
from modules.Config import GetConfig
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetOpponent, GetParty
from modules.mmf.Screenshot import GetScreenshot
from modules.mmf.Trainer import GetTrainer

config = GetConfig()

no_sleep_abilities = ["Shed Skin", "Insomnia", "Vital Spirit"]
pickup_pokemon = ["Meowth", "Aipom", "Phanpy", "Teddiursa", "Zigzagoon", "Linoone"]

@staticmethod
def average_iv_meets_threshold(pokemon: dict, threshold: int):
    iv_sum = (pokemon["hpIV"] + 
        pokemon["attackIV"] + 
        pokemon["defenseIV"] + 
        pokemon["speedIV"] + 
        pokemon["spAttackIV"] + 
        pokemon["spDefenseIV"])
    avg = iv_sum / 6
    return avg >= threshold 

@staticmethod
def wait_frames(frames: float):
    time.sleep(max((frames/60.0) / GetEmu()["speed"], 0.02))

@staticmethod
def emu_combo(sequence: list): # Function to send a sequence of inputs and delays to the emulator
    for k in sequence:
        if type(k) is int:
            wait_frames(k)
        else:
            press_button(k)
            wait_frames(1)

# TODO remove
@staticmethod
def read_file(file: str): # Simple function to read data from a file, return False if file doesn't exist
    if os.path.exists(file):
        with open(file, mode="r", encoding="utf-8") as open_file:
            return open_file.read()
    else:
        return False

# TODO remove
@staticmethod
def write_file(file: str, value: str, mode: str = "w"): # Simple function to write data to a file, will create the file if doesn't exist
    dirname = os.path.dirname(file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(file, mode=mode, encoding="utf-8") as save_file:
        save_file.write(value)
        return True

# TODO move to separate file in root dir for user to configure
def mon_is_desirable(pokemon: dict):
    ### Custom Filters ###
    # Add custom filters here (make sure to uncomment the line), examples:
    # If you want to pause the bot instead of automatically catching, replace `catch_pokemon()` with `input("Pausing bot for manual catch (don't forget to pause pokebot.lua script so you can provide inputs). Press Enter to continue...")`

    # --- Catch any species that the trainer has not already caught ---
    #elif pokemon["hasSpecies"] == 0: catch_pokemon()

    # --- Catch all Luvdisc with the held item "Heart Scale" ---
    #elif pokemon["name"] == "Luvdisc" and pokemon["itemName"] == "Heart Scale": catch_pokemon()

    # --- Catch Lonely natured Ralts with >25 attackIV and spAttackIV ---
    #elif pokemon["name"] == "Ralts" and pokemon["attackIV"] > 25 and pokemon["spAttackIV"] > 25 and pokemon["nature"] == "Lonely": catch_pokemon()

    if "perfect_ivs" in config["catch"] and average_iv_meets_threshold(pokemon, 31):
        return True
    elif "zero_ivs" in config["catch"] and not average_iv_meets_threshold(pokemon, 1):
        return True
    elif "good_ivs" in config["catch"] and average_iv_meets_threshold(pokemon, 25):
        return True
    elif "all" in config["catch"]:
        return True
    return False

def get_rngState(tid: str, mon: str):
    file = read_file(f"stats/{tid}/{mon.lower()}.json")
    data = json.loads(file) if file else {"rngState": []}

    return data

try:
    # Set up log handler
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(line:%(lineno)d) %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(message)s')
    path = "logs"
    logFile = f"{path}/debug.log"
    os.makedirs(path, exist_ok=True) # Create logs directory if not exist

    # Set up log file rotation handler
    log_handler = RotatingFileHandler(logFile, mode='a', maxBytes=20*1024*1024, backupCount=5, encoding=None, delay=0)
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.INFO)

    # Set up console log stream handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Create logger and attach handlers
    log = logging.getLogger('root')
    log.setLevel(logging.DEBUG)
    log.addHandler(log_handler)
    log.addHandler(console_handler)
except Exception as e:
    log.exception(str(e))
    os._exit(1)

try:
    global last_opponent_personality # TODO

    config = GetConfig() # Load config

    # Validate python version
    min_major = 3
    min_minor = 10
    v_major = sys.version_info[0]
    v_minor = sys.version_info[1]

    if v_major < min_major or v_minor < min_minor:
        log.error(f"\n\nPython version is out of date! (Minimum required version for pokebot is {min_major}.{min_minor})\nPlease install the latest version at https://www.python.org/downloads/\n")
        os._exit(1)

    log.info(f"Running pokebot on Python {v_major}.{v_minor}")

    while True:
        if GetTrainer():
            break
        else:
            log.error("\n\nUnable to initialize pokebot!\nPlease confirm that `pokebot.lua` is running in BizHawk, keep the Lua console open while the bot is active.\nIt can be opened through 'Tools > Lua Console'.\n")
            can_start_bot = False

    last_trainer_state, last_opponent_personality = None, None
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    log.info(f"Mode: {config['bot_mode']}")

    default_input = {"A": False, "B": False, "L": False, "R": False, "Up": False, "Down": False, "Left": False, "Right": False, "Select": False, "Start": False, "Light Sensor": 0, "Power": False, "Tilt X": 0, "Tilt Y": 0, "Tilt Z": 0, "SaveRAM": False}
        
    input_list_mmap = mmap.mmap(-1, 4096, tagname="bizhawk_input_list-" + config["bot_instance_id"], access=mmap.ACCESS_WRITE)
    g_current_index = 1 # Variable that keeps track of what input in the list we are on.
    input_list_mmap.seek(0)

    for i in range(100): # Clear any prior inputs from last time script ran in case you haven't refreshed in Lua
         input_list_mmap.write(bytes('a', encoding="utf-8"))
        
    item_list = json.loads(read_file("data/items.json"))
    type_list = json.loads(read_file("data/types.json"))
    route_list = json.loads(read_file("data/routes-emerald.json"))

    emu = GetEmu()
    log.info("Detected game: " + emu["detectedGame"])
    if any([x in emu["detectedGame"] for x in ["Emerald"]]): # "Ruby", "Sapphire"
        MapDataEnum = mapRSE
    #if any([x in emu["detectedGame"] for x in ["FireRed", "LeafGreen"]]):
    #    MapDataEnum = mapFRLG
    else:
        log.error("Unsupported game detected...")
        os._exit(1)

    hold_input_mmap = mmap.mmap(-1, 4096, tagname="bizhawk_hold_input-" + config["bot_instance_id"], access=mmap.ACCESS_WRITE)
    hold_input = default_input

    os.makedirs("stats", exist_ok=True) # Sets up stats files if they don't exist

    totals = read_file("stats/totals.json")
    stats = json.loads(totals) if totals else {"pokemon": {}, "totals": {"longest_phase_encounters": 0, "shortest_phase_encounters": "-", "phase_lowest_sv": 99999, "phase_lowest_sv_pokemon": "", "encounters": 0, "phase_encounters": 0, "shiny_average": "-", "shiny_encounters": 0}}

    encounters = read_file("stats/encounter_log.json")
    encounter_log = json.loads(encounters) if encounters else {"encounter_log": []}
    
    shinies = read_file("stats/shiny_log.json")
    shiny_log = json.loads(shinies) if shinies else {"shiny_log": []}
    pokedex_list = json.loads(read_file("data/pokedex.json"))

    if config["ui"]["enable"]:
        import webview
        from modules.FlaskServer import httpServer

        def on_window_close():
            if can_start_bot:
                release_all_inputs()

            log.info("Dashboard closed on user input")
            os._exit(1)

        server = Thread(target=httpServer)
        server.start()

        # Webview UI
        url=f"http://{config['ui']['ip']}:{config['ui']['port']}/dashboard"
        window = webview.create_window("PokeBot", url=url, width=config["width"], height=config["height"], resizable=True, hidden=False, frameless=False, easy_drag=True, fullscreen=False, text_select=True, zoomable=True)
        window.events.closed += on_window_close
        webview.start()
    
    release_all_inputs()
    press_button("SaveRAM") # Flush Bizhawk SaveRAM to disk

    while True:
        if GetTrainer() and GetEmu(): # Test that emulator information is accessible:
            match config["bot_mode"]:
                case "manual":
                    while not opponent_changed(): 
                        wait_frames(20)
                    identify_pokemon()
                case "spin":
                    mode_spin()
                case "sweet scent":
                    mode_sweetScent()
                case "bunny hop":
                    mode_bunnyHop()
                case "move between coords":
                    mode_move_between_coords()
                case "move until obstructed":
                    mode_move_until_obstructed()
                case "fishing":
                    mode_fishing()
                case "starters":
                    mode_starters()
                case "rayquaza":
                    mode_rayquaza()
                case "groudon":
                    mode_groudon()
                case "kyogre":
                    mode_kyogre()
                case "southern island":
                    mode_southernIsland()
                case "mew":
                    mode_farawayMew()
                case "regi trio":
                    mode_regiTrio()
                case "deoxys runaways":
                    mode_deoxysPuzzle()
                case "deoxys resets":
                    if config["deoxys_puzzle_solved"]:
                        mode_deoxysResets()
                    else:
                        mode_deoxysPuzzle(False)
                case "fossil":
                    mode_fossil()
                case "castform":
                    mode_castform()
                case "beldum":
                    mode_beldum()
                case "johto starters":
                    mode_johtoStarters()
                case "buy premier balls":
                    purchase_success = mode_buyPremierBalls()

                    if not purchase_success:
                        log.info(f"Ran out of money to buy Premier Balls. Script ended.")
                        input("Press any key to continue...")
                case other:
                    log.exception("Couldn't interpret bot mode: " + config["bot_mode"])
                    input("Press any key to continue...")
    else:
        opponent = GetOpponent()
        if opponent:
            last_opponent_personality = opponent["personality"]
        release_all_inputs()
        time.sleep(0.2)
    wait_frames(1)

except Exception as e:
    log.exception(str(e))
    os._exit(1)
