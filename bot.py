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
from threading import Thread, Event
import logging
from logging.handlers import RotatingFileHandler 
# Image processing and detection modules
import cv2
import numpy
from PIL import Image, ImageGrab, ImageFile

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

# TODO move to modules/Map.py
def player_on_map(map_data: tuple):
    trainer = GetTrainer()
    on_map = trainer["mapBank"] == map_data[0] and trainer["mapId"] == map_data[1]
    log.debug(f"Player was not on target map of {map_data[0]},{map_data[1]}. Map was {trainer['mapBank']}, {trainer['mapId']}")
    return on_map

# TODO move to modules/Control.py
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
        case 'SaveRAM':
            button = 'x'

    index = g_current_index
    input_list_mmap.seek(index)
    input_list_mmap.write(bytes(button, encoding="utf-8"))
    input_list_mmap.seek(100) #Position 0-99 are inputs, position 100 keeps the value of the current index
    input_list_mmap.write(bytes([index+1]))

    g_current_index +=1
    if g_current_index > 99:
        g_current_index = 0

# TODO move to modules/Control.py
def hold_button(button: str): # Function to update the hold_input object
    global hold_input
    log.debug(f"Holding: {button}...")

    hold_input[button] = True
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

# TODO move to modules/Control.py
def release_button(button: str): # Function to update the hold_input object
    global hold_input
    log.debug(f"Releasing: {button}...")

    hold_input[button] = False
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

# TODO move to modules/Control.py
def release_all_inputs(): # Function to release all keys in all input objects
    global press_input, hold_input
    log.debug(f"Releasing all inputs...")

    for button in ["A", "B", "L", "R", "Up", "Down", "Left", "Right", "Select", "Start", "Power"]:
        hold_input[button] = False
        hold_input_mmap.seek(0)
        hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

def opponent_changed(): # This function checks if there is a different opponent since last check, indicating the game state is probably now in a battle
    try:
        global last_opponent_personality

        # Fixes a bug where the bot checks the opponent for up to 20 seconds if it was last closed in a battle
        if GetTrainer()["state"] == GameState.OVERWORLD:
            return False

        opponent = GetOpponent()
        if opponent and last_opponent_personality != opponent["personality"]:
            log.info(f"Opponent has changed! Previous PID: {last_opponent_personality}, New PID: {opponent['personality']}")
            last_opponent_personality = opponent["personality"]
            return True   
    except Exception as e:
        log.exception(str(e))
        return False

# TODO move to modules/Image.py
def find_image(file: str): # Function to find an image in a BizHawk screenshot
    try:
        threshold = 0.999
        template = cv2.imread(f"data/templates/{GetEmu()['language']}/" + file, cv2.IMREAD_UNCHANGED)
        hh, ww = template.shape[:2]

        screenshot = GetScreenshot()    
        correlation = cv2.matchTemplate(screenshot, template[:,:,0:3], cv2.TM_CCORR_NORMED) # Do masked template matching and save correlation image
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(correlation)
        max_val_corr = float('{:.6f}'.format(max_val))
        if max_val_corr > threshold: 
            # Debug image detection - shows a window with a red square around the detected match
            #loc = numpy.where(correlation >= threshold)
            #result = screenshot.copy()
            #for point in zip(*loc[::-1]):
            #    cv2.rectangle(result, point, (point[0]+ww, point[1]+hh), (0,0,255), 1)
            #    cv2.imshow(f"match", result)
            #    cv2.waitKey(1)
            return True
        else:
            return False
        
    except Exception as e:
        log.exception(str(e))
        return False

# TODO move to modules/Something?.py
def catch_pokemon(): # Function to catch pokemon
    try:
        while not find_image("battle/fight.png"):
            release_all_inputs()
            emu_combo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible
        
        if config["manual_catch"]:
            input("Pausing bot for manual catch (don't forget to pause pokebot.lua script so you can provide inputs). Press Enter to continue...")
            return True
        else:
            log.info("Attempting to catch Pokemon...")
        
        if config["use_spore"]: # Use Spore to put opponent to sleep to make catches much easier
            log.info("Attempting to sleep the opponent...")
            i, spore_pp = 0, 0
            
            opponent = GetOpponent()
            ability = opponent["ability"][opponent["altAbility"]]
            can_spore = ability not in no_sleep_abilities

            if (opponent["status"] == 0) and can_spore:
                for move in GetParty()[0]["enrichedMoves"]:
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
                log.info(f"Can't sleep the opponent! Ability is {ability}")

            while not find_image("battle/bag.png"): 
                release_all_inputs()
                emu_combo(["B", "Up", "Right"]) # Press B + up + right until BAG menu is visible

        while True:
            if find_image("battle/bag.png"): press_button("A")

            # Preferred ball order to catch wild mons + exceptions 
            # TODO read this data from memory instead
            if GetTrainer()["state"] == GameState.BAG_MENU:
                can_catch = False

                # Check if current species has a preferred ball
                if opponent["speciesName"] in config["pokeball_override"]:
                    species_rule = config["pokeball_override"][opponent["speciesName"]]
                    
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
                    log.info("No balls to catch the Pokemon found. Killing the script!")
                    os._exit(1)

            if find_image("gotcha.png"): # Check for gotcha! text when a pokemon is successfully caught
                log.info("Pokemon caught!")

                while GetTrainer()["state"] != GameState.OVERWORLD:
                    press_button("B")

                wait_frames(120) # Wait for animations
                
                if config["save_game_after_catch"]: 
                    save_game()
                
                return True

            if GetTrainer()["state"] == GameState.OVERWORLD:
                return False
    except Exception as e:
        log.exception(str(e))
        return False

