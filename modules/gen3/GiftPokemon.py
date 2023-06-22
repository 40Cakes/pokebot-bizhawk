import json
import os
import logging

from modules.Config import GetConfig
from modules.data.GameState import GameState
from modules.Files import WriteFile
from modules.Image import DetectTemplate
from modules.Inputs import ButtonCombo, HoldButton, PressButton, ReleaseButton, WaitFrames
from modules.Menuing import StartMenu
from modules.Navigation import MapDataEnum, PlayerOnMap
from modules.Stats import GetRNGState, LogEncounter
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetParty
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)
config = GetConfig()


def CollectGiftMon(target: str):
    rng_frames = GetRNGState(GetTrainer()["tid"], target)
    party_size = len(GetParty())

    if party_size == 6:
        log.info("Please leave at least one party slot open, then restart the script.")
        os._exit(1)

    while True:
        # Button mash through intro/title
        while GetTrainer()["state"] != GameState.OVERWORLD:
            PressButton("A")
            WaitFrames(8)

        # Text goes faster with B held
        HoldButton("B")

        emu = GetEmu()
        while len(GetParty()) == party_size:
            emu = GetEmu()
            if emu["rngState"] in rng_frames:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
                continue
            PressButton("A")
            WaitFrames(5)

        rng_frames["rngState"].append(emu["rngState"])
        WriteFile(f"stats/{GetTrainer()['tid']}/{target.lower()}.json",
                  json.dumps(rng_frames, indent=4, sort_keys=True))

        mon = GetParty()[party_size]

        # Open the menu and find Gift mon in party
        ReleaseButton("B")

        if config["mem_hacks"] and not mon["shiny"]:
            LogEncounter(mon)
            HoldButton("Power")
            WaitFrames(60)
            ReleaseButton("Power")
            continue

        while not DetectTemplate("start_menu/select.png"):
            PressButton("B")

            for _ in range(4):
                if DetectTemplate("start_menu/select.png"):
                    break
                WaitFrames(1)

        while DetectTemplate("start_menu/select.png"):
            PressButton("B")

            for _ in range(4):
                if not DetectTemplate("start_menu/select.png"):
                    break
                WaitFrames(1)

        StartMenu("pokemon")

        WaitFrames(60)

        for _ in range(party_size):
            ButtonCombo(["Down", 15])

        ButtonCombo(["A", 15, "A", 60])

        LogEncounter(mon)

        if not mon["shiny"]:
            HoldButton("Power")
            WaitFrames(60)
            ReleaseButton("Power")
        else:
            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can "
                  "provide inputs). Press Enter to continue...")


def ModeBeldum():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if not PlayerOnMap(MapDataEnum.MOSSDEEP_CITY_H.value) or not ((x == 3 and y == 3) or (x == 4 and y == 2)):
        log.info("Please face the player toward the Pokeball in Steven's house after saving the game, then restart the "
                 "script.")
        os._exit(1)

    CollectGiftMon("Beldum")


def ModeCastform():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if (not PlayerOnMap(MapDataEnum.ROUTE_119_B.value) or not (
            (x == 2 and y == 3) or (x == 3 and y == 2) or (x == 1 and y == 2))):
        log.info("Please face the player toward the scientist after saving the game, then restart the script.")
        os._exit(1)

    CollectGiftMon("Castform")


def ModeFossil():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if not PlayerOnMap(MapDataEnum.RUSTBORO_CITY_B.value) or y != 8 and not (x == 13 or x == 15):
        log.info("Please face the player toward the Fossil researcher after handing it over, re-entering the room, "
                 "and saving the game. Then restart the script.")
        os._exit(1)

    CollectGiftMon(config["fossil"])


def ModeJohtoStarters():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if not PlayerOnMap(MapDataEnum.LITTLEROOT_TOWN_E.value) or not (y == 5 and 8 <= x <= 10):
        log.info("Please face the player toward a Pokeball in Birch's Lab after saving the game, then restart the "
                 "script.")
        os._exit(1)

    CollectGiftMon(config["johto_starter"])
