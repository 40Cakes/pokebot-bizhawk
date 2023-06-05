# Import modules
import io                                        # https://docs.python.org/3/library/io.html
import os                                        # https://docs.python.org/3/library/os.html
import re                                        # https://docs.python.org/3/library/re.html
import array                                     # https://docs.python.org/3/library/array.html
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
# Helper functions
from data.HiddenPower import calculate_hidden_power
from data.GameState import GameState
from data.MapData import mapRSE #mapFRLG
# Data processing
import pandas as pd

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
def language_id_to_iso_639(lang: int):
    match lang:
        case 1: return "en"
        case 2: return "jp"
        case 3: return "fr"
        case 4: return "es"
        case 5: return "de"
        case 6: return "it"

@staticmethod
def wait_frames(frames):
    time.sleep(frames_to_ms(frames))

@staticmethod
def emu_combo(sequence: list): # Function to send a sequence of inputs and delays to the emulator
    for k in sequence:
        if type(k) is int:
            wait_frames(k)
        else:
            press_button(k)
            wait_frames(1)

@staticmethod
def read_file(file: str): # Simple function to read data from a file, return False if file doesn't exist
    if os.path.exists(file):
        with open(file, mode="r", encoding="utf-8") as open_file:
            return open_file.read()
    else:
        return False

@staticmethod
def write_file(file: str, value: str, mode: str = "w"): # Simple function to write data to a file, will create the file if doesn't exist
    dirname = os.path.dirname(file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(file, mode=mode, encoding="utf-8") as save_file:
        save_file.write(value)
        return True

def player_on_map(map_data: tuple):
    on_map = trainer_info["mapBank"] == map_data[0] and trainer_info["mapId"] == map_data[1]

    if not on_map and args.d:
        debug_log.info(f"Player was not on target map of {map_data[0]},{map_data[1]}. Map was {trainer_info['mapBank']}, {trainer_info['mapId']}")

    return on_map

def load_json_mmap(size, file): 
    # Loads a JSON object from a memory mapped file
    # BizHawk writes game information to memory mapped files every few frames (see pokebot.lua)
    # See https://tasvideos.org/Bizhawk/LuaFunctions (comm.mmfWrite)
    try:
        shmem = mmap.mmap(0, size, file)
        if shmem:
            bytes_io = io.BytesIO(shmem)
            byte_str = bytes_io.read()
            json_obj = json.loads(byte_str.decode("utf-8").split("\x00")[0]) # Only grab the data before \x00 null chars

            if args.dm: 
                debug_log.debug(f"Attempting to read {file} ({size} bytes) from memory...")
                debug_log.debug(f"Byte string: {byte_str}")
                debug_log.debug(f"JSON result: {json_obj}")
            return json_obj
        else: return False
    except Exception as e:
        if args.dm: debug_log.exception(str(e))
        return False

def frames_to_ms(frames: float):
    return max((frames/60.0) / emu_speed, 0.02)

def press_button(button: str): # Function to update the press_input object
    global g_current_index

    match button:
        case 'Left':
            button = 'l'
        case 'Right':
            button = 'r'
        case 'Up':
            button = 'u'
        case 'Down':
            button = 'd'
        case 'Select':
            button = 's'
        case 'Start':
            button = 'S'

    index = g_current_index
    input_list_mmap.seek(index)
    input_list_mmap.write(bytes(button, encoding="utf-8"))
    input_list_mmap.seek(100) #Position 0-99 are inputs, position 100 keeps the value of the current index
    input_list_mmap.write(bytes([index+1]))

    g_current_index +=1
    if g_current_index > 99:
        g_current_index = 0

def hold_button(button: str): # Function to update the hold_input object
    global hold_input
    debug_log.debug(f"Holding: {button}...")

    hold_input[button] = True
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

def release_button(button: str): # Function to update the hold_input object
    global hold_input
    debug_log.debug(f"Releasing: {button}...")

    hold_input[button] = False
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

def release_all_inputs(): # Function to release all keys in all input objects
    global press_input, hold_input
    debug_log.debug(f"Releasing all inputs...")

    for button in ["A", "B", "L", "R", "Up", "Down", "Left", "Right", "Select", "Start", "Power"]:
        hold_input[button] = False
        hold_input_mmap.seek(0)
        hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

def opponent_changed(): # This function checks if there is a different opponent since last check, indicating the game state is probably now in a battle
    try:
        global last_opponent_personality

        # Fixes a bug where the bot checks the opponent for up to 20 seconds if it was last closed in a battle
        if trainer_info["state"] == GameState.OVERWORLD:
            return False

        if opponent_info and last_opponent_personality != opponent_info["personality"]:
            debug_log.info(f"Opponent has changed! Previous PID: {last_opponent_personality}, New PID: {opponent_info['personality']}")
            last_opponent_personality = opponent_info["personality"]
            return True    
    except Exception as e:
        if args.d: debug_log.exception(str(e))
        return False

def get_screenshot():
    g_bizhawk_screenshot = None
    hold_button("Screenshot")
    time.sleep(max((1/max(emu_speed,1))*0.016,0.002)) # Give emulator time to produce a screenshot
    try:
        shmem = mmap.mmap(0, mmap_screenshot_size, mmap_screenshot_file)
        screenshot = Image.open(io.BytesIO(shmem))
        g_bizhawk_screenshot = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_BGR2RGB) # Convert screenshot to numpy array COLOR_BGR2RGB
        screenshot.close()
    except:
        if screenshot is not None:
            screenshot.close()
        if args.dm:
            debug_log.exception('')
        release_button("Screenshot")
        return None
    release_button("Screenshot")

    if args.di:
        cv2.imshow("get_screenshot",g_bizhawk_screenshot)
        cv2.waitKey(1)
    
    return g_bizhawk_screenshot

def mem_pollScreenshot():
    global g_bizhawk_screenshot
    while True:
        hold_button("Screenshot")
        time.sleep(max((1/max(emu_speed,1))*0.016,0.002)) # Give emulator time to produce a screenshot
        try:
            shmem = mmap.mmap(0, mmap_screenshot_size, mmap_screenshot_file)
            screenshot = Image.open(io.BytesIO(shmem))
            g_bizhawk_screenshot = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_BGR2RGB) # Convert screenshot to numpy array COLOR_BGR2RGB
            screenshot.close()
        except Exception as e:
            if screenshot is not None:
                screenshot.close()
            if args.dm:
                debug_log.exception(str(e))
            continue
        release_button("Screenshot")
        if args.di:
            cv2.imshow("pollScreenShotData",g_bizhawk_screenshot)
            cv2.waitKey(1)

def find_image(file: str): # Function to find an image in a BizHawk screenshot
    try:
        profile_start = time.time() # Performance profiling
        threshold = 0.999
        if args.di: debug_log.debug(f"Searching for image {file} (threshold: {threshold})")
        template = cv2.imread(f"data/templates/{language}/" + file, cv2.IMREAD_UNCHANGED)
        hh, ww = template.shape[:2]
    
        correlation = cv2.matchTemplate(g_bizhawk_screenshot, template[:,:,0:3], cv2.TM_CCORR_NORMED) # Do masked template matching and save correlation image
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(correlation)
        max_val_corr = float('{:.6f}'.format(max_val))
        if args.di:
            debug_log.debug(f"Image detection took: {(time.time() - profile_start)*1000} ms")
            cv2.imshow("screenshot", g_bizhawk_screenshot)
            cv2.waitKey(1)
        if max_val_corr > threshold: 
            if args.di:
                loc = numpy.where(correlation >= threshold)
                result = g_bizhawk_screenshot.copy()
                for point in zip(*loc[::-1]):
                    cv2.rectangle(result, point, (point[0]+ww, point[1]+hh), (0,0,255), 1)
                    cv2.imshow(f"match", result)
                    cv2.waitKey(1)
            if args.di: debug_log.debug(f"Maximum correlation value ({max_val_corr}) is above threshold ({threshold}), file {file} was on-screen!")
            return True
        else:
            if args.di: debug_log.debug(f"Maximum correlation value ({max_val_corr}) is below threshold ({threshold}), file {file} was not detected on-screen.")
            return False
        
    except Exception as e:
        if args.di: debug_log.exception(str(e))
        return False

