# Import modules
import io                                        # https://docs.python.org/3/library/io.html
import os                                        # https://docs.python.org/3/library/os.html
import re                                        # https://docs.python.org/3/library/re.html
import sys                                       # https://docs.python.org/3/library/sys.html
import glob                                      # https://docs.python.org/3/library/glob.html
import json                                      # https://docs.python.org/3/library/json.html
import math                                      # https://docs.python.org/3/library/math.html
import mmap                                      # https://docs.python.org/3/library/mmap.html
import time                                      # https://docs.python.org/3/library/time.html
import atexit                                    # https://docs.python.org/3/library/atexit.html
import random                                    # https://docs.python.org/3/library/random.html
import argparse                                  # https://docs.python.org/3/library/argparse.html
from pathlib import Path                         # https://docs.python.org/3/library/pathlib.html
from datetime import datetime                    # https://docs.python.org/3/library/datetime.html
from threading import Thread, Event              # https://docs.python.org/3/library/threading.html
import logging                                   # https://docs.python.org/3/library/logging.html
from logging.handlers import RotatingFileHandler # https://docs.python.org/3/library/logging.html
# Image processing and detection modules            
import cv2                                       # https://pypi.org/project/opencv-python/
import numpy                                     # https://pypi.org/project/numpy/
from PIL import Image, ImageGrab, ImageFile      # https://pypi.org/project/Pillow/
# HTTP server/interface modules         
from flask import Flask, abort, jsonify, request # https://pypi.org/project/Flask/
from flask_cors import CORS                      # https://pypi.org/project/Flask-Cors/
import webview                                   # https://pypi.org/project/pywebview/
# Parsing modules           
from ruamel.yaml import YAML                     # https://pypi.org/project/ruamel.yaml/
import fastjsonschema                            # https://pypi.org/project/fastjsonschema/

def read_file(file: str): # Function to read data from a file
    try:
        debug_log.debug(f"Reading file: {file}...")
        if os.path.isfile(file):
            with open(file, mode="r", encoding="utf-8") as open_file:
                file_data = open_file.read()
                return file_data
        else:
            debug_log.exception('')
            return False
    except:
        debug_log.exception('')
        return False

def write_file(file: str, value: str): # Function to write data to a file
    try:
        debug_log.debug(f"Writing file: {file}...")
        with open(file, mode="w", encoding="utf-8") as save_file:
            save_file.write(value)
            return True
    except:
        debug_log.exception('')
        return False

def load_json_mmap(size, file): # Function to load a JSON object from a memory mapped file (Bizhawk maps the files)
    try:
        shm = mmap.mmap(0, size, file)
        if shm:
            try:
                if args.dm: debug_log.debug(f"Attempting to read {file} ({size} bytes) from memory...")
                bytes_io = io.BytesIO(shm)
                byte_str = bytes_io.read()
                if args.dm: debug_log.debug(f"Byte string: {byte_str}")
                json_obj = json.loads(byte_str.decode("utf-8").split("\x00")[0])
                if args.dm: debug_log.debug(f"JSON result: {json_obj}")
                return json_obj
            except: return False
        else: return False
    except:
        debug_log.exception('')
        return False

def emu_combo(sequence: list): # Function to run a sequence of inputs and delays
    try:
        sleep_pattern = "^\d*\.?\d*sec$"

        for k in sequence:
            if re.match(sleep_pattern, k):
                delay = float(re.sub(r"sec$", "", k))
                time.sleep(delay/emu_speed)
            else: press_button(k)
    except: debug_log.exception('')

def press_button(button: str):
    global press_input
    debug_log.debug(f"Pressing: {button}...")
    press_input[button] = True
    time.sleep(0.01/emu_speed)
    press_input[button] = False
    time.sleep(0.01/emu_speed)

def hold_button(button: str):
    global hold_input
    debug_log.debug(f"Holding: {button}...")
    hold_input[button] = True

def release_button(button: str):
    global hold_input
    debug_log.debug(f"Releasing: {button}...")
    hold_input[button] = False

def release_all_inputs():
    global press_input, hold_input
    debug_log.debug(f"Releasing all inputs...")
    for button in ["A", "B", "L", "R", "Up", "Down", "Left", "Right", "Select", "Start", "Power"]:
        press_input[button] = False
        hold_input[button] = False

def opponent_changed(): # This function detects if there is a new opponent, indicating the game state is now in a battle
    try:
        global last_trainer_state, last_opponent_personality

        if opponent_info:
            if last_opponent_personality != opponent_info["personality"]:
                last_opponent_personality = opponent_info["personality"]
                debug_log.info("Opponent has changed!")
                return True
            else: return False
        elif trainer_info:
            if trainer_info["state"] != 80 and trainer_info["state"] == 255 and last_trainer_state != trainer_info["state"]:
                last_trainer_state = trainer_info["state"]
                debug_log.info("Trainer state has changed!")
                return True
            else: return False
        else: return False
    except:
        debug_log.exception('')
        return False

def find_image(file: str): # Function to find an image in a BizHawk screenshot
    try:
        profile_start = time.time() # Performance profiling
        hold_button("Screenshot")
        threshold = 0.999
        if args.di: debug_log.debug(f"Searching for image {file} (threshold: {threshold})")

        shm = mmap.mmap(0, mmap_screenshot_size, mmap_screenshot_file)
        screenshot = Image.open(io.BytesIO(shm))

        screenshot = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_BGR2RGB) # Convert screenshot to numpy array COLOR_BGR2RGB
        template = cv2.imread(file, cv2.IMREAD_UNCHANGED)
        hh, ww = template.shape[:2]
    
        correlation = cv2.matchTemplate(screenshot, template[:,:,0:3], cv2.TM_CCORR_NORMED) # Do masked template matching and save correlation image
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(correlation)
        max_val_corr = float('{:.6f}'.format(max_val))

        release_button("Screenshot")

        if args.di:
            debug_log.debug(f"Image detection took: {(time.time() - profile_start)*1000} ms")
            cv2.imshow("screenshot", screenshot)
            cv2.waitKey(1)
        if max_val_corr > threshold: 
            if args.di:
                loc = numpy.where(correlation >= threshold)
                result = screenshot.copy()
                for point in zip(*loc[::-1]):
                    cv2.rectangle(result, point, (point[0]+ww, point[1]+hh), (0,0,255), 1)
                    cv2.imshow(f"match", result)
                    cv2.waitKey(1)
            if args.di: debug_log.debug(f"Maximum correlation value ({max_val_corr}) is above threshold ({threshold}), file {file} was on-screen!")
            return True
        else:
            if args.di: debug_log.debug(f"Maximum correlation value ({max_val_corr}) is below threshold ({threshold}), file {file} was not detected on-screen.")
            return False
    except:
        debug_log.exception('')
        return None

