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
from data.MapData import MapBank, MapID

def player_on_map(map_bank: int, map_id: int):
    on_map = trainer_info["mapBank"] == map_bank and trainer_info["mapId"] == map_id

    if not on_map:
        debug_log.info(f"Player was not on target map of {map_bank},{map_id}. Map was {trainer_info['mapBank']}, {trainer_info['mapId']}")

    return on_map

def read_file(file: str): # Simple function to read data from a file, return False if file doesn't exist
    try:
        debug_log.debug(f"Reading file: {file}...")
        with open(file, mode="r", encoding="utf-8") as open_file:
            return open_file.read()
    except Exception as e:
        if args.d: debug_log.exception(str(e))
        return False

def write_file(file: str, value: str): # Simple function to write data to a file, will create the file if doesn't exist
    try:
        debug_log.debug(f"Writing file: {file}...")
        with open(file, mode="w", encoding="utf-8") as save_file:
            save_file.write(value)
            return True
    except Exception as e:
        if args.d: debug_log.exception(str(e))
        return False

def load_json_mmap(size, file): # Function to load a JSON object from a memory mapped file
    # BizHawk writes game information to memory mapped files every few frames (see bizhawk.lua)
    # See https://tasvideos.org/Bizhawk/LuaFunctions (comm.mmfWrite)
    try:
        shmem = mmap.mmap(0, size, file)
        if shmem:
            if args.dm: debug_log.debug(f"Attempting to read {file} ({size} bytes) from memory...")
            bytes_io = io.BytesIO(shmem)
            byte_str = bytes_io.read()
            if args.dm: debug_log.debug(f"Byte string: {byte_str}")
            json_obj = json.loads(byte_str.decode("utf-8").split("\x00")[0]) # Only grab the data before \x00 null chars
            if args.dm: debug_log.debug(f"JSON result: {json_obj}")
            return json_obj
        else: return False
    except Exception as e:
        if args.dm: debug_log.exception(str(e))
        return False

def frames_to_ms(frames: float):
    return max((frames/60.0) / emu_speed, 0.02)

# Pre-compile sleep pattern regex
sleep_pattern = re.compile("^\d*\.?\d*ms$")

def emu_combo(sequence: list): # Function to send a sequence of inputs and delays to the emulator
    # Example: emu_combo(["B", "Up", "500ms", "Left"])
    try:
        for k in sequence:
            if sleep_pattern.match(k):
                delay = float(k[:-2])  # Remove "ms" from the string
                time.sleep((delay/1000) / emu_speed)
            elif k == "button_release:all":
                release_all_inputs()  
            else: press_button(k)
    except Exception as e:
        if args.d: debug_log.exception(str(e))

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
        input_list_mmap.write(bytes(button,"utf-8"))
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
        #press_input[button] = False
        hold_input[button] = False
        hold_input_mmap.seek(0)
        hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))
def opponent_changed(): # This function checks if there is a different opponent since last check, indicating the game state is probably now in a battle
    try:
        global last_opponent_personality
        #debug_log.info(f"Checking if opponent has changed... Previous PID: {last_opponent_personality}, New PID: {opponent_info['personality']}")

        # Fixes a bug where the bot checks the opponent for up to 20 seconds if it was last closed in a battle
        if trainer_info["state"] == 80:
            return False

        if opponent_info and last_opponent_personality != opponent_info["personality"]:
            last_opponent_personality = opponent_info["personality"]
            debug_log.info("Opponent has changed!")
            return True
        
        return False
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
        #g_bizhawk_screenshot = get_screenshot()
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

no_sleep_abilities = ["Shed Skin", "Insomnia", "Vital Spirit"]