def catch_pokemon(): # Function to catch pokemon
    try:
        while not find_image("battle/fight.png"):
            release_all_inputs()
            emu_combo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible
        
        if config["manual_catch"]:
            input("Pausing bot for manual catch (don't forget to pause pokebot.lua script so you can provide inputs). Press Enter to continue...")
            return True
        else:
            debug_log.info("Attempting to catch Pokemon...")
        
        if config["use_spore"]: # Use Spore to put opponent to sleep to make catches much easier
            debug_log.info("Attempting to sleep the opponent...")
            i, spore_pp = 0, 0
            
            ability = opponent_info["ability"][opponent_info["altAbility"]]
            can_spore = ability not in no_sleep_abilities

            if (opponent_info["status"] == 0) and can_spore:
                for move in party_info[0]["enrichedMoves"]:
                    if move["name"] == "Spore":
                        spore_pp = move["pp"]
                        spore_move_num = i
                    i += 1

                if spore_pp != 0:
                    emu_combo(["A", 15])
                    if spore_move_num == 0: seq = ["Up", "Left"]
                    elif spore_move_num == 1: seq = ["Up", "Right"]
                    elif spore_move_num == 2: seq = ["Left", "Down"]
                    elif spore_move_num == 3: seq = ["Right", "Down"]

                    while not find_image("spore.png"):
                        emu_combo(seq)

                    emu_combo(["A", 240]) # Select move and wait for animations
            elif not can_spore:
                debug_log.info(f"Can't sleep the opponent! Ability is {ability}")

            while not find_image("battle/bag.png"): 
                release_all_inputs()
                emu_combo(["B", "Up", "Right"]) # Press B + up + right until BAG menu is visible

        while True:
            if find_image("battle/bag.png"): press_button("A")

            # TODO Safari Zone
            #if opponent_info["metLocationName"] == "Safari Zone":
            #    while not find_image("battle/safari_zone/ball.png"):
            #        if trainer_info["state"] == GameState.OVERWORLD:
            #            return False
            #        emu_combo(["B", "Up", "Left"]) # Press B + up + left until BALL menu is visible

            # Preferred ball order to catch wild mons + exceptions 
            # TODO read this data from memory instead
            if trainer_info["state"] == GameState.BAG_MENU:
                can_catch = False

                # Check if current species has a preferred ball
                foe_name = opponent_info["speciesName"]
                if foe_name in config["pokeball_override"]:
                    species_rule = config["pokeball_override"][foe_name]
                    
                    for ball in species_rule:
                        if bag_menu(category="pokeballs", item=ball):
                            can_catch = True
                            break

                # Check global pokeball priority 
                if not can_catch:
                    for ball in config["pokeball_priority"]:
                        if bag_menu(category="pokeballs", item=ball):
                            can_catch = True
                            break

                if not can_catch:
                    debug_log.info("No balls to catch the Pokemon found. Killing the script!")
                    os._exit(1)

            if find_image("gotcha.png"): # Check for gotcha! text when a pokemon is successfully caught
                debug_log.info("Pokemon caught!")

                while trainer_info["state"] != GameState.OVERWORLD:
                    press_button("B")

                wait_frames(120) # Wait for animations
                
                if config["save_game_after_catch"]: 
                    save_game()
                
                return True

            if trainer_info["state"] == GameState.OVERWORLD:
                return False
    except Exception as e:
        if args.di: debug_log.exception(str(e))
        return False

def battle(): # Function to battle wild pokemon
    # This will only battle with the lead pokemon of the party, and will run if it dies or runs out of PP
    ally_fainted = False
    foe_fainted = False

    while not ally_fainted and not foe_fainted and trainer_info["state"] != GameState.OVERWORLD:
        debug_log.info("Navigating to the FIGHT button...")

        while not find_image("battle/fight.png") and trainer_info["state"] != GameState.OVERWORLD:
            emu_combo(["B", 10, "Up", 10, "Left", 10]) # Press B + up + left until FIGHT menu is visible
        
        if trainer_info["state"] == GameState.OVERWORLD:
            return True

        best_move = find_effective_move(party_info[0], opponent_info)
        
        if best_move["power"] <= 10:
            debug_log.info("Lead Pokemon has no effective moves to battle the foe!")
            flee_battle()
            return False
        
        press_button("A")

        wait_frames(5)

        debug_log.info(f"Best move against foe is {best_move['name']} (Effective power is {best_move['power']})")

        i = int(best_move["index"])

        if i == 0:
            emu_combo(["Up", "Left"])
        elif i == 1:
            emu_combo(["Up", "Right"])
        elif i == 2:
            emu_combo(["Down", "Left"])
        elif i == 3:
            emu_combo(["Down", "Right"])
        
        press_button("A")

        wait_frames(5)

        while trainer_info["state"] != GameState.OVERWORLD and not find_image("battle/fight.png"):
            press_button("B")
            wait_frames(1)
        
        ally_fainted = party_info[0]["hp"] == 0
        foe_fainted = opponent_info["hp"] == 0
    
    if ally_fainted:
        debug_log.info("Lead Pokemon fainted!")
        flee_battle()
        return False
    elif foe_fainted:
        debug_log.info("Battle won!")
        return True
    return True

def is_valid_move(move: dict):
    return not move["name"] in config["banned_moves"] and move["power"] > 0

def find_effective_move(ally: dict, foe: dict):
    i = 0
    move_power = []

    for move in ally["enrichedMoves"]:
        power = move["power"]

        # Ignore banned moves and those with 0 PP
        if not is_valid_move(move) or ally["pp"][i] == 0:
            move_power.append(0)
            i += 1
            continue

        # Calculate effectiveness against opponent's type(s)
        matchups = type_list[move["type"]]

        for foe_type in foe["type"]:
            if foe_type in matchups["immunes"]:
                power *= 0
            elif foe_type in matchups["weaknesses"]:
                power *= 0.5
            elif foe_type in matchups["strengths"]:
                power *= 2

        # STAB
        for ally_type in ally["type"]:
            if ally_type == move["type"]:
                power *= 1.5

        move_power.append(power)
        i += 1

    # Return info on the best move
    move_idx = move_power.index(max(move_power))
    return {
        "name": ally["enrichedMoves"][move_idx]["name"],
        "index": move_idx,
        "power": max(move_power)
    }

def flee_battle(): # Function to run from wild pokemon
    try:
        debug_log.info("Running from battle...")
        while trainer_info["state"] != GameState.OVERWORLD:
            while not find_image("battle/run.png") and trainer_info["state"] != GameState.OVERWORLD: 
                emu_combo(["Right", 5, "Down", "B", 5])
            while find_image("battle/run.png") and trainer_info["state"] != GameState.OVERWORLD: 
                press_button("A")
            press_button("B")
        wait_frames(30) # Wait for battle fade animation
    except Exception as e:
        if args.d: debug_log.exception(str(e))

def run_until_obstructed(direction: str, run: bool = True): # Function to run until trainer position stops changing
    press_button("B") # press and release B in case of a random pokenav call

    hold_button(direction)
    last_x = trainer_info["posX"]
    last_y = trainer_info["posY"]

    if run: move_speed = 8
    else: move_speed = 16

    dir_unchanged = 0
    while dir_unchanged < move_speed:
        if run: 
            hold_button("B")
        
        wait_frames(1)

        if last_x == trainer_info["posX"] and last_y == trainer_info["posY"]: 
            dir_unchanged += 1
            continue

        last_x = trainer_info["posX"]
        last_y = trainer_info["posY"]
        dir_unchanged = 0

        if opponent_changed():
            return None

    release_all_inputs()
    wait_frames(1)
    press_button("B")
    wait_frames(1)

    return [last_x, last_y]