# TODO move to modules/Something?.py
def battle(): # Function to battle wild pokemon
    # This will only battle with the lead pokemon of the party, and will run if it dies or runs out of PP
    ally_fainted = False
    foe_fainted = False

    while not ally_fainted and not foe_fainted and GetTrainer()["state"] != GameState.OVERWORLD:
        log.info("Navigating to the FIGHT button...")

        while not find_image("battle/fight.png") and GetTrainer()["state"] != GameState.OVERWORLD:
            emu_combo(["B", 10, "Up", 10, "Left", 10]) # Press B + up + left until FIGHT menu is visible
        
        if GetTrainer()["state"] == GameState.OVERWORLD:
            return True

        best_move = find_effective_move(GetParty()[0], GetOpponent())
        
        if best_move["power"] <= 10:
            log.info("Lead Pokemon has no effective moves to battle the foe!")
            flee_battle()
            return False
        
        press_button("A")

        wait_frames(5)

        log.info(f"Best move against foe is {best_move['name']} (Effective power is {best_move['power']})")

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

        while GetTrainer()["state"] != GameState.OVERWORLD and not find_image("battle/fight.png"):
            press_button("B")
            wait_frames(1)
        
        ally_fainted = GetParty()[0]["hp"] == 0
        foe_fainted = GetOpponent()["hp"] == 0
    
    if ally_fainted:
        log.info("Lead Pokemon fainted!")
        flee_battle()
        return False
    elif foe_fainted:
        log.info("Battle won!")
        return True
    return True

def is_valid_move(move: dict):
    return not move["name"] in config["banned_moves"] and move["power"] > 0

# TODO move to modules/Something?.py
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

# TODO move to modules/Something?.py
def flee_battle(): # Function to run from wild pokemon
    try:
        log.info("Running from battle...")
        while GetTrainer()["state"] != GameState.OVERWORLD:
            while not find_image("battle/run.png") and GetTrainer()["state"] != GameState.OVERWORLD: 
                emu_combo(["Right", 5, "Down", "B", 5])
            while find_image("battle/run.png") and GetTrainer()["state"] != GameState.OVERWORLD: 
                press_button("A")
            press_button("B")
        wait_frames(30) # Wait for battle fade animation
    except Exception as e:
        log.exception(str(e))

# TODO move to modules/Navigation.py
def run_until_obstructed(direction: str, run: bool = True): # Function to run until trainer position stops changing
    press_button("B") # press and release B in case of a random pokenav call

    hold_button(direction)
    last_x = GetTrainer()["posX"]
    last_y = GetTrainer()["posY"]

    if run: move_speed = 8
    else: move_speed = 16

    dir_unchanged = 0
    while dir_unchanged < move_speed:
        if run: 
            hold_button("B")
        
        wait_frames(1)

        trainer = GetTrainer()
        if last_x == trainer["posX"] and last_y == trainer["posY"]: 
            dir_unchanged += 1
            continue

        last_x = trainer["posX"]
        last_y = trainer["posY"]
        dir_unchanged = 0

        if opponent_changed():
            return None

    release_all_inputs()
    wait_frames(1)
    press_button("B")
    wait_frames(1)

    return [last_x, last_y]

# TODO move to modules/Navigation.py
def follow_path(coords: list, run: bool = True, exit_when_stuck: bool = False):
    possibly_stuck = False
    direction = None

    for x, y, *map_data in coords:
        log.info(f"Moving to: {x}, {y}")

        stuck_time = 0
        last_pos = [0, 0]

        if run:
            hold_button("B")

        while True:
            if direction != None:
                release_button(direction)

            if opponent_changed():
                identify_pokemon()
                return

            trainer = GetTrainer()
            last_pos = [trainer["posX"], trainer["posY"]]

            if map_data != []:
                # On map change
                if (trainer["mapBank"] == map_data[0][0] and trainer["mapId"] == map_data[0][1]):
                    break
            elif last_pos[0] == x and last_pos[1] == y:
                break
            
            if trainer["posX"] > x:
                direction = "Left"
            elif trainer["posX"] < x:
                direction = "Right"
            elif trainer["posY"] < y:
                direction = "Down"
            elif trainer["posY"] > y:
                direction = "Up"

            if trainer["posX"] == last_pos[0] and trainer["posY"] == last_pos[1]:
                stuck_time += 1

                if stuck_time == 120:
                    log.info("Bot hasn't moved for a while. Is it stuck?")
                    
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