def catch_pokemon(): # Function to catch pokemon
    try:
        if config["manual_catch"]: return True
        else:
            debug_log.info("Attempting to catch Pokemon...")
            while not find_image("data/templates/battle/fight.png"):
                emu_combo(["button_release:all", "B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible

            if "spore" in config["catch"]: # Use Spore to put opponent to sleep to make catches much easier
                debug_log.info("Attempting to sleep the opponent...")
                i, spore_pp = 0, 0
    
                if (opponent_info["status"] == 0) and (opponent_info["name"] not in config["no_sleep_pokemon"]):
                    for move in party_info[0]["enrichedMoves"]:
                        if move["name"] == "Spore":
                            spore_pp = move["pp"]
                            spore_move_num = i
                        i += 1
    
                    if spore_pp != 0:
                        emu_combo(["A", "0.1sec"])
                        if spore_move_num == 0: seq = ["Up", "Left"]
                        elif spore_move_num == 1: seq = ["Up", "Right"]
                        elif spore_move_num == 2: seq = ["Left", "Down"]
                        elif spore_move_num == 3: seq = ["Right", "Down"]
    
                        while not find_image("data/templates/spore.png"):
                            emu_combo(seq)
    
                        emu_combo(["A", "4sec"]) # Select move and wait for animations
    
                while not find_image("data/templates/battle/bag.png"): emu_combo(["button_release:all", "B", "Up", "Right"]) # Press B + up + right until BAG menu is visible

            while True:
                if find_image("data/templates/battle/bag.png"): press_button("A")

                # TODO Safari Zone
                #if opponent_info["metLocationName"] == "Safari Zone":
                #    while not find_image("data/templates/battle/safari_zone/ball.png"):
                #        if trainer_info["state"] == 80: # State 80 = overworld
                #            return False
                #        emu_combo(["B", "Up", "Left"]) # Press B + up + left until BALL menu is visible

                # Preferred ball order to catch wild mons + exceptions # TODO move pokeball preference to config
                # TODO read this data from memory instead
                if trainer_info["state"] == 0:
                    if not bag_menu(category="pokeballs", item="premier_ball") and opponent_info["name"] not in ["Abra"]:
                        if not bag_menu(category="pokeballs", item="ultra_ball"):
                            if not bag_menu(category="pokeballs", item="great_ball"):
                                if not bag_menu(category="pokeballs", item="poke_ball"):
                                    debug_log.info("No balls to catch the Pokemon found. Killing the script!")
                                    os._exit(1)

                if find_image("data/templates/gotcha.png"): # Check for gotcha! text when a pokemon is successfully caught
                    debug_log.info("Pokemon caught!")

                    while trainer_info["state"] != 80: # State 80 = overworld
                        press_button("B")
                    time.sleep(2/emu_speed) # Wait for animations
                    if "save_game_after_catch" in config["game_save"]: save_game()
                    return True

                if trainer_info["state"] == 80: # State 80 = overworld
                    return False
    except:
        debug_log.exception('')
        return False

def battle(): # Function to battle wild pokemon
    try:
        # This will only battle with the lead pokemon of the party, and will run if it dies or runs out of PP
        debug_log.info("Battling Pokemon...")

        while opponent_info["hp"] != 0 and party_info[0]["hp"] != 0:
            while not find_image("data/templates/battle/fight.png"):
                if trainer_info["state"] == 80: # State 80 = overworld
                    return
                emu_combo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible

            debug_log.info("Finding a damaging attack with PP...")

            i, effective_pp, power_pp = 0, 0, 0
            for move in party_info[0]["enrichedMoves"]:
                if move["name"] not in config["banned_moves"]:
                    if move["power"] != 0:
                        power_pp += party_info[0]["pp"][i]
                        for type in opponent_info["type"]:
                            if type in type_list[move["type"]]["immunes"] or type in type_list[move["type"]]["weaknesses"]: debug_log.info(f"Opponent type {opponent_info['type']} is immune/weak against move {move['name']}") 
                            else: effective_pp += party_info[0]["pp"][i]
                i += 1

            if effective_pp == 0 and power_pp > 0:
                debug_log.info("Lead Pokemon has no effective PP to damage opponent!")
                flee_battle()
                return False

            if effective_pp == 0 and power_pp == 0:
                debug_log.info("Lead Pokemon has no more damaging PP!")
                flee_battle()
                return False

            i = 0
            if effective_pp > 0:
                for move in party_info[0]["enrichedMoves"]:
                    immune = False
                    if move["name"] not in config["banned_moves"]:
                        if move["power"] != 0:
                            for type in opponent_info["type"]:
                                if type in type_list[move["type"]]["immunes"]: # TODO add option to avoid using ineffective (0.5x) moves
                                    immune = True

                            if party_info[0]["pp"][i] != 0 and not immune:
                                emu_combo(["A", "0.05sec"])
                                if i == 0:
                                    emu_combo(["Up", "Left"])
                                    break
                                elif i == 1:
                                    emu_combo(["Up", "Right"])
                                    break
                                elif i == 2:
                                    emu_combo(["Left", "Down"])
                                    break
                                elif i == 3:
                                    emu_combo(["Right", "Down"])
                                    break
                    i += 1
                if i <= 3: emu_combo(["A", "4sec"]) # Select move and wait for animations

        if party_info[0]["hp"] == 0:
            debug_log.info("Lead Pokemon out of HP!")
            flee_battle()
            return False

        while trainer_info["state"] != 80: # State 80 = overworld
            if find_image("data/templates/stop_learning.png"): # Check if our Pokemon is trying to learn a move and skip learning
                press_button("A")
            press_button("B")

        if opponent_info["hp"] == 0:
            debug_log.info("Battle won!")
            return True
    except:
        debug_log.exception('')
        return False

def flee_battle(): # Function to run from wild pokemon
    try:
        debug_log.info("Running from battle...")
        while trainer_info["state"] != 80: # State 80 = overworld
            while not find_image("data/templates/battle/run.png") and trainer_info["state"] != 80: emu_combo(["Right", "Down", "B"]) # Press right + down until RUN is selected
            while find_image("data/templates/battle/run.png") and trainer_info["state"] != 80: press_button("A")
            press_button("B")
        time.sleep(0.8/emu_speed) # Wait for battle fade animation
    except:
        debug_log.exception('')

def run_until_obstructed(direction: str, run: bool = True): # Function to run until trainer position stops changing
    try:
        debug_log.info(f"Pathing {direction.lower()} until obstructed...")
        if run: hold_button("B")

        last_x = trainer_info["posX"]
        last_y = trainer_info["posY"]

        dir_unchanged = 0
        while dir_unchanged < 35:
            time.sleep(0.01/emu_speed)
            hold_button(direction)
            if direction == "Left" or direction == "Right":
                if last_x == trainer_info["posX"]: dir_unchanged += 1
                else:
                    last_x = trainer_info["posX"]
                    dir_unchanged = 0
            if direction == "Up" or direction == "Down":
                if last_y == trainer_info["posY"]: dir_unchanged += 1
                else:
                    last_y = trainer_info["posY"]
                    dir_unchanged = 0
        
        release_button(direction)
        debug_log.info("Bonk!")
        if run: release_button("B")
    except:
        debug_log.exception('')

def follow_path(coords: list):
    def run_to_pos(x: int, y: int, map_data: tuple, run: bool = True):
        try:
            while True:
                if x != trainer_info["posX"]:
                    axis = "posX"
                    directions = ["Left", "Right"]
                    end_pos = x
                elif y != trainer_info["posY"]:
                    axis = "posY"
                    directions = ["Up", "Down"]
                    end_pos = y
                else: return True

                def target_pos():
                    if run:
                        hold_button("B")
                    if end_pos < trainer_info[axis]:
                        hold_button(directions[0])
                        return False
                    elif end_pos > trainer_info[axis]:
                        hold_button(directions[1])
                        return False
                    else: return True

                stuck = 0
                last_axis = 0

                if map_data != []:
                    debug_log.info(f"Running to map: {map_data[0][0]}:{map_data[0][1]}")
                    while (trainer_info["mapBank"] != map_data[0][0] or trainer_info["mapId"] != map_data[0][1]):
                        if stuck > 25:
                            press_button("B")
                            stuck = 0
                        
                        if trainer_info[axis] == last_axis: stuck += 1
                        else: stuck = 0
                        last_axis = trainer_info[axis]
                        time.sleep(0.01/emu_speed)

                        if not opponent_changed():
                            try: target_pos()
                            except: debug_log.exception('')
                        else:
                            identify_pokemon()
                            return False
                    else: return True

                else:
                    debug_log.info(f"Running to {axis}: {end_pos}")
                    while trainer_info[axis] != end_pos:
                        if stuck > 25:
                            press_button("B")
                            stuck = 0
                        
                        if trainer_info[axis] == last_axis: stuck += 1
                        else: stuck = 0
                        last_axis = trainer_info[axis]
                        time.sleep(0.01/emu_speed)

                        if not opponent_changed():
                            try: target_pos()
                            except:
                                debug_log.exception('')
                                return False
                        else:
                            identify_pokemon()
                            return False
                    else:
                        release_all_inputs()
                        return True
        except:
            debug_log.exception('')
            return False

    try:
        for x, y, *map_data in coords:
            debug_log.info(f"Current: X: {trainer_info['posX']}, Y: {trainer_info['posY']}, Map: [({trainer_info['mapBank']},{trainer_info['mapId']})]")
            debug_log.info(f"Pathing: X: {x}, Y: {y}, Map: {map_data}")
            while not run_to_pos(x, y, map_data): continue
            else: release_all_inputs()
    except:
        debug_log.exception('')
        return False

def start_menu(entry: str): # Function to open any start menu item - presses START, finds the menu entry and opens it
    try:
        if entry in ["bag", "bot", "exit", "option", "pokedex", "pokemon", "pokenav", "save"]:
            debug_log.info(f"Opening start menu entry: {entry}")
            filename = f"data/templates/start_menu/{entry.lower()}.png"
            
            release_all_inputs()
            emu_combo(["Start", "0.2sec"]) # Open start menu

            while not find_image(filename): # Find menu entry
                emu_combo(["Down", "0.2sec"])

            while find_image(filename): # Press menu entry
                emu_combo(["A", "0.2sec"])
        else:
            return False
    except:
        debug_log.exception('')
        return False

def bag_menu(category: str, item: str): # Function to find an item in the bag and use item in battle such as a pokeball
    try:
        if category in ["berries", "items", "key_items", "pokeballs", "tms&hms"]:
            debug_log.info(f"Scrolling to bag category: {category}...")

            while not find_image(f"data/templates/start_menu/bag/{category.lower()}.png"):
                emu_combo(["Right", "0.3sec"]) # Press right until the correct category is selected
            time.sleep(2/emu_speed) # Wait for animations

            debug_log.info(f"Scanning for item: {item}...")
            i = 0
            while not find_image(f"data/templates/start_menu/bag/items/{item}.png") and i < 50:
                if i < 25: emu_combo(["Down", "0.05sec"])
                else: emu_combo(["Up", "0.05sec"])
                i += 1

            if find_image(f"data/templates/start_menu/bag/items/{item}.png"):
                debug_log.info(f"Using item: {item}...")
                while trainer_info["state"] == 0: emu_combo(["A", "0.5sec"]) # Press A to use the item
                return True
            else:
                return False
    except:
        debug_log.exception('')
        return False

def pickup_items(): # If using a team of Pokemon with the ability "pickup", this function will take the items from the pokemon in your party if 3 or more Pokemon have an item
    try:
        debug_log.info("Checking for pickup items...")
        item_count = 0
        pickup_pokemon = ["ZIGZAGOON", "LINOONE"]

        for i in range(1, 6):
            try:
                pokemon = party_info[i]
                if pokemon["speciesName"] in pickup_pokemon:
                    debug_log.info(f"Pokemon {i}: {pokemon['speciesName']} has item: {item_list[pokemon['heldItem']]}")
                    if pokemon["heldItem"] != 0: item_count += 1
            except:
                debug_log.exception('')

        if item_count >= 3: # Only run if 3 or more Pokemon have an item
            time.sleep(0.3/emu_speed) # Wait for animations
            start_menu("pokemon") # Open Pokemon menu

            for i in range(1, 6):
                pokemon = party_info[i]

                if item_count > 0:
                    if pokemon["speciesName"] in pickup_pokemon:
                        if pokemon["heldItem"] != 0:
                            emu_combo(["Down", "0.05sec", "A", "0.05sec", "Down", "0.05sec", "Down", "0.05sec", "A", "0.05sec", "Down", "0.05sec", "A", "1sec", "B", "0.05sec"]) # Take the item from the pokemon
                            item_count -= 1
                        else:
                            emu_combo(["0.05sec", "Down"])
            emu_combo(["B", "1.5sec", "B"]) # Close out of menus
    except:
        debug_log.exception('')

def save_game(): # Function to save the game via the save option in the start menu
    try:
        debug_log.info("Saving the game...")

        i = 0
        start_menu("save")
        while i < 2:
            while not find_image("data/templates/start_menu/save/yes.png"):
                time.sleep(0.1/emu_speed)
            while find_image("data/templates/start_menu/save/yes.png"):
                emu_combo(["A", "0.5sec"])
                i += 1
        time.sleep(8/emu_speed) # Wait for game to save
    except:
        debug_log.exception('')

def identify_pokemon(starter: bool = False): # Identify opponent pokemon and incremement statistics, returns True if shiny, else False
    try:
        def common_stats():
            global stats, encounter_log
    
            stats["pokemon"][pokemon["name"]]["encounters"] += 1
            stats["pokemon"][pokemon["name"]]["phase_encounters"] += 1
            phase_encounters = stats["totals"]["phase_encounters"]
            total_encounters = stats["totals"]["encounters"] + stats["totals"]["shiny_encounters"]
            total_shiny_encounters = stats["totals"]["shiny_encounters"]
    
            if stats["pokemon"][pokemon["name"]]["phase_lowest_sv"] == "-": stats["pokemon"][pokemon["name"]]["phase_lowest_sv"] = pokemon["shinyValue"]
            else:
                if pokemon["shinyValue"] < stats["pokemon"][pokemon["name"]]["phase_lowest_sv"]: stats["pokemon"][pokemon["name"]]["phase_lowest_sv"] = pokemon["shinyValue"]

            if stats["pokemon"][pokemon["name"]]["total_lowest_sv"] == "-": stats["pokemon"][pokemon["name"]]["total_lowest_sv"] = pokemon["shinyValue"]
            else:
                if pokemon["shinyValue"] < stats["pokemon"][pokemon["name"]]["total_lowest_sv"]: stats["pokemon"][pokemon["name"]]["total_lowest_sv"] = pokemon["shinyValue"]
    
            if stats['pokemon'][pokemon['name']]['shiny_encounters'] > 0: shiny_average = f"1/{int(math.floor(stats['pokemon'][pokemon['name']]['encounters']/stats['pokemon'][pokemon['name']]['shiny_encounters'])):,}"
            else: shiny_average = "-"

            if total_shiny_encounters != 0 and stats['pokemon'][pokemon['name']]['encounters'] != 0: stats["totals"]["shiny_average"] = f"1/{int(math.floor(total_encounters/total_shiny_encounters)):,}"
            else: stats["totals"]["shiny_average"] = "-"
    
            log_obj = {
                "time_encountered": str(datetime.now()),
                "pokemon_obj": pokemon,
                "snapshot_stats": {
                    "phase_encounters": stats["totals"]["phase_encounters"],
                    "species_encounters": stats['pokemon'][pokemon['name']]['encounters'],
                    "species_shiny_encounters": stats['pokemon'][pokemon['name']]['shiny_encounters'],
                    "total_encounters": total_encounters,
                    "total_shiny_encounters": total_shiny_encounters,
                    "shiny_average": shiny_average
                }
            }

            if pokemon["shiny"]: shiny_log["shiny_log"].append(log_obj)
            encounter_log["encounter_log"].append(log_obj)
    
            stats["pokemon"][pokemon["name"]]["shiny_average"] = shiny_average
            encounter_log["encounter_log"] = encounter_log["encounter_log"][-config["encounter_log_limit"]:]
 
            if not args.n:
                write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file
                write_file("stats/encounter_log.json", json.dumps(encounter_log, indent=4, sort_keys=True)) # Save encounter log file
                write_file("stats/shiny_log.json", json.dumps(shiny_log, indent=4, sort_keys=True)) # Save shiny log file

                year, month, day, hour, minute, second = f"{datetime.now().year}", f"{(datetime.now().month):02}", f"{(datetime.now().day):02}", f"{(datetime.now().hour):02}", f"{(datetime.now().minute):02}", f"{(datetime.now().second):02}"
                if not args.n and not pokemon["shiny"] and "all_encounters" in config["log"]: # Log all encounters to a file
                    path = f"stats/encounters/Phase {total_shiny_encounters}/{pokemon['metLocationName']}/{year}-{month}-{day}/{pokemon['name']}/"
                    os.makedirs(path, exist_ok=True)
                    write_file(f"{path}SV_{pokemon['shinyValue']} ({hour}-{minute}-{second}).json", json.dumps(pokemon, indent=4, sort_keys=True))
                if pokemon["shiny"] and "shiny_encounters" in config["log"]: # Log shiny Pokemon to a file
                    path = f"stats/encounters/Shinies/"
                    os.makedirs(path, exist_ok=True)
                    write_file(f"{path}SV_{pokemon['shinyValue']} {pokemon['name']} ({hour}-{minute}-{second}).json", json.dumps(pokemon, indent=4, sort_keys=True))

            debug_log.info(f"Phase encounters: {phase_encounters} | {pokemon['name']} Phase Encounters: {stats['pokemon'][pokemon['name']]['phase_encounters']}")
            debug_log.info(f"{pokemon['name']} Encounters: {stats['pokemon'][pokemon['name']]['encounters']:,} | Lowest {pokemon['name']} SV seen this phase: {stats['pokemon'][pokemon['name']]['phase_lowest_sv']}")
            debug_log.info(f"Shiny {pokemon['name']} Encounters: {stats['pokemon'][pokemon['name']]['shiny_encounters']:,} | {pokemon['name']} Shiny Average: {shiny_average}")
            debug_log.info(f"Total Encounters: {total_encounters:,} | Total Shiny Encounters: {total_shiny_encounters:,} | Total Shiny Average: {stats['totals']['shiny_average']}")
            debug_log.info(f"------------------ {pokemon['name']} ------------------")

        debug_log.info("Identifying Pokemon...")
        release_all_inputs()

        if starter: time.sleep(0.5/emu_speed)
        else:
            i = 0
            while trainer_info["state"] not in [3, 255] and i < 250:
                press_button("B")
                i += 1
        if trainer_info["state"] == 80: return False

        if starter: pokemon = party_info[0]
        else: pokemon = opponent_info

        debug_log.info(f"------------------ {pokemon['name']} ------------------")
        debug_log.debug(pokemon)
        debug_log.info(f"Encountered a {pokemon['name']} at {pokemon['metLocationName']}")
        debug_log.info(f"HP: {pokemon['hpIV']} | ATK: {pokemon['attackIV']} | DEF: {pokemon['defenseIV']} | SPATK: {pokemon['spAttackIV']} | SPDEF: {pokemon['spDefenseIV']} | SPE: {pokemon['speedIV']}")
        debug_log.info(f"Shiny Value (SV): {pokemon['shinyValue']:,} (is {pokemon['shinyValue']:,} < 8 = {pokemon['shiny']})")

        if not pokemon["name"] in stats["pokemon"]: stats["pokemon"].update({pokemon["name"]: {"encounters": 0, "shiny_encounters": 0, "phase_lowest_sv": "-", "phase_encounters": 0, "shiny_average": "-", "total_lowest_sv": "-"}}) # Set up pokemon stats if first encounter

        if pokemon["shiny"]:
            debug_log.info("Shiny Pokemon detected!")

            if stats["totals"]["shortest_phase_encounters"] == "-": stats["totals"]["shortest_phase_encounters"] = stats["totals"]["phase_encounters"]
            elif stats["totals"]["shortest_phase_encounters"] > stats["totals"]["phase_encounters"]: stats["totals"]["shortest_phase_encounters"] = stats["totals"]["phase_encounters"]

            stats["pokemon"][pokemon["name"]]["shiny_encounters"] += 1
            stats["totals"]["shiny_encounters"] += 1
            common_stats()
            stats["totals"]["phase_encounters"] = 0
            stats["totals"]["phase_lowest_sv"] = "-"
            stats["totals"]["phase_lowest_sv_pokemon"] = ""

            for mon_name in stats["pokemon"]: # Reset phase stats
                stats["pokemon"][mon_name]["phase_lowest_sv"] = "-"
                stats["pokemon"][mon_name]["phase_encounters"] = 0

            if not args.n: write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file

            if not starter and config["bot_mode"] not in ["Manual Mode", "Rayquaza", "Kyogre", "Groudon"] and "shinies" in config["catch"]: catch_pokemon()

            if not args.n: write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file
            if config["manual_catch"]: os._exit(0)
            else: return True

        else:
            debug_log.info("Non shiny Pokemon detected...")
    
            stats["totals"]["encounters"] += 1
            stats["totals"]["phase_encounters"] += 1
    
            if stats["totals"]["phase_encounters"] > stats["totals"]["longest_phase_encounters"]: stats["totals"]["longest_phase_encounters"] = stats["totals"]["phase_encounters"]
            if stats["totals"]["phase_lowest_sv"] == "-": 
                stats["totals"]["phase_lowest_sv"] = pokemon["shinyValue"]
                stats["totals"]["phase_lowest_sv_pokemon"] = pokemon["name"]
            elif pokemon["shinyValue"] <= stats["totals"]["phase_lowest_sv"]:
                stats["totals"]["phase_lowest_sv"] = pokemon["shinyValue"]
                stats["totals"]["phase_lowest_sv_pokemon"] = pokemon["name"]
    
            common_stats()
    
            if config["bot_mode"] == "Manual Mode":
                while trainer_info["state"] != 80: time.sleep(1/emu_speed)
            elif not starter:
                if "perfect_ivs" in config["catch"] and pokemon["hpIV"] == 31 and pokemon["attackIV"] == 31 and pokemon["defenseIV"] == 31 and pokemon["speedIV"] == 31 and pokemon["spAttackIV"] == 31 and pokemon["spDefenseIV"] == 31: catch_pokemon()
                elif "zero_ivs" in config["catch"] and pokemon["hpIV"] == 0 and pokemon["attackIV"] == 0 and pokemon["defenseIV"] == 0 and pokemon["speedIV"] == 0 and pokemon["spAttackIV"] == 0 and pokemon["spDefenseIV"] == 0: catch_pokemon()

                ### Custom Filters ###
                # Add custom filters here (make sure to uncomment the line), examples:
                # If you want to STOP the bot instead of automatically catching, replace `catch_pokemon()` with `os._exit(0)`

                # --- Catch any species that the trainer has not already caught ---
                #elif pokemon["hasSpecies"] == 0: catch_pokemon()

                # --- Catch all Luvdisc with the held item "Heart Scale" ---
                #elif pokemon["name"] == "Luvdisc" and pokemon["itemName"] == "Heart Scale": catch_pokemon()

                # --- Catch Lonely natured Ralts with >25 attackIV and spAttackIV ---
                #elif pokemon["name"] == "Ralts" and pokemon["attackIV"] > 25 and pokemon["spAttackIV"] > 25 and pokemon["nature"] == "Lonely": catch_pokemon()

                elif "wild_pokemon" in config["battle"]: battle()
                else: flee_battle()
    
            return False
    except: debug_log.exception('')

def memGrabber(): # Loop repeatedly to read and write game information and inputs in memory
    try:
        global trainer_info, party_info, opponent_info, last_trainer_state, last_opponent_personality, emu_info, emu_speed

        pokemon_schema = json.loads(read_file("data/schemas/pokemon.json"))
        validate_pokemon = fastjsonschema.compile(pokemon_schema)
        trainer_info_schema = json.loads(read_file("data/schemas/trainer_info.json"))
        validate_trainer_info = fastjsonschema.compile(trainer_info_schema)
        emu_info_schema = json.loads(read_file("data/schemas/emu_info.json"))
        validate_emu_info = fastjsonschema.compile(emu_info_schema)

        def enrich_mon_data(pokemon: dict): # Function to add information to the pokemon data extracted from mGBA
            try:
                pokemon["name"] = pokemon["speciesName"].capitalize() # Capitalise name
                pokemon["metLocationName"] = location_list[pokemon["metLocation"]] # Add a human readable location
                pokemon["type"] = pokemon_list[pokemon["name"]]["type"] # Get pokemon types
                pokemon["nature"] = nature_list[pokemon["personality"] % 25] # Get pokemon nature
                pokemon["zeroPadNumber"] = f"{pokemon_list[pokemon['name']]['number']:03}" # Get zero pad number - e.g.: #5 becomes #005
                pokemon["itemName"] = item_list[pokemon['heldItem']] # Get held item's name
                pokemon["personalityBin"] = format(pokemon["personality"], "032b") # Convert personality ID to binary
                pokemon["personalityF"] = int(pokemon["personalityBin"][:16], 2) # Get first 16 bits of binary PID
                pokemon["personalityL"] = int(pokemon["personalityBin"][16:], 2) # Get last 16 bits of binary PID
                pokemon["shinyValue"] = int(bin(pokemon["personalityF"] ^ pokemon["personalityL"] ^ trainer_info["tid"] ^ trainer_info["sid"])[2:], 2) # https://bulbapedia.bulbagarden.net/wiki/Personality_value#Shininess

                if pokemon["shinyValue"] < 8: pokemon["shiny"] = True
                else: pokemon["shiny"] = False

                pokemon["enrichedMoves"] = []
                for move in pokemon["moves"]:
                    pokemon["enrichedMoves"].append(move_list[move])

                if pokemon["pokerus"] != 0: # TODO get number of days infectious, see - https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9rus#Technical_information
                    if pokemon["pokerus"] % 10: pokemon["pokerusStatus"] = "infected"
                    else: pokemon["pokerusStatus"] = "cured"
                else:
                    pokemon["pokerusStatus"] = "none"
                return pokemon
            except: pass

        while True:
            try:
                press_input_mmap.seek(0)
                press_input_mmap.write(bytes(json.dumps(press_input), encoding="utf-8"))
                hold_input_mmap.seek(0)
                hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

                trainer_info_mmap = load_json_mmap(4096, "bizhawk_trainer_info")
                if trainer_info_mmap:
                    if validate_trainer_info(trainer_info_mmap["trainer"]):
                        if trainer_info_mmap["trainer"]["posX"] < 0: trainer_info_mmap["trainer"]["posX"] = 0
                        if trainer_info_mmap["trainer"]["posY"] < 0: trainer_info_mmap["trainer"]["posY"] = 0
                        trainer_info = trainer_info_mmap["trainer"]

                party_info_mmap = load_json_mmap(8192, "bizhawk_party_info")
                if party_info_mmap:
                    enriched_party_obj = []
                    for pokemon in party_info_mmap["party"]:
                        if validate_pokemon(pokemon):
                            pokemon = enrich_mon_data(pokemon)
                            enriched_party_obj.append(pokemon)
                        else:
                            print(validate(pokemon, pokemon_schema))
                            continue
                    party_info = enriched_party_obj
                
                opponent_info_mmap = load_json_mmap(4096, "bizhawk_opponent_info")
                if config["bot_mode"] == "Starters": 
                    if party_info: opponent_info = party_info[0]
                elif opponent_info_mmap:
                    if validate_pokemon(opponent_info_mmap):
                        enriched_opponent_obj = enrich_mon_data(opponent_info_mmap["opponent"])
                        if enriched_opponent_obj:
                            opponent_info = enriched_opponent_obj
                elif not opponent_info: opponent_info = json.loads(read_file("data/placeholder_pokemon.json")) # TODO fix

                emu_info_mmap = load_json_mmap(4096, "bizhawk_emu_info")
                if emu_info_mmap:
                    if validate_emu_info(emu_info_mmap["emu"]):
                        emu_info = emu_info_mmap["emu"]
                        if emu_info_mmap["emu"]["emuFPS"]: emu_speed = emu_info_mmap["emu"]["emuFPS"]/60
            except:
                if args.d: debug_log.exception('')
                continue
    except:
        debug_log.exception('')
        pass

def httpServer(): # Run HTTP server to make data available via HTTP GET
    try:
        log = logging.getLogger('werkzeug')
        if not args.d: log.setLevel(logging.ERROR)

        server = Flask(__name__)
        CORS(server)

        @server.route('/trainer_info', methods=['GET'])
        def req_trainer_info():
            if trainer_info:
                response = jsonify(trainer_info)
                return response
            else: abort(503)
        @server.route('/party_info', methods=['GET'])
        def req_party_info():
            if party_info:
                response = jsonify(party_info)
                return response
            else: abort(503)
        @server.route('/opponent_info', methods=['GET'])
        def req_opponent_info():
            if opponent_info:
                if stats:
                    try: 
                        opponent_info["stats"] = stats["pokemon"][opponent_info["name"]]
                        response = jsonify(opponent_info)
                        return response
                    except: abort(503)
                else: response = jsonify(opponent_info)
                return response
            else: abort(503)
        @server.route('/emu_info', methods=['GET'])
        def req_emu_info():
            if emu_info:
                response = jsonify(emu_info)
                return response
            else: abort(503)
        @server.route('/stats', methods=['GET'])
        def req_stats():
            if stats:
                response = jsonify(stats)
                return response
            else: abort(503)
        @server.route('/encounter_log', methods=['GET'])
        def req_encounter_log():
            if encounter_log:
                response = jsonify(encounter_log)
                return response
            else: abort(503)
        #@server.route('/config', methods=['POST'])
        #def submit_config():
        #    debug_log.info(request.get_json()) # TODO HTTP config handler
        #    response = jsonify({})
        #    return response

        server.run(debug=False, threaded=True, host="127.0.0.1", port=6969)
    except: debug_log.exception('')

def mainLoop(): # 🔁 Main loop
    try:
        global last_opponent_personality, last_trainer_state
        if "save_game_on_start" in config["game_save"]: save_game()
        release_all_inputs()

        while True:
            if trainer_info and emu_info:
                if config["bot_mode"] == "Manual Mode":
                    while not opponent_changed(): time.sleep(0.2/emu_speed)
                    identify_pokemon()
                elif "pickup" in config["battle"]: pickup_items()

                # 🌸 Sweet scent method
                if config["bot_mode"] == "Sweet Scent":
                    debug_log.info(f"Using Sweet Scent...")
                    start_menu("pokemon")
                    press_button("A") # Select first pokemon in party
                    while not find_image("data/templates/sweet_scent.png"): press_button("Down") # Search for sweet scent in menu
                    emu_combo(["A", "5sec"]) # Select sweet scent and wait for animation
                    identify_pokemon()

                # 🚲 Bunny hop method
                if config["bot_mode"] == "Bunny Hop":
                    debug_log.info("Bunny hopping...")
                    i = 0
                    while not opponent_changed():
                        if i < 250:
                            hold_button("B")
                            time.sleep(0.01/emu_speed)
                        else: 
                            release_all_inputs()
                            time.sleep(0.1/emu_speed)
                            i = 0
                        i += 1
                    release_all_inputs()
                    identify_pokemon()

                # 🏃‍♂️🏄‍♂️ Run/Surf method
                if "Run/Surf" in config["bot_mode"]:
                    debug_log.info(f"Running/Surfing...")
                    while not opponent_changed():
                        if config["bot_mode"] == "Run/Surf between coords":
                            follow_path([(config["run_surf"]["coord1"][0], config["run_surf"]["coord1"][1]), (config["run_surf"]["coord2"][0], config["run_surf"]["coord2"][1])])
                        elif config["bot_mode"] == "Run/Surf until obstructed":
                            run_until_obstructed(config["obstructed_dir"][0])
                            run_until_obstructed(config["obstructed_dir"][1])
                    identify_pokemon()

                # 🐠 Fishing method
                if config["bot_mode"] == "Fishing":
                    debug_log.info(f"Fishing...")
                    emu_combo(["Select", "0.8sec"]) # Cast rod and wait for fishing animation
                    started_fishing = time.time()
                    while not opponent_changed(): # State 80 = overworld
                        if find_image("data/templates/oh_a_bite.png") or find_image("data/templates/on_the_hook.png"): emu_combo(["0.1sec", "A", "0.1sec"])
                        if find_image("data/templates/not_even_a_nibble.png") or find_image("data/templates/it_got_away.png"): emu_combo(["B", "0.1sec", "Select"])
                        if not find_image("data/templates/text_period.png"): emu_combo(["Select", "0.8sec"]) # Re-cast rod if the fishing text prompt is not visible
                    identify_pokemon()

                # ➕ Starters soft reset method
                if config["bot_mode"] == "Starters":
                    debug_log.info(f"Soft resetting starter Pokemon...")
                    release_all_inputs()
                    while trainer_info["state"] != 80: press_button("A") # State 80 = overworld

                    if read_file(f"stats/{trainer_info['tid']}.json"): starter_frames = json.loads(read_file(f"stats/{trainer_info['tid']}.json")) # Open starter frames file
                    else: starter_frames = {"rngState": {"Treecko": [], "Torchic": [], "Mudkip": []}}

                    while trainer_info["state"] == 80: press_button("A")
                    if config["starter_pokemon"] == "Mudkip":
                        while not find_image("data/templates/mudkip.png"): press_button("Right")
                    elif config["starter_pokemon"] == "Treecko":
                        while not find_image("data/templates/treecko.png"): press_button("Left")

                    while emu_info["rngState"] in starter_frames["rngState"][config["starter_pokemon"]]:
                        debug_log.debug(f"Already rolled on RNG state: {emu_info['rngState']}, waiting...")
                    else:
                        starter_frames["rngState"][config["starter_pokemon"]].append(emu_info["rngState"])
                        write_file(f"stats/{trainer_info['tid']}.json", json.dumps(starter_frames, indent=4, sort_keys=True))
                        while trainer_info["state"] == 255: press_button("A")
                        while not find_image("data/templates/battle/fight.png"):
                            release_all_inputs()
                            emu_combo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible
                        while True:
                            try:
                                if party_info[0]:
                                    if identify_pokemon(starter=True): os._exit(0) # Kill bot and wait for manual intervention to manually catch the shiny starter
                                    else:
                                        hold_button("Power")
                                        time.sleep(0.5/emu_speed)
                                        break
                            except: continue

                # 🐍 Rayquaza method
                if config["bot_mode"] == "Rayquaza":
                    if trainer_info["mapBank"] == 24 and trainer_info["mapId"] == 85 and trainer_info["posX"] == 14 and trainer_info["posY"] <= 12:  # 24:85 Top of Sky Pillar in front of Rayquaza
                        while True:
                            emu_combo(["A", "Up"])
                            if trainer_info["posY"] < 7:
                                break
                            if trainer_info["state"] != 80:
                                if opponent_changed():
                                    if identify_pokemon(): os._exit(0) # Kill bot and wait for manual intervention to manually catch Rayquaza
                                break

                        time.sleep(1/emu_speed)
                        press_button("B")

                        follow_path([(14, 11), (12, 11), (12, 15), (16, 15), (16, -99, (24, 84)), (10, -99, (24, 85)), (12, 15), (12, 11), (14, 11), (14, 7)])

                # 🌋 Groudon method
                if config["bot_mode"] == "Groudon":
                    if trainer_info["mapBank"] == 24 and trainer_info["mapId"] == 105 and 11 <= trainer_info["posX"] <= 20 and 26 <= trainer_info["posY"] <= 27:  # 24:105 Terra Cave in front of Groudon
                        while True:
                            follow_path([(trainer_info["posX"], 26), (17, 26), (7, 26), (7, 15), (9, 15), (9, 4), (5, 4), (5, 99, (24, 104)), (14, -99, (24, 105)), (9, 4), (9, 15), (7, 15), (7, 26), (11, 26)])

                # 🌊 Kyogre method
                if config["bot_mode"] == "Kyogre":
                    if trainer_info["mapBank"] == 24 and trainer_info["mapId"] == 103 and 5 <= trainer_info["posX"] <= 14 and 26 <= trainer_info["posY"] <= 27:  # 24:103 Marine Cave in front of Kyogre
                        while True:
                            follow_path([(trainer_info["posX"], 26), (9, 26), (9, 27), (18, 27), (18, 14), (14, 14), (14, 4), (20, 4), (20, 99, (24, 102)), (14, -99, (24, 103)), (14, 4), (14, 14), (18, 14), (18, 27), (14, 27)])

                # 🧭 Southern Island method
                if config["bot_mode"] == "Southern Island":
                    if trainer_info["mapBank"] == 26 and trainer_info["mapId"] == 10 and 5 <= trainer_info["posX"] == 13 and trainer_info["posY"] >= 12:  # 26:10 Southern Island, facing the sphere
                        while True:
                            follow_path([(13, 99, (26, 9)), (14, -99, (26, 10))])
                            i = 0
                            while not opponent_changed():
                                if i < 500:
                                    follow_path([(13, 12)])
                                    emu_combo(["A", "1sec"])
                                    if find_image("data/templates/dreams.png"):
                                        press_button("B")
                                        break
                                    i += 1
                                else: break
                            else: identify_pokemon()

                # TODO fix Buy 10x pokeballs method
                #if config["bot_mode"] == "Buy Premier Balls": while True: emu_combo(["A", "1sec", "Right", "Down", "A", "1sec", "A", "0.8sec", "A", "0.8sec", "A"])
            else:
                debug_log.info("Waiting for initial information from Bizhawk script...")
                debug_log.debug(f"Trainer info: {trainer_info}")
                debug_log.debug(f"Party info: {trainer_info}")
                debug_log.debug(f"Opponent info: {opponent_info}")
                debug_log.debug(f"Emu info: {emu_info}")
                if trainer_info: last_trainer_state = trainer_info["state"]
                if opponent_info: last_opponent_personality = opponent_info["personality"]
                release_all_inputs()
                time.sleep(0.2)
    except:
        debug_log.exception('')

try:
    # Parse flags to change the behaviour of the bot
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', action='store_true')  # -n flag: "no stats mode" set to NOT save statistics or log encounters to file
    parser.add_argument('-s', action='store_true')  # -s flag: save the game after starting bot
    parser.add_argument('-m', action='store_true')  # -m flag: set to Manual Mode (bot will check for shinies and update stats without providing any button input)
    parser.add_argument('-d', action='store_true')  # -d flag: enable general debug logging
    parser.add_argument('-di', action='store_true') # -di flag: enable on-screen image detection debugging
    parser.add_argument('-dm', action='store_true') # -dm flag: enable memory debug logging
    args = parser.parse_args()
    if args.di or args.dm: args.d = True

    # Set up log handler
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(line:%(lineno)d) %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(message)s')
    path = "logs"
    logFile = f"{path}/debug.log"
    os.makedirs(path, exist_ok=True) # Create logs directory if not exist

    # Set up log file rotation handler
    log_handler = RotatingFileHandler(logFile, mode='a', maxBytes=20*1024*1024, backupCount=5, encoding=None, delay=0)
    log_handler.setFormatter(log_formatter)
    if args.d: log_handler.setLevel(logging.DEBUG)
    else: log_handler.setLevel(logging.INFO)

    # Set up console log stream handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Create logger and attach handlers
    debug_log = logging.getLogger('root')
    debug_log.setLevel(logging.DEBUG)
    debug_log.addHandler(log_handler)
    debug_log.addHandler(console_handler)
except Exception as e:
    print(e)
    os._exit(1)

try:
    yaml = YAML()
    yaml.default_flow_style = False

    config = yaml.load(read_file("config.yml")) # Load config

    if args.s: config["game_save"].append("save_game_on_start")
    if args.m: config["bot_mode"] = "Manual Mode"

    debug_log.info("Starting bot!")
    debug_log.info(f"Mode: {config['bot_mode']}")

    item_list = json.loads(read_file("data/items.json"))
    location_list = json.loads(read_file("data/locations.json"))
    move_list = json.loads(read_file("data/moves.json"))
    pokemon_list = json.loads(read_file("data/pokemon.json"))
    type_list = json.loads(read_file("data/types.json"))
    nature_list = json.loads(read_file("data/natures.json"))

    os.makedirs("stats", exist_ok=True) # Sets up stats files if they don't exist
    if read_file("stats/totals.json"): stats = json.loads(read_file("stats/totals.json")) # Open totals stats file
    else: stats = {"pokemon": {}, "totals": {"longest_phase_encounters": 0, "shortest_phase_encounters": "-", "phase_lowest_sv": 99999, "phase_lowest_sv_pokemon": "", "encounters": 0, "phase_encounters": 0, "shiny_average": "-", "shiny_encounters": 0}}

    if read_file("stats/encounter_log.json"): encounter_log = json.loads(read_file("stats/encounter_log.json")) # Open encounter log file
    else: encounter_log = {"encounter_log": []}

    if read_file("stats/shiny_log.json"): shiny_log = json.loads(read_file("stats/shiny_log.json")) # Open shiny log file
    else: shiny_log = {"shiny_log": []}

    default_input = {"A": False, "B": False, "L": False, "R": False, "Up": False, "Down": False, "Left": False, "Right": False, "Select": False, "Start": False, "Light Sensor": 0, "Power": False, "Tilt X": 0, "Tilt Y": 0, "Tilt Z": 0, "Screenshot": False}
    press_input_mmap = mmap.mmap(-1, 256, tagname="bizhawk_press_input", access=mmap.ACCESS_WRITE)
    press_input = default_input
    hold_input_mmap = mmap.mmap(-1, 256, tagname="bizhawk_hold_input", access=mmap.ACCESS_WRITE)
    hold_input = default_input

    last_trainer_state, last_opponent_personality, trainer_info, opponent_info, emu_info, party_info, emu_speed = None, None, None, None, None, None, 1
    mmap_screenshot_size, mmap_screenshot_file = 12288, "bizhawk_screenshot"
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    def on_window_close(): os._exit(1)
    window = webview.create_window("PokeBot", url="interface/dashboard.html", width=1280, height=720, resizable=True, hidden=False, frameless=False, easy_drag=True, fullscreen=False, text_select=True, zoomable=True)
    window.events.closed += on_window_close

    # Set up and launch threads if screenshot is detected in memory (Lua script is running in Bizhawk)
    if mmap.mmap(0, mmap_screenshot_size, mmap_screenshot_file):
        mem_grabber = Thread(target=memGrabber)
        mem_grabber.start()

        http_server = Thread(target=httpServer)
        http_server.start()

        main_thread = Thread(target=mainLoop)
        main_thread.start()

        webview.start()
except Exception as e:
    print(e)
    debug_log.exception('')
    os._exit(1)