def follow_path(coords: list, run: bool = True, exit_when_stuck: bool = False):
    possibly_stuck = False
    direction = None

    for x, y, *map_data in coords:
        debug_log.info(f"Moving to: {x}, {y}")

        stuck_time = 0
        last_pos = [0, 0]

        if run:
            hold_button("B")

        while True:
            if direction != None:
                release_button(direction)

            if opponent_changed():
                return

            last_pos = [trainer_info["posX"], trainer_info["posY"]]

            if map_data != []:
                # On map change
                if (trainer_info["mapBank"] == map_data[0][0] and trainer_info["mapId"] == map_data[0][1]):
                    break
            elif last_pos[0] == x and last_pos[1] == y:
                break
            
            if trainer_info["posX"] > x:
                direction = "Left"
            elif trainer_info["posX"] < x:
                direction = "Right"
            elif trainer_info["posY"] < y:
                direction = "Down"
            elif trainer_info["posY"] > y:
                direction = "Up"

            if trainer_info["posX"] == last_pos[0] and trainer_info["posY"] == last_pos[1]:
                stuck_time += 1

                if stuck_time == 120:
                    debug_log.info("Bot hasn't moved for a while. Is it stuck?")
                    
                    if exit_when_stuck:
                        release_all_inputs()
                        return False

                # Press B occasionally in case there's a menu/dialogue open
                if stuck_time % 120 == 0:
                    release_button("B")
                    wait_frames(1)
                    press_button("B")
            else:
                stuck_time = 0

            hold_button(direction)
            wait_frames(1)

    release_all_inputs()
    return True

def start_menu(entry: str): # Function to open any start menu item - presses START, finds the menu entry and opens it
    if not entry in ["bag", "bot", "exit", "option", "pokedex", "pokemon", "pokenav", "save"]:
        return False

    debug_log.info(f"Opening start menu entry: {entry}")
    filename = f"start_menu/{entry.lower()}.png"
    
    release_all_inputs()

    while not find_image("start_menu/select.png"):
        emu_combo(["B", "Start"])
        
        for i in range(0, 10):
            if find_image("start_menu/select.png"):
                break
            wait_frames(1)

    wait_frames(5)

    while not find_image(filename): # Find menu entry
        emu_combo(["Down", 10])

    while find_image(filename): # Press menu entry
        emu_combo(["A", 10])

def bag_menu(category: str, item: str): # Function to find an item in the bag and use item in battle such as a pokeball
    if not category in ["berries", "items", "key_items", "pokeballs", "tms&hms"]:
        return False

    debug_log.info(f"Scrolling to bag category: {category}...")

    while not find_image(f"start_menu/bag/{category.lower()}.png"):
        emu_combo(["Right", 25]) # Press right until the correct category is selected

    wait_frames(60) # Wait for animations

    debug_log.info(f"Scanning for item: {item}...")
    
    i = 0
    while not find_image(f"start_menu/bag/items/{item}.png") and i < 50:
        if i < 25: emu_combo(["Down", 15])
        else: emu_combo(["Up", 15])
        i += 1

    if find_image(f"start_menu/bag/items/{item}.png"):
        debug_log.info(f"Using item: {item}...")
        while trainer_info["state"] == GameState.BAG_MENU: 
            emu_combo(["A", 30]) # Press A to use the item
        return True
    else:
        return False

def pickup_items(): # If using a team of Pokemon with the ability "pickup", this function will take the items from the pokemon in your party if 3 or more Pokemon have an item
    if trainer_info["state"] != GameState.OVERWORLD:
        return

    item_count = 0
    pickup_mon_count = 0
    party_size = len(party_info)

    i = 0
    while i < party_size:
        pokemon = party_info[i]
        held_item = pokemon['heldItem']

        if pokemon["speciesName"] in pickup_pokemon:
            if held_item != 0:
                item_count += 1

            pickup_mon_count += 1
            debug_log.info(f"Pokemon {i}: {pokemon['speciesName']} has item: {item_list[held_item]}")

        i += 1

    if item_count < config["pickup_threshold"]:
        debug_log.info(f"Party has {item_count} item(s), won't collect until at threshold {config['pickup_threshold']}")
        return

    wait_frames(60) # Wait for animations
    start_menu("pokemon") # Open Pokemon menu
    wait_frames(65)

    i = 0
    while i < party_size:
        pokemon = party_info[i]
        if pokemon["speciesName"] in pickup_pokemon and pokemon["heldItem"] != 0:
            # Take the item from the pokemon
            emu_combo(["A", 15, "Up", 15, "Up", 15, "A", 15, "Down", 15, "A", 75, "B"])
            item_count -= 1
        
        if item_count == 0:
            break

        emu_combo([15, "Down", 15])
        i += 1

    # Close out of menus
    for i in range(0, 5):
        press_button("B")
        wait_frames(20)

def save_game(): # Function to save the game via the save option in the start menu
    try:
        debug_log.info("Saving the game...")

        i = 0
        start_menu("save")
        while i < 2:
            while not find_image("start_menu/save/yes.png"):
                wait_frames(10)
            while find_image("start_menu/save/yes.png"):
                emu_combo(["A", 30])
                i += 1
        wait_frames(500) # Wait for game to save
    except Exception as e:
        if args.dm: debug_log.exception(str(e))

def reset_game():
    debug_log.info("Resetting...")
    hold_button("Power")
    wait_frames(60)
    release_button("Power")

