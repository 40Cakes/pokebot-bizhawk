import os
import sys
import json
import time
from threading import Thread
import logging
from logging.handlers import RotatingFileHandler

from data.MapData import mapRSE #mapFRLG
from modules.Config import GetConfig
from modules.Files import ReadFile
from modules.Inputs import ReleaseAllInputs, PressButton, WaitFrames
from modules.Stats import OpponentChanged
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetOpponent, GetParty
from modules.mmf.Screenshot import GetScreenshot
from modules.mmf.Trainer import GetTrainer
from modules.gen3.Spin import Spin

config = GetConfig()

def get_rngState(tid: str, mon: str):
    file = ReadFile(f"stats/{tid}/{mon.lower()}.json")
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
    console_handler.setLevel(logging.DEBUG)

    # Create logger and attach handlers
    log = logging.getLogger('root')
    log.setLevel(logging.INFO)
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
        input("Press enter to continue...")
        os._exit(1)

    log.info(f"Running pokebot on Python {v_major}.{v_minor}")

    while True:
        if GetTrainer():
            break
        else:
            log.error("\n\nFailed to get trainer data, unable to initialize pokebot!\nPlease confirm that `pokebot.lua` is running in BizHawk, keep the Lua console open while the bot is active.\nIt can be opened through 'Tools > Lua Console'.\n")
            input("Press enter to try again...")

    config = GetConfig() # Load config
    log.info(f"Mode: {config['bot_mode']}")
        
    item_list = json.loads(ReadFile("data/items.json"))
    route_list = json.loads(ReadFile("data/routes-emerald.json"))

    emu = GetEmu()
    log.info("Detected game: " + emu["detectedGame"])
    if any([x in emu["detectedGame"] for x in ["Emerald"]]): # "Ruby", "Sapphire"
        MapDataEnum = mapRSE
    #if any([x in emu["detectedGame"] for x in ["FireRed", "LeafGreen"]]):
    #    MapDataEnum = mapFRLG
    else:
        log.error("Unsupported game detected...")
        input("Press enter to continue...")
        os._exit(1)    

    if config["ui"]["enable"]:
        import webview
        from modules.FlaskServer import httpServer

        def on_window_close():
            ReleaseAllInputs()

            log.info("Dashboard closed on user input...")
            os._exit(1)

        server = Thread(target=httpServer)
        server.start()

        # Webview UI
        url=f"http://{config['ui']['ip']}:{config['ui']['port']}/dashboard"
        window = webview.create_window("PokeBot", url=url, width=config["ui"]["width"], height=config["ui"]["height"], resizable=True, hidden=False, frameless=False, easy_drag=True, fullscreen=False, text_select=True, zoomable=True)
        window.events.closed += on_window_close
        webview.start()
    
    ReleaseAllInputs()
    PressButton("SaveRAM") # Flush Bizhawk SaveRAM to disk

    while True:
        if GetTrainer() and GetEmu(): # Test that emulator information is accessible:
            match config["bot_mode"]:
                case "manual":
                    while not OpponentChanged(): 
                        WaitFrames(20)
                    identify_pokemon()
                case "spin":
                    Spin()
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
                        input("Press enter to continue...")
                case other:
                    log.exception("Couldn't interpret bot mode: " + config["bot_mode"])
                    input("Press enter to continue...")
    else:
        ReleaseAllInputs()
        time.sleep(0.2)
    WaitFrames(1)

except Exception as e:
    log.exception(str(e))
    os._exit(1)