# TODO move to modules/Menuing.py
def start_menu(entry: str): # Function to open any start menu item - presses START, finds the menu entry and opens it
    if not entry in ["bag", "bot", "exit", "option", "pokedex", "pokemon", "pokenav", "save"]:
        return False

    log.info(f"Opening start menu entry: {entry}")
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

# TODO move to modules/Menuing.py
def bag_menu(category: str, item: str): # Function to find an item in the bag and use item in battle such as a pokeball
    if not category in ["berries", "items", "key_items", "pokeballs", "tms&hms"]:
        return False

    log.info(f"Scrolling to bag category: {category}...")

    while not find_image(f"start_menu/bag/{category.lower()}.png"):
        emu_combo(["Right", 25]) # Press right until the correct category is selected

    wait_frames(60) # Wait for animations

    log.info(f"Scanning for item: {item}...")
    
    i = 0
    while not find_image(f"start_menu/bag/items/{item}.png") and i < 50:
        if i < 25: emu_combo(["Down", 15])
        else: emu_combo(["Up", 15])
        i += 1

    if find_image(f"start_menu/bag/items/{item}.png"):
        log.info(f"Using item: {item}...")
        while GetTrainer()["state"] == GameState.BAG_MENU: 
            emu_combo(["A", 30]) # Press A to use the item
        return True
    else:
        return False

# TODO move to modules/Menuing.py
def pickup_items(): # If using a team of Pokemon with the ability "pickup", this function will take the items from the pokemon in your party if 3 or more Pokemon have an item
    if GetTrainer()["state"] != GameState.OVERWORLD:
        return

    item_count = 0
    pickup_mon_count = 0
    party_size = len(GetParty())

    i = 0
    while i < party_size:
        pokemon = GetParty()[i]
        held_item = pokemon['heldItem']

        if pokemon["speciesName"] in pickup_pokemon:
            if held_item != 0:
                item_count += 1

            pickup_mon_count += 1
            log.info(f"Pokemon {i}: {pokemon['speciesName']} has item: {item_list[held_item]}")

        i += 1

    if item_count < config["pickup_threshold"]:
        log.info(f"Party has {item_count} item(s), won't collect until at threshold {config['pickup_threshold']}")
        return

    wait_frames(60) # Wait for animations
    start_menu("pokemon") # Open Pokemon menu
    wait_frames(65)

    i = 0
    while i < party_size:
        pokemon = GetParty()[i]
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

# TODO move to modules/Menuing.py
def save_game(): # Function to save the game via the save option in the start menu
    try:
        log.info("Saving the game...")

        i = 0
        start_menu("save")
        while i < 2:
            while not find_image("start_menu/save/yes.png"):
                wait_frames(10)
            while find_image("start_menu/save/yes.png"):
                emu_combo(["A", 30])
                i += 1
        wait_frames(500) # Wait for game to save
        press_button("SaveRAM") # Flush Bizhawk SaveRAM to disk
    except Exception as e:
        log.exception(str(e))

# TODO move to modules/Menuing.py
def reset_game():
    log.info("Resetting...")
    hold_button("Power")
    wait_frames(60)
    release_button("Power")