def log_encounter(pokemon: dict):
    global opponent_info, last_opponent_personality

    mon_sv = pokemon["shinyValue"]
    mon_name = pokemon["name"]

    # Show Gift Pokemon as the current encounter
    if last_opponent_personality != pokemon["personality"]:
        opponent_info = pokemon
        last_opponent_personality = pokemon["personality"]

    def common_stats():
        global stats, encounter_log

        mon_stats = stats["pokemon"][mon_name]
        total_stats = stats["totals"]

        mon_stats["encounters"] += 1
        mon_stats["phase_encounters"] += 1

        # Update encounter stats
        phase_encounters = total_stats["phase_encounters"]
        total_encounters = total_stats["encounters"] + total_stats["shiny_encounters"]
        total_shiny_encounters = total_stats["shiny_encounters"]

        # Log lowest Shiny Value
        if mon_stats["phase_lowest_sv"] == "-": 
            mon_stats["phase_lowest_sv"] = mon_sv
        else:
            mon_stats["phase_lowest_sv"] = min(mon_sv, mon_stats["phase_lowest_sv"])

        if mon_stats["total_lowest_sv"] == "-": 
            mon_stats["total_lowest_sv"] = mon_sv
        else:
            mon_stats["total_lowest_sv"] = min(mon_sv, mon_stats["total_lowest_sv"])

        # Log shiny average
        if mon_stats['shiny_encounters'] > 0: 
            avg = int(math.floor(mon_stats['encounters']/mon_stats['shiny_encounters']))
            shiny_average = f"1/{avg:,}"
        else: 
            shiny_average = "-"

        if total_shiny_encounters != 0 and mon_stats['encounters'] != 0: 
            avg = int(math.floor(total_encounters/total_shiny_encounters))
            total_stats["shiny_average"] = f"1/{avg:,}"
        else: 
            total_stats["shiny_average"] = "-"

        log_obj = {
            "time_encountered": str(datetime.now()),
            "pokemon_obj": pokemon,
            "snapshot_stats": {
                "phase_encounters": total_stats["phase_encounters"],
                "species_encounters": mon_stats['encounters'],
                "species_shiny_encounters": mon_stats['shiny_encounters'],
                "total_encounters": total_encounters,
                "total_shiny_encounters": total_shiny_encounters,
                "shiny_average": shiny_average
            }
        }

        if pokemon["shiny"]: 
            shiny_log["shiny_log"].append(log_obj)

        encounter_log["encounter_log"].append(log_obj)

        mon_stats["shiny_average"] = shiny_average
        encounter_log["encounter_log"] = encounter_log["encounter_log"][-config["encounter_log_limit"]:]

        write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file
        write_file("stats/encounter_log.json", json.dumps(encounter_log, indent=4, sort_keys=True)) # Save encounter log file
        write_file("stats/shiny_log.json", json.dumps(shiny_log, indent=4, sort_keys=True)) # Save shiny log file

        now = datetime.now()
        year, month, day, hour, minute, second = f"{now.year}", f"{(now.month):02}", f"{(now.day):02}", f"{(now.hour):02}", f"{(now.minute):02}", f"{(now.second):02}"
            
        if "all_encounters" in config["log"]: 
            # Log all encounters to a file
            jsonpath = f"stats/encounters/Phase {total_shiny_encounters}/{pokemon['metLocationName']}/{year}-{month}-{day}/{pokemon['name']}/"
            csvpath = f"stats/encounters/Phase {total_shiny_encounters}/"
            os.makedirs(jsonpath, exist_ok=True)
            os.makedirs(csvpath, exist_ok=True)
            if config["jsonlog"]:
                write_file(f"{jsonpath}SV_{pokemon['shinyValue']} ({hour}-{minute}-{second}).json", json.dumps(pokemon, indent=4, sort_keys=True))
            if config["csvlog"]:
                pokemondata = pd.DataFrame.from_dict(pokemon, orient = 'index').drop(['enrichedMoves', 'moves', 'pp', 'type']).sort_index().transpose()
                if os.path.exists(f"{csvpath}Encounters.csv"):
                    pokemondata.to_csv(f"{csvpath}Encounters.csv", mode='a', encoding='utf-8',index=False, header=False)
                else:
                    pokemondata.to_csv(f"{csvpath}Encounters.csv", mode='a', encoding='utf-8',index=False)
        if pokemon["shiny"] and "shiny_encounters" in config["log"]: # Log shiny Pokemon to a file
            path = f"stats/encounters/Shinies/"
            os.makedirs(path, exist_ok=True)
            if config["jsonlog"]:
                write_file(f"{path}SV_{pokemon['shinyValue']} {pokemon['name']} ({hour}-{minute}-{second}).json", json.dumps(pokemon, indent=4, sort_keys=True))
            if config["csvlog"]:
                pokemondata = pd.DataFrame.from_dict(pokemon, orient = 'index').drop(['enrichedMoves', 'moves', 'pp', 'type']).sort_index().transpose()
                if os.path.exists(f"{path}Encounters.csv"):
                    pokemondata.to_csv(f"{path}Encounters.csv", mode='a', encoding='utf-8',index=False, header=False)
                else:
                    pokemondata.to_csv(f"{path}Encounters.csv", mode='a', encoding='utf-8',index=False)

        debug_log.info(f"Phase encounters: {phase_encounters} | {pokemon['name']} Phase Encounters: {mon_stats['phase_encounters']}")
        debug_log.info(f"{pokemon['name']} Encounters: {mon_stats['encounters']:,} | Lowest {pokemon['name']} SV seen this phase: {mon_stats['phase_lowest_sv']}")
        debug_log.info(f"Shiny {pokemon['name']} Encounters: {mon_stats['shiny_encounters']:,} | {pokemon['name']} Shiny Average: {shiny_average}")
        debug_log.info(f"Total Encounters: {total_encounters:,} | Total Shiny Encounters: {total_shiny_encounters:,} | Total Shiny Average: {total_stats['shiny_average']}")

    # Use the correct article when describing the Pokemon
    # e.g. "A Poochyena", "An Anorith"
    article = "an" if mon_name.lower()[0] in {"a","e","i","o","u"} else "a"

    debug_log.info(f"------------------ {pokemon['name']} ------------------")
    debug_log.debug(pokemon)
    debug_log.info(f"Encountered {article} {pokemon['name']} at {pokemon['metLocationName']}")
    debug_log.info(f"HP: {pokemon['hpIV']} | ATK: {pokemon['attackIV']} | DEF: {pokemon['defenseIV']} | SPATK: {pokemon['spAttackIV']} | SPDEF: {pokemon['spDefenseIV']} | SPE: {pokemon['speedIV']}")
    debug_log.info(f"Shiny Value (SV): {pokemon['shinyValue']:,} (is {pokemon['shinyValue']:,} < 8 = {pokemon['shiny']})")

    # Set up pokemon stats if first encounter
    if not pokemon["name"] in stats["pokemon"]:
        stats["pokemon"].update({pokemon["name"]: {"encounters": 0, "shiny_encounters": 0, "phase_lowest_sv": "-", "phase_encounters": 0, "shiny_average": "-", "total_lowest_sv": "-"}})

    if pokemon["shiny"]:
        debug_log.info("Shiny Pokemon detected!")

        shortest_phase = stats["totals"]["shortest_phase_encounters"]
        encounters = stats["totals"]["phase_encounters"]

        if shortest_phase == "-": 
            shortest_phase = encounters
        else:
            shortest_phase = max(shortest_phase, encounters)

        stats["pokemon"][pokemon["name"]]["shiny_encounters"] += 1
        stats["totals"]["shiny_encounters"] += 1
        common_stats()
        stats["totals"]["phase_encounters"] = 0
        stats["totals"]["phase_lowest_sv"] = "-"
        stats["totals"]["phase_lowest_sv_pokemon"] = ""

        # Reset phase stats
        for mon_name in stats["pokemon"]:
            stats["pokemon"][mon_name]["phase_lowest_sv"] = "-"
            stats["pokemon"][mon_name]["phase_encounters"] = 0

        write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file
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

    debug_log.info(f"----------------------------------------")

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

def identify_pokemon(starter: bool = False): # Identify opponent pokemon and incremement statistics, returns True if shiny, else False
    legendary_hunt = config["bot_mode"] in ["manual", "rayquaza", "kyogre", "groudon", "southern island", "regi trio", "deoxys resets", "deoxys runaways", "mew"]

    debug_log.info("Identifying Pokemon...")
    release_all_inputs()

    if starter: 
        wait_frames(30)
    else:
        i = 0
        while trainer_info["state"] not in [3, 255] and i < 250:
            i += 1

    if trainer_info["state"] == GameState.OVERWORLD: 
        return False

    pokemon = party_info[0] if starter else opponent_info
    log_encounter(pokemon)

    replace_battler = False

    if pokemon["shiny"]:
        if not starter and not legendary_hunt and "shinies" in config["catch"]: 
            catch_pokemon()
        elif legendary_hunt:
            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")

        write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file
        return True
    else:
        if config["bot_mode"] == "manual":
            while trainer_info["state"] != GameState.OVERWORLD: 
                wait_frames(100)
        elif starter:
            return False

        if mon_is_desirable(pokemon):
            catch_pokemon()

        if not legendary_hunt:
            if config["battle_others"]:
                battle_won = battle()
                replace_battler = not battle_won
            else:
                flee_battle()
        elif config["bot_mode"] == "deoxys resets":
            if config["do_realistic_hunt"]:
                # Wait until sprite has appeared in battle before reset
                wait_frames(240)
            reset_game()
            return False
        else:
            flee_battle()

        if config["pickup"] and not legendary_hunt: 
            pickup_items()

        if replace_battler:
            if not config["cycle_lead_pokemon"]:
                debug_log.info("Lead Pokemon can no longer battle. Ending the script!")
                flee_battle()
                return
            else:
                start_menu("pokemon")

                # Find another healthy battler
                party_pp = [0, 0, 0, 0, 0, 0]
                i = 0
                for mon in party_info:
                    if mon == None:
                        continue

                    if mon["hp"] > 0 and i != 0:
                        j = 0
                        for move in mon["enrichedMoves"]:
                            if is_valid_move(move) and mon["pp"][j] > 0:
                                party_pp[i] += move["pp"]
                            j += 1

                    i += 1

                highest_pp = max(party_pp)
                lead_idx = party_pp.index(highest_pp)

                if highest_pp == 0:
                    debug_log.info("Ran out of Pokemon to battle with. Ending the script!")
                    os._exit(1)

                lead = party_info[lead_idx]
                if lead != None:
                    debug_log.info(f"Replacing lead battler with {lead['speciesName']} (Party slot {lead_idx})")

                press_button("A")
                wait_frames(60)
                press_button("A")
                wait_frames(15)

                for i in range(0, 3):
                    press_button("Up")
                    wait_frames(15)

                press_button("A")
                wait_frames(15)

                for i in range(0, lead_idx):
                    press_button("Down")
                    wait_frames(15)

                # Select target Pokemon and close out menu
                press_button("A")
                wait_frames(60)
                
                debug_log.info("Replaced lead Pokemon!")

                for i in range(0, 5):
                    press_button("B")
                    wait_frames(15)
        return False

