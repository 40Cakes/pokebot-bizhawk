import os
import sys
import json
from threading import Thread
import logging
from logging.handlers import RotatingFileHandler

from modules.Config import GetConfig
from modules.data.MapData import mapRSE #mapFRLG
from modules.Files import ReadFile
from modules.Inputs import ReleaseAllInputs, PressButton, WaitFrames
from modules.Stats import EncounterPokemon, OpponentChanged
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetOpponent, GetParty
from modules.mmf.Screenshot import GetScreenshot
from modules.mmf.Trainer import GetTrainer
from modules.gen3.General import ModeBonk, ModeBunnyHop, ModeFishing, ModeCoords, ModeSpin, ModeSweetScent, ModePremierBalls
from modules.gen3.Starters import ModeStarters # ModeJohtoStarters
from modules.gen3.Legendaries import ModeGroudon, ModeKyogre, ModeRayquaza, ModeMew, ModeRegis, ModeSouthernIsland, ModeDeoxysPuzzle, ModeDeoxysResets 
from modules.gen3.GiftPokemon import ModeCastform, ModeBeldum, ModeFossil

config = GetConfig()

def MainLoop():
    # This is the main loop that runs in a thread
    # TODO modes should always return True once the trainer is back in the overworld after an encounter, else False - then go into a "recovery" mode
    # TODO after each pass, read updated config that gets POSTed by the UI

    ReleaseAllInputs()
    PressButton("SaveRAM") # Flush Bizhawk SaveRAM to disk

    while True:
        if GetTrainer() and GetEmu(): # Test that emulator information is accessible and valid
            match config["bot_mode"]:
                case "manual":
                    while not OpponentChanged(): 
                        WaitFrames(20)
                    EncounterPokemon()
                case "spin":
                    ModeSpin()
                case "sweet scent":
                    ModeSweetScent()
                case "bunny hop":
                    ModeBunnyHop()
                case "move between coords":
                    ModeCoords()
                case "bonk":
                    ModeBonk()
                case "fishing":
                    ModeFishing()
                case "starters":
                    ModeStarters()
                case "rayquaza":
                    ModeRayquaza()
                case "groudon":
                    ModeGroudon()
                case "kyogre":
                    ModeKyogre()
                case "southern island":
                    ModeSouthernIsland()
                case "mew":
                    ModeMew()
                case "regis":
                    ModeRegis()
                case "deoxys runaways":
                    ModeDeoxysPuzzle()
                case "deoxys resets":
                    if config["deoxys_puzzle_solved"]:
                        ModeDeoxysResets()
                    else:
                        ModeDeoxysPuzzle(False)
                case "fossil":
                    ModeFossil()
                case "castform":
                    ModeCastform()
                case "beldum":
                    ModeBeldum()
                case "johto starters":
                    ModeJohtoStarters()
                case "buy premier balls":
                    purchased = ModePremierBalls()

                    if not purchased:
                        log.info(f"Ran out of money to buy Premier Balls. Script ended.")
                        input("Press enter to continue...")
                case other:
                    log.exception("Couldn't interpret bot mode: " + config["bot_mode"])
                    input("Press enter to continue...")
        else:
            ReleaseAllInputs()
            WaitFrames(5)

try:
    # Set up log handler
    LogFormatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(line:%(lineno)d) %(message)s')
    ConsoleFormatter = logging.Formatter('%(asctime)s - %(message)s')
    LogPath = "logs"
    LogFile = f"{LogPath}/debug.log"
    os.makedirs(LogPath, exist_ok=True) # Create logs directory if not exist

    # Set up log file rotation handler
    LogHandler = RotatingFileHandler(LogFile, mode='a', maxBytes=20*1024*1024, backupCount=5, encoding=None, delay=0)
    LogHandler.setFormatter(LogFormatter)
    LogHandler.setLevel(logging.INFO)

    # Set up console log stream handler
    ConsoleHandler = logging.StreamHandler()
    ConsoleHandler.setFormatter(ConsoleFormatter)
    ConsoleHandler.setLevel(logging.DEBUG)

    # Create logger and attach handlers
    log = logging.getLogger('root')
    log.setLevel(logging.INFO)
    log.addHandler(LogHandler)
    log.addHandler(ConsoleHandler)
except Exception as e:
    print(str(e))
    input("Press enter to continue...")
    os._exit(1)

try:
    # Validate python version
    MinMajorVersion = 3
    MinMinorVersion = 10
    MajorVersion = sys.version_info[0]
    MinorVersion = sys.version_info[1]

    if MajorVersion < MinMajorVersion or MinorVersion < MinMinorVersion:
        log.error(f"\n\nPython version is out of date! (Minimum required version for pokebot is {MinMajorVersion}.{MinMinorVersion})\nPlease install the latest version at https://www.python.org/downloads/\n")
        input("Press enter to continue...")
        os._exit(1)

    log.info(f"Running pokebot on Python {MajorVersion}.{MinorVersion}")

    while True:
        if GetTrainer():
            break
        else:
            log.error("\n\nFailed to get trainer data, unable to initialize pokebot!\nPlease confirm that `pokebot.lua` is running in BizHawk, keep the Lua console open while the bot is active.\nIt can be opened through 'Tools > Lua Console'.\n")
            input("Press enter to try again...")

    config = GetConfig() # Load config
    log.info(f"Mode: {config['bot_mode']}")

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

    main = Thread(target=MainLoop)
    main.start()

    if config["server"]["enable"]:
        from modules.FlaskServer import httpServer

        server = Thread(target=httpServer)
        server.start()

    if config["ui"]["enable"]:
        import webview
        def OnWindowClose():
            ReleaseAllInputs()
            log.info("Dashboard closed on user input...")
            os._exit(1)

        url=f"http://{config['server']['ip']}:{config['server']['port']}/dashboard"
        window = webview.create_window("PokeBot", url=url, width=config["ui"]["width"], height=config["ui"]["height"], resizable=True, hidden=False, frameless=False, easy_drag=True, fullscreen=False, text_select=True, zoomable=True)
        window.events.closed += OnWindowClose
        webview.start()
    else:
        main.join()

except Exception as e:
    log.exception(str(e))
    os._exit(1)