# TODO move to modules/Stats.py
def log_encounter(pokemon: dict):
    global last_opponent_personality

    # Show Gift Pokemon as the current encounter
    if last_opponent_personality != pokemon["personality"]:
        last_opponent_personality = pokemon["personality"]

    def common_stats():
        global stats, encounter_log

        mon_stats = stats["pokemon"][pokemon["name"]]
        total_stats = stats["totals"]

        mon_stats["encounters"] += 1
        mon_stats["phase_encounters"] += 1

        # Update encounter stats
        phase_encounters = total_stats["phase_encounters"]
        total_encounters = total_stats["encounters"] + total_stats["shiny_encounters"]
        total_shiny_encounters = total_stats["shiny_encounters"]

        # Log lowest Shiny Value
        if mon_stats["phase_lowest_sv"] == "-": 
            mon_stats["phase_lowest_sv"] = pokemon["shinyValue"]
        else:
            mon_stats["phase_lowest_sv"] = min(pokemon["shinyValue"], mon_stats["phase_lowest_sv"])

        if mon_stats["total_lowest_sv"] == "-": 
            mon_stats["total_lowest_sv"] = pokemon["shinyValue"]
        else:
            mon_stats["total_lowest_sv"] = min(pokemon["shinyValue"], mon_stats["total_lowest_sv"])

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
        encounter_log["encounter_log"] = encounter_log["encounter_log"][-100:]

        write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file
        write_file("stats/encounter_log.json", json.dumps(encounter_log, indent=4, sort_keys=True)) # Save encounter log file
        write_file("stats/shiny_log.json", json.dumps(shiny_log, indent=4, sort_keys=True)) # Save shiny log file

        now = datetime.now()
        year, month, day, hour, minute, second = f"{now.year}", f"{(now.month):02}", f"{(now.day):02}", f"{(now.hour):02}", f"{(now.minute):02}", f"{(now.second):02}"
            
        if config["log"]:
            # Log all encounters to a CSV file per phase
            csvpath = "stats/encounters/"
            csvfile = f"Phase {total_shiny_encounters} Encounters.csv"
            pokemondata = pd.DataFrame.from_dict(pokemon, orient='index').drop(
                ['enrichedMoves', 'moves', 'pp', 'type']).sort_index().transpose()
            os.makedirs(csvpath, exist_ok=True)
            header = False if os.path.exists(f"{csvpath}{csvfile}") else True
            pokemondata.to_csv(f"{csvpath}{csvfile}", mode='a', encoding='utf-8', index=False, header=header)

        log.info(f"Phase encounters: {phase_encounters} | {pokemon['name']} Phase Encounters: {mon_stats['phase_encounters']}")
        log.info(f"{pokemon['name']} Encounters: {mon_stats['encounters']:,} | Lowest {pokemon['name']} SV seen this phase: {mon_stats['phase_lowest_sv']}")
        log.info(f"Shiny {pokemon['name']} Encounters: {mon_stats['shiny_encounters']:,} | {pokemon['name']} Shiny Average: {shiny_average}")
        log.info(f"Total Encounters: {total_encounters:,} | Total Shiny Encounters: {total_shiny_encounters:,} | Total Shiny Average: {total_stats['shiny_average']}")

    # Use the correct article when describing the Pokemon
    # e.g. "A Poochyena", "An Anorith"
    article = "an" if pokemon["name"].lower()[0] in {"a","e","i","o","u"} else "a"

    log.info(f"------------------ {pokemon['name']} ------------------")
    log.debug(pokemon)
    log.info(f"Encountered {article} {pokemon['name']} at {pokemon['metLocationName']}")
    log.info(f"HP: {pokemon['hpIV']} | ATK: {pokemon['attackIV']} | DEF: {pokemon['defenseIV']} | SPATK: {pokemon['spAttackIV']} | SPDEF: {pokemon['spDefenseIV']} | SPE: {pokemon['speedIV']}")
    log.info(f"Shiny Value (SV): {pokemon['shinyValue']:,} (is {pokemon['shinyValue']:,} < 8 = {pokemon['shiny']})")

    # Set up pokemon stats if first encounter
    if not pokemon["name"] in stats["pokemon"]:
        stats["pokemon"].update({pokemon["name"]: {"encounters": 0, "shiny_encounters": 0, "phase_lowest_sv": "-", "phase_encounters": 0, "shiny_average": "-", "total_lowest_sv": "-"}})

    if pokemon["shiny"]:
        log.info("Shiny Pokemon detected!")

        shortest_phase = stats["totals"]["shortest_phase_encounters"]
        encounters = stats["totals"]["phase_encounters"]

        # Send webhook message, if enabled.
        if config["discord_webhook_url"]:
            log.info("Sending Discord ping...")
            if config["discord_shiny_ping"] and config["discord_ping_mode"] == "role": # Thanks Discord for making role and user IDs use the same format, but have different syntaxes for pinging them by ID, really cool.
                content=f"<@&{config['discord_shiny_ping']}>"
            elif config["discord_ping_mode"] == "user":
                content=f"<@{config['discord_shiny_ping']}>"
            else:
                content="" # It breaks if I don't do this, sorry.
            webhook = DiscordWebhook(url=config["discord_webhook_url"], content=content)
            embed = DiscordEmbed(title='Shiny encountered!', description=f"{pokemon['name']} at {pokemon['metLocationName']}", color='ffd242')
            embed.set_footer(text='PokeBot')
            embed.set_timestamp()
            embed.add_embed_field(name='Shiny Value', value=f"{pokemon['shinyValue']:,}")
            embed.add_embed_field(name='Nature', value=f"{pokemon['nature']}")
            # Basic IV list
            if config["discord_webhook_ivs"] == "basic" or config["discord_webhook_ivs"] == "":
                embed.add_embed_field(name='IVs', value=f"HP: {pokemon['hpIV']} | ATK: {pokemon['attackIV']} | DEF: {pokemon['defenseIV']} | SPATK: {pokemon['spAttackIV']} | SPDEF: {pokemon['spDefenseIV']} | SPE: {pokemon['speedIV']}", inline=False)
            # Formatted IV list
            if config["discord_webhook_ivs"] == "formatted":
                embed.add_embed_field(name='IVs', value=f"""
                `╔═══╤═══╤═══╤═══╤═══╤═══╗`\n`
                 ║HP │ATK│DEF│SPA│SPD│SPE║`\n`
                 ╠═══╪═══╪═══╪═══╪═══╪═══╣`\n`
                 ║{pokemon['hpIV']:^3}│{pokemon['attackIV']:^3}│{pokemon['defenseIV']:^3}│{pokemon['spAttackIV']:^3}│{pokemon['spDefenseIV']:^3}│{pokemon['speedIV']:^3}║`\n`
                 ╚═══╧═══╧═══╧═══╧═══╧═══╝`""", inline=False)            
            embed.add_embed_field(name='Species Phase Encounters', value=f"{stats['pokemon'][pokemon['name']]['phase_encounters']}")
            embed.add_embed_field(name='All Phase Encounters', value=f"{stats['totals']['phase_encounters']}")
            with open(f"interface/sprites/pokemon/shiny/{pokemon['name']}.png", "rb") as shiny:
                webhook.add_file(file=shiny.read(), filename='shiny.png')
            embed.set_thumbnail(url='attachment://shiny.png')
            webhook.add_embed(embed)
            response = webhook.execute()
        
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
        stats["totals"]["shortest_phase"] = shortest_phase

        # Reset phase stats
        for pokemon["name"] in stats["pokemon"]:
            stats["pokemon"][pokemon["name"]]["phase_lowest_sv"] = "-"
            stats["pokemon"][pokemon["name"]]["phase_encounters"] = 0

        write_file("stats/totals.json", json.dumps(stats, indent=4, sort_keys=True)) # Save stats file
    else:
        log.info("Non shiny Pokemon detected...")

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

    log.info(f"----------------------------------------")

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