def enrich_mon_data(pokemon: dict): # Function to add information to the pokemon data extracted from Bizhawk
    try:
        pokemon["name"] = pokemon["speciesName"].capitalize() # Capitalise name
        pokemon["metLocationName"] = location_list[pokemon["metLocation"]] # Add a human readable location
        pokemon["type"] = pokemon_list[pokemon["name"]]["type"] # Get pokemon types
        pokemon["ability"] = pokemon_list[pokemon["name"]]["ability"][0] # Get pokemon abilities
        pokemon["hiddenPowerType"] = calculate_hidden_power(pokemon)
        pokemon["nature"] = nature_list[pokemon["personality"] % 25] # Get pokemon nature
        pokemon["zeroPadNumber"] = f"{pokemon_list[pokemon['name']]['number']:03}" # Get zero pad number - e.g.: #5 becomes #005
        pokemon["itemName"] = item_list[pokemon['heldItem']] # Get held item's name

        personalityBin = format(pokemon["personality"], "032b") # Convert personality ID to binary
        personalityF = int(personalityBin[:16], 2) # Get first 16 bits of binary PID
        personalityL = int(personalityBin[16:], 2) # Get last 16 bits of binary PID
        pokemon["shinyValue"] = int(bin(personalityF ^ personalityL ^ trainer_info["tid"] ^ trainer_info["sid"])[2:], 2) # https://bulbapedia.bulbagarden.net/wiki/Personality_value#Shininess
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
        year, month, day, hour, minute, second = f"{now.year}", f"{(now.month):02}", f"{(now.day):02}", f"{(now.hour):02}", f"{(now.minute):02}", f"{(now.second):02}"

        pokemon["date"] = (f"{year}-{month}-{day}")
        pokemon["time"] = (f"{hour}:{minute}:{second}")

        return pokemon
    except Exception as e:
        if args.dm:
            debug_log.exception(str(e))
            moves = pokemon["moves"]
            debug_log.info(f"Moves: {moves}") 

def mem_getEmuInfo(): # Loop repeatedly to read emulator info from memory
    global emu_info, emu_speed, language, MapDataEnum

    while True:
        try:
            emu_info_mmap = load_json_mmap(4096, "bizhawk_emu_info")
            if emu_info_mmap:
                if validate_emu_info(emu_info_mmap["emu"]):
                    emu_info = emu_info_mmap["emu"]
                    if emu_info_mmap["emu"]["emuFPS"]: emu_speed = emu_info_mmap["emu"]["emuFPS"]/60

                    if language == None:
                        language = language_id_to_iso_639(emu_info["language"])
                        debug_log.info(f"Language was set to {language}")           

                    if not MapDataEnum and emu_info["detectedGame"]:
                        debug_log.info("Detected game: " + emu_info["detectedGame"])
                        if any([x in emu_info["detectedGame"] for x in ["Emerald", "Ruby", "Sapphire"]]):
                            MapDataEnum = mapRSE
                        #if any([x in emu_info["detectedGame"] for x in ["FireRed", "LeafGreen"]]):
                        #    MapDataEnum = mapFRLG
             
        except Exception as e:
            if args.dm: debug_log.exception(str(e))
            continue
        time.sleep(max((1/max(emu_speed,1))*0.016,0.002))

def mem_getTrainerInfo(): # Loop repeatedly to read trainer info from memory
    global trainer_info

    while True:
        try:
            trainer_info_mmap = load_json_mmap(4096, "bizhawk_trainer_info")
            if trainer_info_mmap:
                if validate_trainer_info(trainer_info_mmap["trainer"]):
                    if trainer_info_mmap["trainer"]["posX"] < 0: 
                        trainer_info_mmap["trainer"]["posX"] = 0
                    if trainer_info_mmap["trainer"]["posY"] < 0: 
                        trainer_info_mmap["trainer"]["posY"] = 0
                    trainer_info = trainer_info_mmap["trainer"]
            time.sleep(max((1/max(emu_speed,1))*0.016,0.002))
        except Exception as e:
            if args.dm: debug_log.exception(str(e))
            continue

def mem_getPartyInfo(): # Loop repeatedly to read party info from memory
    global party_info

    while True:
        try:
            party_info_mmap = load_json_mmap(8192, "bizhawk_party_info")

            if party_info_mmap:
                enriched_party_obj = []

                for pokemon in party_info_mmap["party"]:
                    if validate_pokemon(pokemon):
                        pokemon = enrich_mon_data(pokemon)
                        enriched_party_obj.append(pokemon)
                    else: continue

                party_info = enriched_party_obj
        except Exception as e:
            if args.dm: debug_log.exception(str(e))
            continue

        wait_frames(1)

def mem_getOpponentInfo(): # Loop repeatedly to read opponent info from memory
    global opponent_info, last_opponent_personality

    while True:
        try:
            opponent_info_mmap = load_json_mmap(4096, "bizhawk_opponent_info")

            if opponent_info_mmap:
                if validate_pokemon(opponent_info_mmap):
                    enriched_opponent_obj = enrich_mon_data(opponent_info_mmap["opponent"])

                    if enriched_opponent_obj:
                        opponent_info = enriched_opponent_obj
            elif not opponent_info: 
                opponent_info = json.loads(read_file("data/placeholder_pokemon.json"))
        except Exception as e:
            if args.d: debug_log.exception(str(e))
            continue

        wait_frames(1)

def mem_can_write_inputs():
    pass
#def mem_sendInputs(): TODO reimplement with new input system
#    while True:
#        try:
#            press_input_mmap.seek(0)
#            press_input_mmap.write(bytes(json.dumps(press_input), encoding="utf-8"))
#            hold_input_mmap.seek(0)
#            hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))
#        except Exception as e:
#            if args.d: debug_log.exception(str(e))
#            continue
#        time.sleep(0.08) #The less sleep the better but without sleep it will hit CPU hard

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
        @server.route('/shiny_log', methods=['GET'])		
        def req_shiny_log():		
            if shiny_log:		
                response = jsonify(shiny_log)		
                return response		
            else: abort(503)
        #@server.route('/config', methods=['POST'])
        #def submit_config():
        #    debug_log.info(request.get_json()) # TODO HTTP config handler
        #    response = jsonify({})
        #    return response

        server.run(debug=False, threaded=True, host="127.0.0.1", port=6969)
    except Exception as e: debug_log.exception(str(e))

def mainLoop():
    global last_opponent_personality
    
    if config["save_game_on_start"]: 
        save_game()
    
    release_all_inputs()

    while True:
        # Don't start bot until language is set
        if language == None:
            continue

        if trainer_info and emu_info and MapDataEnum:
            match config["bot_mode"]:
                case "manual":
                    while not opponent_changed(): 
                        wait_frames(20)
                    identify_pokemon()
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
                case "reporting":
                    mode_reporting()

                    if not purchase_success:
                        debug_log.info(f"Ran out of money to buy Premier Balls. Script ended.")
                        return
                case other:
                    debug_log.exception("Couldn't interpret bot mode: " + config["bot_mode"])
                    return
        else:
            if opponent_info:
                last_opponent_personality = opponent_info["personality"]
            
            release_all_inputs()
            time.sleep(0.2)
        wait_frames(1)