def catch_pokemon(): # Function to catch pokemon
    try:
        while not find_image("battle/fight.png"):
            emu_combo(["button_release:all", "B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible
        
        if config["manual_catch"]:
            input("Pausing bot for manual catch (don't forget to pause bizhawk.lua script so you can provide inputs). Press Enter to continue...")
            return True
        else:
            debug_log.info("Attempting to catch Pokemon...")
        
        if config["use_spore"]: # Use Spore to put opponent to sleep to make catches much easier
            debug_log.info("Attempting to sleep the opponent...")
            i, spore_pp = 0, 0
            
            ability = opponent_info["ability"][opponent_info["altAbility"]]
            can_sleep = ability not in no_sleep_abilities

            if (opponent_info["status"] == 0) and can_sleep:
                for move in party_info[0]["enrichedMoves"]:
                    if move["name"] == "Spore":
                        spore_pp = move["pp"]
                        spore_move_num = i
                    i += 1

                if spore_pp != 0:
                    emu_combo(["A", "100ms"])
                    if spore_move_num == 0: seq = ["Up", "Left"]
                    elif spore_move_num == 1: seq = ["Up", "Right"]
                    elif spore_move_num == 2: seq = ["Left", "Down"]
                    elif spore_move_num == 3: seq = ["Right", "Down"]

                    while not find_image("spore.png"):
                        emu_combo(seq)

                    emu_combo(["A", "4000ms"]) # Select move and wait for animations
            elif not can_sleep:
                debug_log.info(f"Can't sleep the opponent! Ability is {ability}")

            while not find_image("battle/bag.png"): emu_combo(["button_release:all", "B", "Up", "Right"]) # Press B + up + right until BAG menu is visible

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

                time.sleep(frames_to_ms(120)) # Wait for animations
                
                if config["save_game_after_catch"]: 
                    save_game()
                
                return True

            if trainer_info["state"] == GameState.OVERWORLD:
                return False
    except Exception as e:
        if args.di: debug_log.exception(str(e))
        return False

def battle(): # Function to battle wild pokemon
    try:
        # This will only battle with the lead pokemon of the party, and will run if it dies or runs out of PP
        ally_fainted = False
        foe_fainted = False

        while not ally_fainted and not foe_fainted:
            debug_log.info("Navigating to the FIGHT button...")
            while not find_image("battle/fight.png"):
                if trainer_info["state"] == GameState.OVERWORLD:
                    return
                emu_combo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible

            best_move = find_effective_move(party_info[0], opponent_info)
            
            if best_move["power"] <= 10:
                debug_log.info("Lead Pokemon has no effective moves to battle the foe!")
                flee_battle()
                return False
            
            emu_combo(["A", "100ms"])
            
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
            
            emu_combo(["A", "4000ms"])

            if opponent_info["hp"] == 0:
                foe_fainted = True
            elif party_info[0]["hp"] == 0:
                debug_log.info("Lead Pokemon fainted!")
                flee_battle()
                return False

        while trainer_info["state"] != GameState.OVERWORLD:
            if find_image("stop_learning.png"): # Check if our Pokemon is trying to learn a move and skip learning
                press_button("A")
            press_button("B")

        if foe_fainted:
            debug_log.info("Battle won!")
            return True
    except Exception as e:
        if args.di: debug_log.exception(str(e))
        return False

def find_effective_move(ally: dict, foe: dict):
    i = 0
    move_power = []

    for move in ally["enrichedMoves"]:
        power = move["power"]

        # Ignore banned moves and those with 0 PP
        if move["name"] in config["banned_moves"] or power == 0 or ally["pp"][i] == 0:
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
                emu_combo(["Right","50ms","Down", "B","50ms"])
            while find_image("battle/run.png") and trainer_info["state"] != GameState.OVERWORLD: 
                press_button("A")
            press_button("B")
        time.sleep(frames_to_ms(30)) # Wait for battle fade animation
    except Exception as e:
        if args.d: debug_log.exception(str(e))

def run_until_obstructed(direction: str, run: bool = True): # Function to run until trainer position stops changing
    try:
        debug_log.info(f"Pathing {direction.lower()} until obstructed...")
        if run: hold_button("B")
        hold_button(direction)
        last_x = trainer_info["posX"]
        last_y = trainer_info["posY"]

        if run: move_speed = 8
        else: move_speed = 16

        dir_unchanged = 0
        while dir_unchanged < move_speed:
            time.sleep(frames_to_ms(1))
            if last_x == trainer_info["posX"] and last_y == trainer_info["posY"]: 
                dir_unchanged += 1
                continue
            
            last_x = trainer_info["posX"]
            last_y = trainer_info["posY"]
            dir_unchanged = 0
        
        release_button(direction)
        press_button("B") # press and release B in case of a random pokenav call

        return [last_x, last_y]
    except Exception as e:
        if args.d: debug_log.exception(str(e))

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
                            #press_button("B")
                            stuck = 0
                        
                        if trainer_info[axis] == last_axis: stuck += 1
                        else: stuck = 0
                        last_axis = trainer_info[axis]
                        time.sleep(frames_to_ms(1))

                        if not opponent_changed():
                            try: target_pos()
                            except Exception as e:
                                if args.dm: debug_log.exception(str(e))
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
                        time.sleep(frames_to_ms(1))

                        if not opponent_changed():
                            try: target_pos()
                            except Exception as e:
                                if args.dm: debug_log.exception(str(e))
                                return False
                        else:
                            identify_pokemon()
                            return False
                    else:
                        release_all_inputs()
                        return True
        except Exception as e:
            if args.dm: debug_log.exception(str(e))
            return False

    try:
        for x, y, *map_data in coords:
            #debug_log.info(f"Current: X: {trainer_info['posX']}, Y: {trainer_info['posY']}, Map: [({trainer_info['mapBank']},{trainer_info['mapId']})]")
            #debug_log.info(f"Pathing: X: {x}, Y: {y}, Map: {map_data}")
            while not run_to_pos(x, y, map_data): continue
            else: release_all_inputs()
    except Exception as e:
        if args.dm: debug_log.exception(str(e))
        return False

menus = ["bag", "bot", "exit", "option", "pokedex", "pokemon", "pokenav", "save"]

def start_menu(entry: str): # Function to open any start menu item - presses START, finds the menu entry and opens it
    try:
        if entry in menus:
            debug_log.info(f"Opening start menu entry: {entry}")
            filename = f"start_menu/{entry.lower()}.png"
            
            release_all_inputs()

            # Press start until menu is visible
            while True:
                emu_combo(["Start", "200ms"])

                if find_image(f"start_menu/select.png"):
                    break

            while not find_image(filename): # Find menu entry
                emu_combo(["Down", "150ms"])

            while find_image(filename): # Press menu entry
                emu_combo(["A", "200ms"])
        else:
            return False
    except Exception as e:
        if args.di: debug_log.exception(str(e))
        return False

def bag_menu(category: str, item: str): # Function to find an item in the bag and use item in battle such as a pokeball
    try:
        if category in ["berries", "items", "key_items", "pokeballs", "tms&hms"]:
            debug_log.info(f"Scrolling to bag category: {category}...")

            while not find_image(f"start_menu/bag/{category.lower()}.png"):
                emu_combo(["Right", "400ms"]) # Press right until the correct category is selected
            time.sleep(frames_to_ms(60)) # Wait for animations

            debug_log.info(f"Scanning for item: {item}...")
            i = 0
            while not find_image(f"start_menu/bag/items/{item}.png") and i < 50:
                if i < 25: emu_combo(["Down", "200ms"])
                else: emu_combo(["Up", "200ms"])
                i += 1

            if find_image(f"start_menu/bag/items/{item}.png"):
                debug_log.info(f"Using item: {item}...")
                while trainer_info["state"] == GameState.BAG_MENU: emu_combo(["A", "500ms"]) # Press A to use the item
                return True
            else:
                return False
    except Exception as e:
        if args.di: debug_log.exception(str(e))
        return False

pickup_pokemon = ["Meowth", "Aipom", "Phanpy", "Teddiursa", "Zigzagoon", "Linoone"]

def pickup_items(): # If using a team of Pokemon with the ability "pickup", this function will take the items from the pokemon in your party if 3 or more Pokemon have an item
    try:
        if trainer_info["state"] != GameState.OVERWORLD:
            return

        debug_log.info("Checking for pickup items...")
        item_count = 0
        pickup_mon_count = 0

        for i in range(0, 6):
            pokemon = party_info[i]
            held_item = pokemon['heldItem']

            if pokemon["speciesName"] in pickup_pokemon:
                if held_item != 0:
                    item_count += 1

                pickup_mon_count += 1
                debug_log.info(f"Pokemon {i}: {pokemon['speciesName']} has item: {item_list[held_item]}")

        if item_count < config["pickup_threshold"]:
            return

        time.sleep(frames_to_ms(60)) # Wait for animations
        start_menu("pokemon") # Open Pokemon menu
        time.sleep(frames_to_ms(60))

        for i in range(0, 6):
            pokemon = party_info[i]
            if pokemon["speciesName"] in pickup_pokemon and pokemon["heldItem"] != 0:
                # Take the item from the pokemon
                emu_combo(["200ms", "A", "50ms", "Up", "50ms", "Up", "50ms", "A", "50ms", "Down", "50ms", "A", "1000ms", "B", "200ms"])
                item_count -= 1
            
            if item_count == 0:
                break

            emu_combo(["200ms", "Down"])

        emu_combo(["50ms", "B", "300ms", "B", "50ms"]) # Close out of menus
    except Exception as e:
        if args.dm: debug_log.exception(str(e))

def save_game(): # Function to save the game via the save option in the start menu
    try:
        debug_log.info("Saving the game...")

        i = 0
        start_menu("save")
        while i < 2:
            while not find_image("start_menu/save/yes.png"):
                time.sleep(frames_to_ms(10))
            while find_image("start_menu/save/yes.png"):
                emu_combo(["A", "500ms"])
                i += 1
        time.sleep(frames_to_ms(500)) # Wait for game to save
    except Exception as e:
        if args.dm: debug_log.exception(str(e))

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

        if starter: time.sleep(frames_to_ms(50))
        else:
            i = 0
            while trainer_info["state"] not in [3, 255] and i < 250:
                #press_button("B")
                i += 1
        if trainer_info["state"] == GameState.OVERWORLD: return False

        if starter: pokemon = party_info[0]
        else: pokemon = opponent_info

        replace_battler = False
        debug_log.info(f"------------------ {pokemon['name']} ------------------")
        debug_log.debug(pokemon)
        debug_log.info(f"Encountered a {pokemon['name']} at {pokemon['metLocationName']}")
        debug_log.info(f"HP: {pokemon['hpIV']} | ATK: {pokemon['attackIV']} | DEF: {pokemon['defenseIV']} | SPATK: {pokemon['spAttackIV']} | SPDEF: {pokemon['spDefenseIV']} | SPE: {pokemon['speedIV']}")
        debug_log.info(f"Shiny Value (SV): {pokemon['shinyValue']:,} (is {pokemon['shinyValue']:,} < 8 = {pokemon['shiny']})")

        if not pokemon["name"] in stats["pokemon"]: 
            stats["pokemon"].update({pokemon["name"]: {"encounters": 0, "shiny_encounters": 0, "phase_lowest_sv": "-", "phase_encounters": 0, "shiny_average": "-", "total_lowest_sv": "-"}}) # Set up pokemon stats if first encounter

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

            if not starter and config["bot_mode"] not in ["manual", "rayquaza", "kyogre", "groudon"] and "shinies" in config["catch"]: 
                catch_pokemon()

            if not args.n: write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file

            return True
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
    
            if config["bot_mode"] == "manual":
                while trainer_info["state"] != GameState.OVERWORLD: 
                    time.sleep(frames_to_ms(100))
            elif not starter:
                if "perfect_ivs" in config["catch"] and mon_ivs_meets_threshold(pokemon, 31):
                    catch_pokemon()
                elif "zero_ivs" in config["catch"] and not mon_ivs_meets_threshold(pokemon, 1):
                    catch_pokemon()
                elif "good_ivs" in config["catch"] and mon_ivs_meets_threshold(pokemon, 25):
                    catch_pokemon()
                elif "all" in config["catch"]:
                    catch_pokemon()
                
                ### Custom Filters ###
                # Add custom filters here (make sure to uncomment the line), examples:
                # If you want to pause the bot instead of automatically catching, replace `catch_pokemon()` with `input("Pausing bot for manual catch (don't forget to pause bizhawk.lua script so you can provide inputs). Press Enter to continue...")`

                # --- Catch any species that the trainer has not already caught ---
                #elif pokemon["hasSpecies"] == 0: catch_pokemon()

                # --- Catch all Luvdisc with the held item "Heart Scale" ---
                #elif pokemon["name"] == "Luvdisc" and pokemon["itemName"] == "Heart Scale": catch_pokemon()

                # --- Catch Lonely natured Ralts with >25 attackIV and spAttackIV ---
                #elif pokemon["name"] == "Ralts" and pokemon["attackIV"] > 25 and pokemon["spAttackIV"] > 25 and pokemon["nature"] == "Lonely": catch_pokemon()

                elif config["battle_others"]: 
                    replace_battler = not battle()
                else:
                    flee_battle()

            if config["pickup"]: 
                pickup_items()

            if replace_battler:
                start_menu("pokemon")

                # Find another healthy battler
                party_pp = [0, 0, 0, 0, 0, 0]
                i = 0
                for mon in party_info:
                    if mon["hp"] > 0 and i != 0:
                        for move in mon["enrichedMoves"]:
                            party_pp[i] += move["pp"]

                    i += 1

                lead_idx = party_pp.index(max(party_pp))

                debug_log.info(f"Replacing lead battler with {party_info[lead_idx]['speciesName']} (Party slot {lead_idx})")

                # Scroll to and select SWITCH
                while not find_image("start_menu/select.png"):
                    emu_combo(["A", "100ms"])
                
                emu_combo(["Up", "500ms", "Up", "500ms", "Up", "500ms", "A", "500ms"])

                for i in range(0, lead_idx):
                    emu_combo(["Down", "100ms"])

                # Select target Pokemon and close out menu
                emu_combo(["A", "100ms"])
                emu_combo(["50ms", "B", "300ms", "B", "50ms"])
            return False
    except Exception as e:
        if args.dm: debug_log.exception(str(e))

def mon_ivs_meets_threshold(pokemon: dict, threshold: int):
    return (pokemon["hpIV"] >= threshold and
            pokemon["attackIV"] >= threshold and
            pokemon["defenseIV"] >= threshold and
            pokemon["speedIV"] >= threshold and
            pokemon["spAttackIV"] >= threshold and
            pokemon["spDefenseIV"] >= threshold)

def enrich_mon_data(pokemon: dict): # Function to add information to the pokemon data extracted from Bizhawk
    try:
        pokemon["name"] = pokemon["speciesName"].capitalize() # Capitalise name
        pokemon["metLocationName"] = location_list[pokemon["metLocation"]] # Add a human readable location
        pokemon["type"] = pokemon_list[pokemon["name"]]["type"] # Get pokemon types
        pokemon["ability"] = pokemon_list[pokemon["name"]]["ability"] # Get pokemon abilities
        pokemon["hiddenPowerType"] = calculate_hidden_power(pokemon)
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
        else: pokemon["pokerusStatus"] = "none"
        return pokemon
    except Exception as e:
        if args.dm:
            debug_log.exception(str(e))
            moves = pokemon["moves"]
            debug_log.info(f"Moves: {moves}") 

def language_id_to_iso_639(lang: int):
    match lang:
        case 1: return "en"
        case 2: return "jp"
        case 3: return "fr"
        case 4: return "es"
        case 5: return "de"
        case 6: return "it"

def mem_getEmuInfo(): # Loop repeatedly to read emulator info from memory
    try:
        global emu_info, emu_speed, language

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
            except Exception as e:
                if args.dm: debug_log.exception(str(e))
                continue
            time.sleep(max((1/max(emu_speed,1))*0.016,0.002))

    except Exception as e:
        if args.d: debug_log.exception(str(e))

def mem_getTrainerInfo(): # Loop repeatedly to read trainer info from memory
    global trainer_info

    while True:
        try:
            trainer_info_mmap = load_json_mmap(4096, "bizhawk_trainer_info")
            if trainer_info_mmap:
                if validate_trainer_info(trainer_info_mmap["trainer"]):
                    if trainer_info_mmap["trainer"]["posX"] < 0: trainer_info_mmap["trainer"]["posX"] = 0
                    if trainer_info_mmap["trainer"]["posY"] < 0: trainer_info_mmap["trainer"]["posY"] = 0
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
            time.sleep(max((1/max(emu_speed,1))*0.016,0.002))
        except Exception as e:
            if args.dm: debug_log.exception(str(e))
            continue

def mem_getOpponentInfo(): # Loop repeatedly to read opponent info from memory
    global opponent_info, last_opponent_personality

    while True:
        try:
            opponent_info_mmap = load_json_mmap(4096, "bizhawk_opponent_info")
            if config["bot_mode"] == "starters":
                if party_info: opponent_info = party_info[0]
            elif opponent_info_mmap:
                if validate_pokemon(opponent_info_mmap):
                    enriched_opponent_obj = enrich_mon_data(opponent_info_mmap["opponent"])
                    if enriched_opponent_obj:
                        opponent_info = enriched_opponent_obj
            elif not opponent_info: opponent_info = json.loads(read_file("data/placeholder_pokemon.json"))
            time.sleep(max((1/max(emu_speed,1))*0.016,0.002))
        except Exception as e:
            if args.d: debug_log.exception(str(e))
            continue
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
        #@server.route('/config', methods=['POST'])
        #def submit_config():
        #    debug_log.info(request.get_json()) # TODO HTTP config handler
        #    response = jsonify({})
        #    return response

        server.run(debug=False, threaded=True, host="127.0.0.1", port=6969)
    except Exception as e: debug_log.exception(str(e))

def mainLoop(): # 🔁 Main loop
    try:
        global last_opponent_personality
        
        if config["save_game_on_start"]: save_game()
        release_all_inputs()

        while True:
            # Don't start bot until language is set
            if language == None:
                continue

            if trainer_info and emu_info:
                match config["bot_mode"]:
                    case "manual":
                        while not opponent_changed(): 
                            time.sleep(frames_to_ms(20))
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
                    case "buy premier balls":
                        purchase_success = mode_buyPremierBalls()

                        if not purchase_success:
                            debug_log.info(f"Ran out of money to buy Premier Balls. Script ended.")
                            return
                    case other:
                        debug_log.exception("Couldn't interpret bot mode: " + config["bot_mode"])
                        return
            else:
                if opponent_info: last_opponent_personality = opponent_info["personality"]
                release_all_inputs()
                time.sleep(0.2)
            time.sleep(max((1/max(emu_speed,1))*0.016,0.002))

    except Exception as e:
        if args.d: debug_log.exception(str(e))

def mode_sweetScent():
    debug_log.info(f"Using Sweet Scent...")
    start_menu("pokemon")
    press_button("A") # Select first pokemon in party

    # Search for sweet scent in menu
    while not find_image("sweet_scent.png"): 
        press_button("Down")

    emu_combo(["A", "5000ms"]) # Select sweet scent and wait for animation
    identify_pokemon()

def mode_bunnyHop():
    debug_log.info("Bunny hopping...")
    i = 0
    while not opponent_changed():
        if i < 250:
            hold_button("B")
            time.sleep(frames_to_ms(1))
        else:
            release_all_inputs()
            time.sleep(frames_to_ms(10))
            i = 0
        i += 1
    release_all_inputs()
    identify_pokemon()

def mode_move_between_coords():
    coords = config["coords"]
    pos1, pos2 = coords["pos1"], coords["pos2"]

    while not opponent_changed():
        follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])