# TODO move to modules/Stats.py
def identify_pokemon(starter: bool = False): # Identify opponent pokemon and incremement statistics, returns True if shiny, else False
    legendary_hunt = config["bot_mode"] in ["manual", "rayquaza", "kyogre", "groudon", "southern island", "regi trio", "deoxys resets", "deoxys runaways", "mew"]

    log.info("Identifying Pokemon...")
    release_all_inputs()

    if starter: 
        wait_frames(30)
    else:
        i = 0
        while GetTrainer()["state"] not in [3, 255] and i < 250:
            i += 1

    if GetTrainer()["state"] == GameState.OVERWORLD: 
        return False

    pokemon = GetParty()[0] if starter else GetOpponent()
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
            while GetTrainer()["state"] != GameState.OVERWORLD: 
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

        # If total encounters modulo config["save_every_x_encounters"] is 0, save the game
        # Save every x encounters to prevent data loss (pickup, levels etc)
        total_encounters = stats["totals"]["encounters"] + stats["totals"]["shiny_encounters"]
        if config["periodic_save"] and total_encounters % config["save_every_x_encounters"] == 0 and total_encounters != 0:
            save_game()

        if replace_battler:
            if not config["cycle_lead_pokemon"]:
                log.info("Lead Pokemon can no longer battle. Ending the script!")
                flee_battle()
                return
            else:
                start_menu("pokemon")

                # Find another healthy battler
                party_pp = [0, 0, 0, 0, 0, 0]
                i = 0
                for mon in GetParty():
                    if mon is None:
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
                    log.info("Ran out of Pokemon to battle with. Ending the script!")
                    os._exit(1)

                lead = GetParty()[lead_idx]
                if lead is not None:
                    log.info(f"Replacing lead battler with {lead['speciesName']} (Party slot {lead_idx})")

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
                
                log.info("Replaced lead Pokemon!")

                for i in range(0, 5):
                    press_button("B")
                    wait_frames(15)
        return False

#def mem_sendInputs(): TODO reimplement with new input system
#    while True:
#        try:
#            press_input_mmap.seek(0)
#            press_input_mmap.write(bytes(json.dumps(press_input), encoding="utf-8"))
#            hold_input_mmap.seek(0)
#            hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))
#        except Exception as e:
#            log.exception(str(e))
#            continue
#        time.sleep(0.08) #The less sleep the better but without sleep it will hit CPU hard