def mode_beldum():
    x, y = trainer_info["posX"], trainer_info["posY"]

    if (not player_on_map(MapDataEnum.MOSSDEEP_CITY_H.value) or not ((x == 3 and y == 3) or (x == 4 and y == 2))):
        debug_log.info("Please face the player toward the Pokeball in Steven's house after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon("Beldum")

def mode_castform():
    x, y = trainer_info["posX"], trainer_info["posY"]

    if (not player_on_map(MapDataEnum.ROUTE_119_B.value) or not ((x == 2 and y == 3) or (x == 3 and y == 2) or (x == 1 and y == 2))):
        debug_log.info("Please face the player toward the scientist after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon("Castform")

def mode_fossil():
    x, y = trainer_info["posX"], trainer_info["posY"]

    if not player_on_map(MapDataEnum.RUSTBORO_CITY_B.value) or y != 8 and not (x == 13 or x == 15):
        debug_log.info("Please face the player toward the Fossil researcher after handing it over, re-entering the room, and saving the game. Then restart the script.")
        os._exit(1)

    collect_gift_mon(config["fossil"])

def mode_johtoStarters():
    x, y = trainer_info["posX"], trainer_info["posY"]

    if (not player_on_map(MapDataEnum.LITTLEROOT_TOWN_D.value) or not (y == 5 and x >= 8 and x <= 10)):
        debug_log.info("Please face the player toward a Pokeball in Birch's Lab after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon(config["johto_starter"])

def collect_gift_mon(target: str):
    rng_frames = get_rngState(trainer_info["tid"], target)
    party_size = len(party_info)

    if party_size == 6:
        debug_log.info("Please leave at least one party slot open, then restart the script.")
        os._exit(1)

    while True:
        # Button mash through intro/title
        while trainer_info["state"] != GameState.OVERWORLD:
            press_button("A")
            wait_frames(8)
        
        # Text goes faster with B held
        hold_button("B")

        while len(party_info) == party_size:
            if emu_info["rngState"] in rng_frames:
                debug_log.debug(f"Already rolled on RNG state: {emu_info['rngState']}, waiting...")
                continue

            press_button("A")
            wait_frames(5)
        
        rng_frames["rngState"].append(emu_info["rngState"])
        write_file(f"stats/{trainer_info['tid']}/{target.lower()}.json", json.dumps(rng_frames, indent=4, sort_keys=True))

        mon = party_info[party_size]
        
        # Open the menu and find Gift mon in party
        release_button("B")

        if not config["do_realistic_hunt"] and not mon["shiny"]:
            log_encounter(mon)
            hold_button("Power")
            wait_frames(60)
            release_button("Power")
            continue

        while not find_image("start_menu/select.png"):
            press_button("B")

            for i in range(0, 4):
                if find_image("start_menu/select.png"):
                    break
                wait_frames(1)

        while find_image("start_menu/select.png"):
            press_button("B")
            
            for i in range(0, 4):
                if not find_image("start_menu/select.png"):
                    break
                wait_frames(1)

        start_menu("pokemon")

        wait_frames(60)

        i = 0
        while i < party_size:
            emu_combo(["Down", 15])
            i += 1

        emu_combo(["A", 15, "A", 60])

        log_encounter(mon)

        if not mon["shiny"]:
            hold_button("Power")
            wait_frames(60)
            release_button("Power")
        else:
            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")

def mode_regiTrio():
    if (not player_on_map(MapDataEnum.DESERT_RUINS.value) and
        not player_on_map(MapDataEnum.ISLAND_CAVE.value) and
        not player_on_map(MapDataEnum.ANCIENT_TOMB.value)):
        debug_log.info("Please place the player below the target Regi in Desert Ruins, Island Cave or Ancient Tomb, then restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["Up", "A"])

        identify_pokemon()

        while not trainer_info["state"] == GameState.OVERWORLD:
            continue

        # Exit and re-enter
        press_button("B")
        follow_path([
            (8, 21), 
            (8, 11)
        ])

def mode_deoxysPuzzle(do_encounter: bool = True):
    def retry_puzzle_if_stuck(success: bool):
        if not success: 
            reset_game()
            return True

    if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or trainer_info["posX"] != 15:
        debug_log.info("Please place the player below the triangle at its starting position on Birth Island, then save before restarting the script.")
        os._exit(1)

    delay = 4

    while True:
        while not trainer_info["state"] == GameState.OVERWORLD:
            emu_combo(["A", 8])

        wait_frames(60)

        # Center
        if trainer_info["posY"] != 13:
            run_until_obstructed("Up")
        emu_combo([delay, "A"])

        # Left
        follow_path([(15, 14), (12, 14)])
        emu_combo([delay, "Left", "A", delay])

        # Top
        if retry_puzzle_if_stuck(follow_path([(15, 14), (15, 9)], True, True)): continue
        emu_combo([delay, "Up", "A", delay])

        # Right
        if retry_puzzle_if_stuck(follow_path([(15, 14), (18, 14)], True, True)): continue
        emu_combo([delay, "Right", "A", delay])

        # Middle Left
        if retry_puzzle_if_stuck(follow_path([(15, 14), (15, 11), (13, 11)], True, True)): continue
        emu_combo([delay, "Left", "A", delay])

        # Middle Right
        follow_path([(17, 11)])
        emu_combo([delay, "Right", "A", delay])

        # Bottom
        if retry_puzzle_if_stuck(follow_path([(15, 11), (15, 13)], True, True)): continue
        emu_combo([delay, "Down", "A", delay])

        # Bottom Left
        follow_path([(15, 14), (12, 14)])
        emu_combo([delay, "Left", "A", delay])

        # Bottom Right
        follow_path([(18, 14)])
        emu_combo([delay, "Right", "A", delay])

        # Bottom
        follow_path([(15, 14)])
        emu_combo([delay, "Down", delay, "A", delay])

        # Center
        if retry_puzzle_if_stuck(follow_path([(15, 11)], True, True)): continue

        if not do_encounter:
            debug_log.info("Deoxys puzzle completed. Saving game and starting resets...")
            config["bot_mode"] = "deoxys resets"
            config["deoxys_puzzle_solved"] = True
            save_game()
            wait_frames(10)
            return True

        while not opponent_changed():
            press_button("A")
            wait_frames(1)

        identify_pokemon()

        while not trainer_info["state"] == GameState.OVERWORLD:
            continue

        for i in range(0, 4):
            press_button("B")
            wait_frames(15)

        # Exit and re-enter
        follow_path([
            (15, 99, (26, 59)), 
            (8, -99, MapDataEnum.BIRTH_ISLAND.value)
        ])

def mode_deoxysResets():
    if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or trainer_info["posX"] != 15:
        debug_log.info("Please place the player below the triangle at its final position on Birth Island, then save before restarting the script.")
        os._exit(1)

    deoxys_frames = get_rngState(trainer_info["tid"], "deoxys")

    while True:
        # Mash A to reach overworld from intro/title
        while trainer_info["state"] != GameState.OVERWORLD:
            emu_combo(["A", 8])

        # Wait for area to load properly
        wait_frames(60)

        if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or trainer_info["posX"] != 15:
            debug_log.info("Please place the player below the triangle at its final position on Birth Island, then save before restarting the script.")
            os._exit(1)

        while emu_info["rngState"] in deoxys_frames:
            debug_log.debug(f"Already rolled on RNG state: {emu_info['rngState']}, waiting...")
        else:
            deoxys_frames["rngState"].append(emu_info["rngState"])
            write_file(f"stats/{trainer_info['tid']}/deoxys.json", json.dumps(deoxys_frames, indent=4, sort_keys=True))

        while not opponent_changed():
            emu_combo(["A", 8])

        identify_pokemon()

def mode_sweetScent():
    debug_log.info(f"Using Sweet Scent...")
    start_menu("pokemon")
    press_button("A") # Select first pokemon in party

    # Search for sweet scent in menu
    while not find_image("sweet_scent.png"): 
        press_button("Down")

    emu_combo(["A", 300]) # Select sweet scent and wait for animation
    identify_pokemon()

def mode_bunnyHop():
    debug_log.info("Bunny hopping...")
    i = 0
    while not opponent_changed():
        if i < 250:
            hold_button("B")
            wait_frames(1)
        else:
            release_all_inputs()
            wait_frames(10)
            i = 0
        i += 1
    release_all_inputs()
    identify_pokemon()

def mode_move_between_coords():
    coords = config["coords"]
    pos1, pos2 = coords["pos1"], coords["pos2"]

    while True:
        foe_personality = last_opponent_personality

        while foe_personality == last_opponent_personality:
            follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])

        identify_pokemon()

        while trainer_info["state"] != GameState.OVERWORLD:
            continue

def mode_move_until_obstructed():
    direction = config["direction"].lower()

    while True:
        pos1, pos2 = None, None
        foe_personality = last_opponent_personality
        debug_log.info(f"Pathing {direction} until obstructed...")

        while foe_personality == last_opponent_personality:
            if pos1 == None or pos2 == None:
                if direction == "horizontal":
                    pos1 = run_until_obstructed("Left")
                    pos2 = run_until_obstructed("Right")
                else:
                    pos1 = run_until_obstructed("Up")
                    pos2 = run_until_obstructed("Down")
            else:
                if pos1 == pos2:
                    pos1 = None
                    pos2 = None
                    continue

                follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])
            opponent_changed()

        identify_pokemon()

        while trainer_info["state"] != GameState.OVERWORLD:
            continue