def mode_move_until_obstructed():
    pos1, pos2 = None, None
    direction = config["direction"].lower()

    while not opponent_changed():
        if pos1 == None or pos2 == None:
            if direction == "horizontal":
                pos1 = run_until_obstructed("Left")
                pos2 = run_until_obstructed("Right")
            else:
                pos1 = run_until_obstructed("Up")
                pos2 = run_until_obstructed("Down")
        else:
            follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])

def mode_fishing():
    # 🐠 Fishing method
    debug_log.info(f"Fishing...")
    emu_combo(["Select", "800ms"]) # Cast rod and wait for fishing animation
    started_fishing = time.time()
    while not opponent_changed(): # State 80 = overworld
        if find_image("oh_a_bite.png") or find_image("on_the_hook.png"): 
            press_button("A")
            while find_image("oh_a_bite.png"):
                pass #This keeps you from getting multiple A presses and failing the catch
        if find_image("not_even_a_nibble.png") or find_image("it_got_away.png"): emu_combo(["B", "100ms", "Select"])
        if not find_image("text_period.png"): emu_combo(["Select", "800ms"]) # Re-cast rod if the fishing text prompt is not visible
    identify_pokemon()

def mode_starters():
    debug_log.info(f"Soft resetting starter Pokemon...")
    release_all_inputs()
    while trainer_info["state"] != GameState.OVERWORLD: press_button("A")

    if read_file(f"stats/{trainer_info['tid']}.json"): starter_frames = json.loads(read_file(f"stats/{trainer_info['tid']}.json")) # Open starter frames file
    else: starter_frames = {"rngState": {"Treecko": [], "Torchic": [], "Mudkip": []}}

    while trainer_info["state"] == GameState.OVERWORLD: press_button("A")
    if config["starter_pokemon"] == "Mudkip":
        while not find_image("mudkip.png"): press_button("Right")
    elif config["starter_pokemon"] == "Treecko":
        while not find_image("treecko.png"): press_button("Left")

    while emu_info["rngState"] in starter_frames["rngState"][config["starter_pokemon"]]:
        debug_log.debug(f"Already rolled on RNG state: {emu_info['rngState']}, waiting...")
    else:
        starter_frames["rngState"][config["starter_pokemon"]].append(emu_info["rngState"])
        write_file(f"stats/{trainer_info['tid']}.json", json.dumps(starter_frames, indent=4, sort_keys=True))
        while trainer_info["state"] == GameState.MISC_MENU: press_button("A")
        while not find_image("battle/fight.png"):
            release_all_inputs()
            emu_combo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible
        while True:
            try:
                if party_info[0]:
                    if identify_pokemon(starter=True): input("Pausing bot for manual catch (don't forget to pause bizhawk.lua script so you can provide inputs). Press Enter to continue...") # Kill bot and wait for manual intervention to manually catch the shiny starter
                    else:
                        hold_button("Power")
                        print("Holding Power")
                        time.sleep(frames_to_ms(50))
                        break
            except: continue