def mainLoop():
    global last_opponent_personality
    
    if config["save_game_on_start"]: 
        save_game()
    
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
                        return
                case other:
                    log.exception("Couldn't interpret bot mode: " + config["bot_mode"])
                    return
        else:
            opponent = GetOpponent()
            if opponent:
                last_opponent_personality = opponent["personality"]
            release_all_inputs()
            time.sleep(0.2)
        wait_frames(1)

# TODO move to own file in modes/emerald/ folder
def mode_spin(): # TODO check if players direction changes, if not spam B (dumb Pokenav)
    trainer = GetTrainer()
    home_coords = (trainer["posX"], trainer["posY"])
    log.info(f"Spinning on the spot, home position is {home_coords}")
    while True:
        trainer = GetTrainer()
        if opponent_changed(): identify_pokemon()
        if home_coords != (trainer["posX"], trainer["posY"]): # Note: this will likely fail if the trainer accidentally changes map bank/ID
            log.info(f"Trainer has moved off home position, pathing back to {home_coords}...")
            follow_path([
                (home_coords[0], trainer["posY"]), 
                (trainer["posX"], home_coords[1])
            ], exit_when_stuck=True)
        directions = ["Up", "Right", "Down", "Left"]
        directions.remove(trainer["facing"])
        press_button(random.choice(directions))
        wait_frames(2)