def mode_fishing():
    debug_log.info(f"Fishing...")
    emu_combo(["Select", 50]) # Cast rod and wait for fishing animation
    started_fishing = time.time()
    while not opponent_changed():
        if find_image("oh_a_bite.png") or find_image("on_the_hook.png"): 
            press_button("A")
            while find_image("oh_a_bite.png"):
                pass #This keeps you from getting multiple A presses and failing the catch
        if find_image("not_even_a_nibble.png") or find_image("it_got_away.png"): emu_combo(["B", 10, "Select"])
        if not find_image("text_period.png"): emu_combo(["Select", 50]) # Re-cast rod if the fishing text prompt is not visible

    identify_pokemon()

def get_rngState(tid: str, mon: str):
    file = read_file(f"stats/{tid}/{mon.lower()}.json")
    data = json.loads(file) if file else {"rngState": []}

    return data

def mode_starters():
    choice = config["starter"].lower()
    starter_frames = get_rngState(trainer_info['tid'], choice)

    if choice not in ["treecko", "torchic", "mudkip"]:
        debug_log.info(f"Unknown starter \"{config['starter']}\". Please edit the value in config.yml and restart the script.")
        os._exit(1)

    debug_log.info(f"Soft resetting starter Pokemon...")
    
    while True:
        release_all_inputs()

        while trainer_info["state"] != GameState.OVERWORLD: 
            press_button("A")

        # Short delay between A inputs to prevent accidental selection confirmations
        while trainer_info["state"] == GameState.OVERWORLD: 
            emu_combo(["A", 10])

        # Press B to back out of an accidental selection when scrolling to chosen starter
        if choice == "mudkip":
            while not find_image("mudkip.png"): 
                emu_combo(["B", "Right"])
        elif choice == "treecko":
            while not find_image("treecko.png"): 
                emu_combo(["B", "Left"])

        while emu_info["rngState"] in starter_frames["rngState"]:
            debug_log.debug(f"Already rolled on RNG state: {emu_info['rngState']}, waiting...")
        else:
            starter_frames["rngState"].append(emu_info["rngState"])
            write_file(f"stats/{trainer_info['tid']}/{choice}.json", json.dumps(starter_frames, indent=4, sort_keys=True))
            
            while trainer_info["state"] == GameState.MISC_MENU: 
                press_button("A")
            while not find_image("battle/fight.png"):
                press_button("B")

                if not config["do_realistic_hunt"] and party_info and party_info[0]:
                    if identify_pokemon(starter=True):
                        input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                    else:
                        reset_game()
                        break
            else:
                while True:
                    if party_info and party_info[0]:
                        if identify_pokemon(starter=True): 
                            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                        else:
                            reset_game()
                            break