def mode_rayquaza():
    if not player_on_map(MapBank.DUNGEONS, MapID.RAYQUAZA_PILLAR):
        return False

    if not trainer_info["posX"] == 14 and trainer_info["posY"] <= 12:
        return

    while True:
        emu_combo(["A", "Up"]) # Walk up toward Rayquaza while mashing A

        if player_on_map(MapBank.DUNGEONS, MapID.RAYQUAZA_PILLAR) and trainer_info["posY"] < 7: # break if trainer passes the point where Rayquaza is meant to be (indicates Rayquaza has flown away)
            break

        if trainer_info["state"] != GameState.OVERWORLD:    
            if opponent_changed():
                if identify_pokemon(): input("Pausing bot for manual catch. Press Enter to continue...") # Kill bot and wait for manual intervention to manually catch Rayquaza
                break

    time.sleep(frames_to_ms(100))
    press_button("B")

    follow_path([(14, 11), (12, 11), (12, 15), (16, 15), (16, -99, (24, 84)), (10, -99, (24, 85)), (12, 15), (12, 11), (14, 11), (14, 7)])

def mode_groudon():
    if not player_on_map(MapBank.DUNGEONS, MapID.GROUDON_CAVE):
        return False

    if not 11 <= trainer_info["posX"] <= 20 and 26 <= trainer_info["posY"] <= 27:
        return

    while True:
        follow_path([(trainer_info["posX"], 26), (17, 26), (7, 26), (7, 15), (9, 15), (9, 4), (5, 4), (5, 99, (24, 104)), (14, -99, (24, 105)), (9, 4), (9, 15), (7, 15), (7, 26), (11, 26)])