# TODO move to own file in modes/emerald/ folder
def mode_beldum():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if (not player_on_map(MapDataEnum.MOSSDEEP_CITY_H.value) or not ((x == 3 and y == 3) or (x == 4 and y == 2))):
        log.info("Please face the player toward the Pokeball in Steven's house after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon("Beldum")

# TODO move to own file in modes/emerald/ folder
def mode_castform():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if (not player_on_map(MapDataEnum.ROUTE_119_B.value) or not ((x == 2 and y == 3) or (x == 3 and y == 2) or (x == 1 and y == 2))):
        log.info("Please face the player toward the scientist after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon("Castform")

# TODO move to own file in modes/emerald/ folder
def mode_fossil():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if not player_on_map(MapDataEnum.RUSTBORO_CITY_B.value) or y != 8 and not (x == 13 or x == 15):
        log.info("Please face the player toward the Fossil researcher after handing it over, re-entering the room, and saving the game. Then restart the script.")
        os._exit(1)

    collect_gift_mon(config["fossil"])

# TODO move to own file in modes/emerald/ folder
def mode_johtoStarters():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if (not player_on_map(MapDataEnum.LITTLEROOT_TOWN_D.value) or not (y == 5 and x >= 8 and x <= 10)):
        log.info("Please face the player toward a Pokeball in Birch's Lab after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon(config["johto_starter"])

# TODO move to own file in modes/emerald/ folder
def collect_gift_mon(target: str):
    rng_frames = get_rngState(GetTrainer()["tid"], target)
    party_size = len(GetParty())

    if party_size == 6:
        log.info("Please leave at least one party slot open, then restart the script.")
        os._exit(1)

    while True:
        # Button mash through intro/title
        while GetTrainer()["state"] != GameState.OVERWORLD:
            press_button("A")
            wait_frames(8)
        
        # Text goes faster with B held
        hold_button("B")

        while len(GetParty()) == party_size:
            emu = GetEmu()
            if emu["rngState"] in rng_frames:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
                continue
            press_button("A")
            wait_frames(5)
        
        rng_frames["rngState"].append(emu["rngState"])
        write_file(f"stats/{GetTrainer()['tid']}/{target.lower()}.json", json.dumps(rng_frames, indent=4, sort_keys=True))

        mon = GetParty()[party_size]
        
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

# TODO move to own file in modes/emerald/ folder
def mode_regiTrio():
    if (not player_on_map(MapDataEnum.DESERT_RUINS.value) and
        not player_on_map(MapDataEnum.ISLAND_CAVE.value) and
        not player_on_map(MapDataEnum.ANCIENT_TOMB.value)):
        log.info("Please place the player below the target Regi in Desert Ruins, Island Cave or Ancient Tomb, then restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["Up", "A"])

        identify_pokemon()

        while not GetTrainer()["state"] == GameState.OVERWORLD:
            continue

        # Exit and re-enter
        press_button("B")
        follow_path([
            (8, 21), 
            (8, 11)
        ])

# TODO move to own file in modes/emerald/ folder
def mode_deoxysPuzzle(do_encounter: bool = True):
    def retry_puzzle_if_stuck(success: bool):
        if not success: 
            reset_game()
            return True

    if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
        log.info("Please place the player below the triangle at its starting position on Birth Island, then save before restarting the script.")
        os._exit(1)

    delay = 4

    while True:
        while not GetTrainer()["state"] == GameState.OVERWORLD:
            emu_combo(["A", 8])

        wait_frames(60)

        # Center
        if GetTrainer()["posY"] != 13:
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
            log.info("Deoxys puzzle completed. Saving game and starting resets...")
            config["bot_mode"] = "deoxys resets"
            config["deoxys_puzzle_solved"] = True
            save_game()
            wait_frames(10)
            return True

        while not opponent_changed():
            press_button("A")
            wait_frames(1)

        identify_pokemon()

        while not GetTrainer()["state"] == GameState.OVERWORLD:
            continue

        for i in range(0, 4):
            press_button("B")
            wait_frames(15)

        # Exit and re-enter
        follow_path([
            (15, 99, (26, 59)), 
            (8, -99, MapDataEnum.BIRTH_ISLAND.value)
        ])

# TODO move to own file in modes/emerald/ folder
def mode_deoxysResets():
    if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
        log.info("Please place the player below the triangle at its final position on Birth Island, then save before restarting the script.")
        os._exit(1)

    deoxys_frames = get_rngState(GetTrainer()["tid"], "deoxys")

    while True:
        # Mash A to reach overworld from intro/title
        while GetTrainer()["state"] != GameState.OVERWORLD:
            emu_combo(["A", 8])

        # Wait for area to load properly
        wait_frames(60)

        if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
            log.info("Please place the player below the triangle at its final position on Birth Island, then save before restarting the script.")
            os._exit(1)

        while True:
            emu = GetEmu()
            if emu["rngState"] in deoxys_frames:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
            else:
                while not opponent_changed():
                    emu_combo(["A", 8])

                deoxys_frames["rngState"].append(emu["rngState"])
                write_file(f"stats/{GetTrainer()['tid']}/deoxys.json", json.dumps(deoxys_frames, indent=4, sort_keys=True))
                identify_pokemon()
            break
        continue

# TODO move to own file in modes/emerald/ folder
def mode_sweetScent():
    log.info(f"Using Sweet Scent...")
    start_menu("pokemon")
    press_button("A") # Select first pokemon in party

    # Search for sweet scent in menu
    while not find_image("sweet_scent.png"): 
        press_button("Down")

    emu_combo(["A", 300]) # Select sweet scent and wait for animation
    identify_pokemon()

# TODO move to own file in modes/emerald/ folder
def mode_bunnyHop():
    log.info("Bunny hopping...")
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

# TODO move to own file in modes/emerald/ folder
def mode_move_between_coords():
    coords = config["coords"]
    pos1, pos2 = coords["pos1"], coords["pos2"]

    while True:
        foe_personality = last_opponent_personality

        while foe_personality == last_opponent_personality:
            follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])

        identify_pokemon()

        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue

# TODO move to own file in modes/emerald/ folder
def mode_move_until_obstructed():
    direction = config["direction"].lower()

    while True:
        pos1, pos2 = None, None
        foe_personality = last_opponent_personality
        log.info(f"Pathing {direction} until obstructed...")

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

        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue

# TODO move to own file in modes/emerald/ folder
def mode_fishing():
    log.info(f"Fishing...")
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

# TODO move to own file in modes/emerald/ folder
def mode_starters():
    choice = config["starter"].lower()
    starter_frames = get_rngState(GetTrainer()['tid'], choice)

    if choice not in ["treecko", "torchic", "mudkip"]:
        log.info(f"Unknown starter \"{config['starter']}\". Please edit the value in config.yml and restart the script.")
        os._exit(1)

    log.info(f"Soft resetting starter Pokemon...")
    
    while True:
        release_all_inputs()

        while GetTrainer()["state"] != GameState.OVERWORLD: 
            press_button("A")

        # Short delay between A inputs to prevent accidental selection confirmations
        while GetTrainer()["state"] == GameState.OVERWORLD: 
            emu_combo(["A", 10])

        # Press B to back out of an accidental selection when scrolling to chosen starter
        if choice == "mudkip":
            while not find_image("mudkip.png"): 
                emu_combo(["B", "Right"])
        elif choice == "treecko":
            while not find_image("treecko.png"): 
                emu_combo(["B", "Left"])

        while True:
            emu = GetEmu()
            if emu["rngState"] in starter_frames["rngState"]:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
            else:
                while GetTrainer()["state"] == GameState.MISC_MENU: 
                    press_button("A")

                starter_frames["rngState"].append(emu["rngState"])
                write_file(f"stats/{GetTrainer()['tid']}/{choice}.json", json.dumps(starter_frames, indent=4, sort_keys=True))

                while not find_image("battle/fight.png"):
                    press_button("B")

                    if not config["do_realistic_hunt"] and GetParty()[0]:
                        if identify_pokemon(starter=True):
                            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                        else:
                            reset_game()
                            break
                else:
                    while True:
                        if GetParty()[0]:
                            if identify_pokemon(starter=True): 
                                input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                            else:
                                reset_game()
                                break
            continue

# TODO move to own file in modes/emerald/ folder
def mode_rayquaza():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.SKY_PILLAR_G.value) or
        not (trainer["posX"] == 14 and trainer["posY"] <= 12)):
        log.info("Please place the player below Rayquaza at the Sky Pillar and restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["A", "Up"]) # Walk up toward Rayquaza while mashing A
        
        identify_pokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
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

# TODO move to own file in modes/emerald/ folder
def mode_groudon():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.TERRA_CAVE_A.value) or
        not 11 <= trainer["posX"] <= 20 and 26 <= trainer["posY"] <= 27):
        log.info("Please place the player below Groudon in Terra Cave and restart the script.")
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