def mode_rayquaza():
    if (not player_on_map(MapDataEnum.SKY_PILLAR_G.value) or
        not (trainer_info["posX"] == 14 and trainer_info["posY"] <= 12)):
        debug_log.info("Please place the player below Rayquaza at the Sky Pillar and restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["A", "Up"]) # Walk up toward Rayquaza while mashing A
        
        identify_pokemon()

        # Wait until battle is over
        while trainer_info["state"] != GameState.OVERWORLD:
            continue

        # Exit and re-enter
        press_button("B")
        follow_path([
            (14, 11), 
            (12, 11), 
            (12, 15), 
            (16, 15), 
            (16, -99, MapDataEnum.SKY_PILLAR_F.value),
            (10, -99, MapDataEnum.SKY_PILLAR_G.value),
            (12, 15), 
            (12, 11), 
            (14, 11), 
            (14, 7)
        ])

def mode_groudon():
    if (not player_on_map(MapDataEnum.TERRA_CAVE_A.value) or
        not 11 <= trainer_info["posX"] <= 20 and 26 <= trainer_info["posY"] <= 27):
        debug_log.info("Please place the player below Groudon in Terra Cave and restart the script.")
        os._exit(1)

    while True:
        follow_path([(17, 26)])

        identify_pokemon()

        # Exit and re-enter
        follow_path([
            (7, 26), 
            (7, 15), 
            (9, 15), 
            (9, 4), 
            (5, 4), 
            (5, 99, MapDataEnum.TERRA_CAVE.value), 
            (14, -99, MapDataEnum.TERRA_CAVE_A.value), 
            (9, 4), (9, 15), 
            (7, 15), 
            (7, 26), 
            (11, 26)
        ])

def mode_kyogre():
    if (not player_on_map(MapDataEnum.MARINE_CAVE_A.value) or
        not 5 <= trainer_info["posX"] <= 14 and 26 <= trainer_info["posY"] <= 27):
        debug_log.info("Please place the player below Kyogre in Marine Cave and restart the script.")
        os._exit(1)

    while True:
        follow_path([(9, 26)])

        identify_pokemon()

        # Exit and re-enter
        follow_path([
            (9, 27), 
            (18, 27), 
            (18, 14), 
            (14, 14), 
            (14, 4), 
            (20, 4), 
            (20, 99, MapDataEnum.MARINE_CAVE.value), 
            (14, -99, MapDataEnum.MARINE_CAVE_A.value), 
            (14, 4), 
            (14, 14), 
            (18, 14), 
            (18, 27), 
            (14, 27)
        ])

def mode_farawayMew():
    if (not player_on_map(MapDataEnum.FARAWAY_ISLAND.value) or not (22 <= trainer_info["posX"] <= 23 and 8 <= trainer_info["posY"] <= 10)):
        debug_log.info("Please place the player below the entrance to Mew's area, then restart the script.")
        os._exit(1)
        return

    while True:
        # Enter main area
        while player_on_map(MapDataEnum.FARAWAY_ISLAND.value):
            follow_path([
                (22, 8),
                (22, -99, MapDataEnum.FARAWAY_ISLAND_A.value)
            ])
        
        wait_frames(30)
        hold_button("B")
        
        follow_path([
            (trainer_info["posX"], 16),
            (16, 16)
        ])
        # 
        # Follow Mew up while mashing A
        hold_button("Up")

        while not opponent_changed():
            emu_combo(["A", 8])

        identify_pokemon()

        for i in range(0, 6):
            press_button("B")
            wait_frames(10)

        # Exit to entrance area
        follow_path([
            (16, 16),
            (12, 16),
            (12, 99, MapDataEnum.FARAWAY_ISLAND.value)
        ])

def mode_southernIsland():
    if (not player_on_map(MapDataEnum.SOUTHERN_ISLAND_A.value) or
        not 5 <= trainer_info["posX"] == 13 and trainer_info["posY"] >= 12):
        debug_log.info("Please place the player below the sphere on Southern Island and restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["A", "Up"])

        identify_pokemon()

        # Wait until battle is over
        while trainer_info["state"] != GameState.OVERWORLD:
            continue

        # Exit and re-enter
        press_button("B")
        follow_path([
            (13, 99, MapDataEnum.SOUTHERN_ISLAND.value), 
            (14, -99, MapDataEnum.SOUTHERN_ISLAND_A.value)
        ])

def mode_buyPremierBalls():
    while not find_image("mart/times_01.png"):
        press_button("A")
        
        if find_image("mart/you_dont.png"):
            return False

        wait_frames(30)

    press_button("Right")
    wait_frames(15)

    if not find_image("mart/times_10.png") and not find_image("mart/times_11.png"):
        return False

    if find_image("mart/times_11.png"):
        press_button("Down")

    return True

def mode_reporting():
    debug_log.info("Running in reporting mode... Don't forget to set `enable_input` to false in `pokebot.lua` before running in Bizhawk!")
    report_trainer_info, report_emu_info = trainer_info, emu_info

    report_template = read_file("data/report_template.html")
    report_start = datetime.now().strftime('%Y%m%d-%H%M%S')

    report_path = f"reports/{report_start}"
    report_file = f"{report_path}/report.html"
    report_image_path = f"reports/{report_start}/img"

    if not os.path.exists(report_image_path):
        os.makedirs(report_image_path)

    write_file(report_file, report_template)

    debug_log.info(f"Report will be generated to ./{report_file}")

    def diff_dict(dict1: dict, dict2: dict):
        return dict(set(dict1.items()) ^ set(dict2.items()))

    while True:
        html = ''

        if diff_dict(report_trainer_info, trainer_info):

            image_time = datetime.now().strftime('%Y%m%d-%H%M%S%f')
            cv2.imwrite(f"reports/{report_start}/img/{image_time}.png", get_screenshot())

            html = f"""
            </br></br><hr><h2>{image_time}</h2>
            <img src="img/{image_time}.png">
            </br></br>emu_info:
            </br><code>{emu_info}</code>
            </br>diff:
            </br><code>{diff_dict(report_emu_info, emu_info)}</code>
            </br></br>trainer_info:
            </br><code>{trainer_info}</code>
            </br>diff:
            </br><code>{diff_dict(report_trainer_info, trainer_info)}</code>
            </br><section><article>
            </br></br><details><summary>opponent_info</summary><code>{opponent_info}</code></details>
            </br><details><summary>party_info</summary><code>{party_info}</code></details>
            </article></section>
            """

            write_file(report_file, html, "a")

        report_trainer_info, report_emu_info = trainer_info, emu_info
        time.sleep(frames_to_ms(1))

try:
    # Parse flags to change the behaviour of the bot
    parser = argparse.ArgumentParser()
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
    debug_log.exception(str(e))
    os._exit(1)

try:
    # Validate python version
    min_major = 3
    min_minor = 10
    v_major = sys.version_info[0]
    v_minor = sys.version_info[1]

    if v_major < min_major or v_minor < min_minor:
        debug_log.error(f"\n\nPython version is out of date! (Minimum required version for pokebot is {min_major}.{min_minor})\nPlease install the latest version at https://www.python.org/downloads/\n")
        os._exit(1)

    debug_log.info(f"Running pokebot on Python {v_major}.{v_minor}")

    # Confirm that the Lua Console is open by doing a test screenshot
    mmap_screenshot_size, mmap_screenshot_file = 24576, "bizhawk_screenshot"
    can_start_bot = True

    try:
        shmem = mmap.mmap(0, mmap_screenshot_size, mmap_screenshot_file)
        screenshot = Image.open(io.BytesIO(shmem))
    except:
        debug_log.error("\n\nUnable to initialize pokebot!\nPlease confirm that the Lua Console is open in BizHawk, and that it remains open while the bot is active.\nIt can be opened through 'Tools > Lua Console'.\n\nStarting in dashboard-only mode...\n")
        can_start_bot = False

    yaml = YAML()
    yaml.default_flow_style = False

    config = yaml.load(read_file("config.yml")) # Load config

    last_trainer_state, last_opponent_personality, trainer_info, opponent_info, emu_info, party_info, emu_speed, language, MapDataEnum = None, None, None, None, None, None, 1, None, None
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    # Main bot functionality
    if can_start_bot:        
        if args.s: config["save_game_on_start"] = True
        if args.m: config["bot_mode"] = "Manual"

        config["bot_mode"] = config["bot_mode"].lower() # Decase all bot modes

        debug_log.info(f"Mode: {config['bot_mode']}")

        default_input = {"A": False, "B": False, "L": False, "R": False, "Up": False, "Down": False, "Left": False, "Right": False, "Select": False, "Start": False, "Light Sensor": 0, "Power": False, "Tilt X": 0, "Tilt Y": 0, "Tilt Z": 0, "Screenshot": False}
        
        input_list_mmap = mmap.mmap(-1, 4096, tagname="bizhawk_input_list", access=mmap.ACCESS_WRITE)
        g_current_index = 1 # Variable that keeps track of what input in the list we are on.
        input_list_mmap.seek(0)

        for i in range(100): # Clear any prior inputs from last time script ran in case you haven't refreshed in Lua
             input_list_mmap.write(bytes('a', encoding="utf-8"))
        
        item_list = json.loads(read_file("data/items.json"))
        location_list = json.loads(read_file("data/locations.json"))
        move_list = json.loads(read_file("data/moves.json"))
        pokemon_list = json.loads(read_file("data/pokemon.json"))
        type_list = json.loads(read_file("data/types.json"))
        nature_list = json.loads(read_file("data/natures.json"))

        pokemon_schema = json.loads(read_file("data/schemas/pokemon.json"))
        validate_pokemon = fastjsonschema.compile(pokemon_schema)
        trainer_info_schema = json.loads(read_file("data/schemas/trainer_info.json"))
        validate_trainer_info = fastjsonschema.compile(trainer_info_schema)
        emu_info_schema = json.loads(read_file("data/schemas/emu_info.json"))
        validate_emu_info = fastjsonschema.compile(emu_info_schema)

        hold_input_mmap = mmap.mmap(-1, 4096, tagname="bizhawk_hold_input", access=mmap.ACCESS_WRITE)
        hold_input = default_input

        poll_screenshot = Thread(target=mem_pollScreenshot)
        poll_screenshot.start()

        get_emu_info = Thread(target=mem_getEmuInfo)
        get_emu_info.start()

        get_trainer_info = Thread(target=mem_getTrainerInfo)
        get_trainer_info.start()

        get_party_info = Thread(target=mem_getPartyInfo)
        get_party_info.start()

        if not config["bot_mode"] in ["starters", "johto starters", "fossil", "castform", "beldum"]:
            get_opponent_info = Thread(target=mem_getOpponentInfo)
            get_opponent_info.start()
        
        #send_inputs = Thread(target=mem_sendInputs) TODO Use another buffer to throttle inputs and use this thread again
        #send_inputs.start()

        main_loop = Thread(target=mainLoop)
        main_loop.start()

    # Dashboard
    http_server = Thread(target=httpServer)
    http_server.start()

    os.makedirs("stats", exist_ok=True) # Sets up stats files if they don't exist

    totals = read_file("stats/totals.json")
    stats = json.loads(totals) if totals else {"pokemon": {}, "totals": {"longest_phase_encounters": 0, "shortest_phase_encounters": "-", "phase_lowest_sv": 99999, "phase_lowest_sv_pokemon": "", "encounters": 0, "phase_encounters": 0, "shiny_average": "-", "shiny_encounters": 0}}

    encounters = read_file("stats/encounter_log.json")
    encounter_log = json.loads(encounters) if encounters else {"encounter_log": []}
    
    shinies = read_file("stats/shiny_log.json")
    shiny_log = json.loads(shinies) if shinies else {"shiny_log": []} 

    def on_window_close():
        if can_start_bot:
            release_all_inputs()

        debug_log.info("Dashboard closed on user input")
        os._exit(1)

    window = webview.create_window("PokeBot", url="interface/dashboard.html", width=1280, height=720, resizable=True, hidden=False, frameless=False, easy_drag=True, fullscreen=False, text_select=True, zoomable=True)
    window.events.closed += on_window_close

    webview.start()

except Exception as e:
    debug_log.exception(str(e))
    os._exit(1)