def mode_kyogre():
    if not player_on_map(MapBank.DUNGEONS, MapID.KYOGRE_CAVE):
       return False

    if not 5 <= trainer_info["posX"] <= 14 and 26 <= trainer_info["posY"] <= 27:
        return

    while True:
        follow_path([(trainer_info["posX"], 26), (9, 26), (9, 27), (18, 27), (18, 14), (14, 14), (14, 4), (20, 4), (20, 99, (24, 102)), (14, -99, (24, 103)), (14, 4), (14, 14), (18, 14), (18, 27), (14, 27)])

def mode_southernIsland():
    if not player_on_map(MapBank.SPECIAL, MapID.LATI_ISLAND) :
        return False

    if not 5 <= trainer_info["posX"] == 13 and trainer_info["posY"] >= 12:
        return True

    while True:
        follow_path([(13, 99, (26, 9)), (14, -99, (26, 10))])
        i = 0
        while not opponent_changed():
            if i < 500:
                follow_path([(13, 12)])
                emu_combo(["A", "1000ms"])
                if find_image("dreams.png"):
                    press_button("B")
                    break
                i += 1
            else: break
        else: identify_pokemon()

def mode_buyPremierBalls():
    while not find_image("mart/times_01.png"):
        release_all_inputs()
        emu_combo(["A", "400ms"])

        if find_image("mart/you_dont.png"): # Not enough money to buy a single ball
            return False

    press_count = 0
    while not find_image("mart/times_11.png") and not find_image("mart/times_10.png"):
        emu_combo(["Right", "100ms"])

        if press_count > 3: # Not enough money to buy at least 10
            return False
        press_count += 1

    while not find_image("mart/times_10.png"):
        emu_combo(["Down", "100ms"])

    return True

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

    last_trainer_state, last_opponent_personality, trainer_info, opponent_info, emu_info, party_info, emu_speed, language = None, None, None, None, None, None, 1, None
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    # Main bot functionality
    if can_start_bot:        
        if args.s: config["save_game_on_start"] = True
        if args.m: config["bot_mode"] = "Manual"

        config["bot_mode"] = config["bot_mode"].lower() # Decase all bot modes

        debug_log.info(f"Mode: {config['bot_mode']}")

    default_input = {"A": False, "B": False, "L": False, "R": False, "Up": False, "Down": False, "Left": False, "Right": False, "Select": False, "Start": False, "Light Sensor": 0, "Power": False, "Tilt X": 0, "Tilt Y": 0, "Tilt Z": 0, "Screenshot": False}
    input_list_mmap = mmap.mmap(-1, 4096, tagname="bizhawk_input_list", access=mmap.ACCESS_WRITE)
    g_current_index = 1 #Variable that keeps track of what input in the list we are on.
    
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

    get_opponent_info = Thread(target=mem_getOpponentInfo)
    get_opponent_info.start()
    
    #send_inputs = Thread(target=mem_sendInputs) TODO Use another buffer to throttle inputs and use this thread again
    #send_inputs.start()

    main_loop = Thread(target=mainLoop)
    main_loop.start()

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

    # Dashboard
    http_server = Thread(target=httpServer)
    http_server.start()

    os.makedirs("stats", exist_ok=True) # Sets up stats files if they don't exist

    totals = read_file("stats/totals.json")
    if totals: stats = json.loads(totals)
    else: stats = {"pokemon": {}, "totals": {"longest_phase_encounters": 0, "shortest_phase_encounters": "-", "phase_lowest_sv": 99999, "phase_lowest_sv_pokemon": "", "encounters": 0, "phase_encounters": 0, "shiny_average": "-", "shiny_encounters": 0}}

    encounters = read_file("stats/encounter_log.json")
    if encounters: encounter_log = json.loads(encounters)
    else: encounter_log = {"encounter_log": []}

    shinies = read_file("stats/shiny_log.json")
    if shinies: shiny_log = json.loads(shinies) # Open shiny log file
    else: shiny_log = {"shiny_log": []}

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