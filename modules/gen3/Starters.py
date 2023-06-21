import json
import logging
import os

from modules.data.GameState import GameState
from modules.Config import GetConfig
from modules.Files import WriteFile
from modules.Image import DetectTemplate
from modules.Inputs import ButtonCombo, ReleaseAllInputs, PressButton
from modules.Menuing import ResetGame
from modules.Stats import GetRNGState, EncounterPokemon
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetParty
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)
config = GetConfig()


def ModeStarters():
    try:
        starter_choice = config["starter"].lower()
        log.debug(f"Starter choice: {starter_choice}")
        starter_frames = GetRNGState(GetTrainer()['tid'], starter_choice)

        if starter_choice not in ["treecko", "torchic", "mudkip"]:
            log.info(f"Unknown starter \"{config['starter']}\". Please edit the value in config.yml and restart the "
                     f"script.")
            input("Press enter to continue...")
            os._exit(1)

        log.info(f"Soft resetting starter Pokemon...")

        while True:
            ReleaseAllInputs()

            while GetTrainer()["state"] != GameState.OVERWORLD:
                PressButton("A")

            # Short delay between A inputs to prevent accidental selection confirmations
            while GetTrainer()["state"] == GameState.OVERWORLD:
                ButtonCombo(["A", 10])

            # Press B to back out of an accidental selection when scrolling to chosen starter
            if starter_choice == "mudkip":
                while not DetectTemplate("mudkip.png"):
                    ButtonCombo(["B", "Right"])
            elif starter_choice == "treecko":
                while not DetectTemplate("treecko.png"):
                    ButtonCombo(["B", "Left"])

            while True:
                emu = GetEmu()
                if emu["rngState"] in starter_frames["rngState"]:
                    log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
                else:
                    while GetTrainer()["state"] == GameState.MISC_MENU:
                        PressButton("A")

                    starter_frames["rngState"].append(emu["rngState"])
                    WriteFile(f"stats/{GetTrainer()['tid']}/{starter_choice}.json",
                              json.dumps(starter_frames, indent=4, sort_keys=True))

                    while not DetectTemplate("battle/fight.png"):
                        PressButton("B")

                        if config["mem_hacks"] and GetParty()[0]:
                            if EncounterPokemon(starter=True):
                                input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua "
                                      "script so you can provide inputs). Press Enter to continue...")
                            else:
                                ResetGame()
                                break
                    else:
                        if GetParty()[0]:
                            if EncounterPokemon(starter=True):
                                input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua "
                                      "script so you can provide inputs). Press Enter to continue...")
                            else:
                                ResetGame()
                                break
                continue
    except Exception as e:
        log.exception(str(e))