# TODO move to own file in modes/emerald/ folder
def mode_kyogre():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.MARINE_CAVE_A.value) or
        not 5 <= trainer["posX"] <= 14 and 26 <= trainer["posY"] <= 27):
        log.info("Please place the player below Kyogre in Marine Cave and restart the script.")
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

# TODO move to own file in modes/emerald/ folder
def mode_farawayMew():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.FARAWAY_ISLAND.value) or not (22 <= trainer["posX"] <= 23 and 8 <= trainer["posY"] <= 10)):
        log.info("Please place the player below the entrance to Mew's area, then restart the script.")
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
            (GetTrainer()["posX"], 16),
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

# TODO move to own file in modes/emerald/ folder
def mode_southernIsland():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.SOUTHERN_ISLAND_A.value) or
        not 5 <= trainer["posX"] == 13 and trainer["posY"] >= 12):
        log.info("Please place the player below the sphere on Southern Island and restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["A", "Up"])

        identify_pokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue

        # Exit and re-enter
        press_button("B")
        follow_path([
            (13, 99, MapDataEnum.SOUTHERN_ISLAND.value), 
            (14, -99, MapDataEnum.SOUTHERN_ISLAND_A.value)
        ])

# TODO move to own file in modes/emerald/ folder
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
    # Validate python version
    min_major = 3
    min_minor = 10
    v_major = sys.version_info[0]
    v_minor = sys.version_info[1]

    if v_major < min_major or v_minor < min_minor:
        log.error(f"\n\nPython version is out of date! (Minimum required version for pokebot is {min_major}.{min_minor})\nPlease install the latest version at https://www.python.org/downloads/\n")
        os._exit(1)

    log.info(f"Running pokebot on Python {v_major}.{v_minor}")

    # Confirm that the Lua Console is open by doing a test screenshot
    mmap_screenshot_size, mmap_screenshot_file = 24576, "bizhawk_screenshot-" + config["bot_instance_id"]
    can_start_bot = True

    try:
        shmem = mmap.mmap(0, mmap_screenshot_size, mmap_screenshot_file)
        screenshot = Image.open(io.BytesIO(shmem))
    except:
        log.error("\n\nUnable to initialize pokebot!\nPlease confirm that the Lua Console is open in BizHawk, and that it remains open while the bot is active.\nIt can be opened through 'Tools > Lua Console'.\n\nStarting in dashboard-only mode...\n")
        can_start_bot = False

    last_trainer_state, last_opponent_personality = None, None
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    # Main bot functionality
    if can_start_bot:
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
        
        #send_inputs = Thread(target=mem_sendInputs) TODO Use another buffer to throttle inputs and use this thread again
        #send_inputs.start()

        main_loop = Thread(target=mainLoop)
        main_loop.start()

    os.makedirs("stats", exist_ok=True) # Sets up stats files if they don't exist

    totals = read_file("stats/totals.json")
    stats = json.loads(totals) if totals else {"pokemon": {}, "totals": {"longest_phase_encounters": 0, "shortest_phase_encounters": "-", "phase_lowest_sv": 99999, "phase_lowest_sv_pokemon": "", "encounters": 0, "phase_encounters": 0, "shiny_average": "-", "shiny_encounters": 0}}

    encounters = read_file("stats/encounter_log.json")
    encounter_log = json.loads(encounters) if encounters else {"encounter_log": []}
    
    shinies = read_file("stats/shiny_log.json")
    shiny_log = json.loads(shinies) if shinies else {"shiny_log": []}
    pokedex_list = json.loads(read_file("data/pokedex.json"))

    if config["ui"]:
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
        url=f"http://{config['ui_ip']}:{config['ui_port']}/dashboard"
        window = webview.create_window("PokeBot", url=url, width=config["ui_width"], height=config["ui_height"], resizable=True, hidden=False, frameless=False, easy_drag=True, fullscreen=False, text_select=True, zoomable=True)
        window.events.closed += on_window_close
        webview.start()

except Exception as e:
    log.exception(str(e))
    os._exit(1)
