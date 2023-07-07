import json
import logging
import os

from modules.Config import GetConfig
from modules.data.GameState import GameState
from modules.Files import WriteFile
from modules.Inputs import ButtonCombo, HoldButton, PressButton, WaitFrames
from modules.Menuing import ResetGame, SaveGame
from modules.Navigation import Bonk, FollowPath, MapDataEnum, PlayerOnMap
from modules.Stats import EncounterPokemon, GetRNGState, OpponentChanged
from modules.mmf.Emu import GetEmu
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)
config = GetConfig()


def ModeGroudon():
    trainer = GetTrainer()
    if (not PlayerOnMap(MapDataEnum.TERRA_CAVE_A.value) or
            not 11 <= trainer["posX"] <= 20 and 26 <= trainer["posY"] <= 27):
        log.info("Please place the player below Groudon in Terra Cave and restart the script.")
        os._exit(1)

    while True:
        FollowPath([(17, 26)])

        EncounterPokemon()

        # Exit and re-enter
        FollowPath([
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


def ModeKyogre():
    trainer = GetTrainer()
    if (not PlayerOnMap(MapDataEnum.MARINE_CAVE_A.value) or
            not 5 <= trainer["posX"] <= 14 and 26 <= trainer["posY"] <= 27):
        log.info("Please place the player below Kyogre in Marine Cave and restart the script.")
        os._exit(1)

    while True:
        FollowPath([(9, 26)])

        EncounterPokemon()

        # Exit and re-enter
        FollowPath([
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


def ModeRayquaza():
    trainer = GetTrainer()
    if (not PlayerOnMap(MapDataEnum.SKY_PILLAR_G.value) or
            not (trainer["posX"] == 14 and trainer["posY"] <= 12)):
        log.info("Please place the player below Rayquaza at the Sky Pillar and restart the script.")
        os._exit(1)

    while True:
        while not OpponentChanged():
            ButtonCombo(["A", "Up"])  # Walk up toward Rayquaza while mashing A

        EncounterPokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            WaitFrames(1)
            continue

        # Exit and re-enter
        PressButton("B")
        FollowPath([
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


def ModeMew():
    trainer = GetTrainer()
    if (not PlayerOnMap(MapDataEnum.FARAWAY_ISLAND.value) or not (
            22 <= trainer["posX"] <= 23 and 8 <= trainer["posY"] <= 10)):
        log.info("Please place the player below the entrance to Mew's area, then restart the script.")
        os._exit(1)
        return

    while True:
        # Enter main area
        while PlayerOnMap(MapDataEnum.FARAWAY_ISLAND.value):
            FollowPath([
                (22, 8),
                (22, -99, MapDataEnum.FARAWAY_ISLAND_A.value)
            ])

        WaitFrames(30)
        HoldButton("B")

        FollowPath([
            (GetTrainer()["posX"], 16),
            (16, 16)
        ])
        # 
        # Follow Mew up while mashing A
        HoldButton("Up")

        while not OpponentChanged():
            ButtonCombo(["A", 8])

        EncounterPokemon()

        for _ in range(6):
            PressButton("B")
            WaitFrames(10)

        # Exit to entrance area
        FollowPath([
            (16, 16),
            (12, 16),
            (12, 99, MapDataEnum.FARAWAY_ISLAND.value)
        ])


def ModeRegis():
    if (not PlayerOnMap(MapDataEnum.DESERT_RUINS.value) and
            not PlayerOnMap(MapDataEnum.ISLAND_CAVE.value) and
            not PlayerOnMap(MapDataEnum.ANCIENT_TOMB.value)):
        log.info("Please place the player below the target Regi in Desert Ruins, Island Cave or Ancient Tomb, "
                 "then restart the script.")
        os._exit(1)

    while True:
        while not OpponentChanged():
            ButtonCombo(["Up", "A"])

        EncounterPokemon()

        while not GetTrainer()["state"] == GameState.OVERWORLD:
            continue

        # Exit and re-enter
        PressButton("B")
        FollowPath([
            (8, 21),
            (8, 11)
        ])


def ModeSouthernIsland():
    trainer = GetTrainer()
    if (not PlayerOnMap(MapDataEnum.SOUTHERN_ISLAND_A.value) or
            not 5 <= trainer["posX"] == 13 and trainer["posY"] >= 12):
        log.info("Please place the player below the sphere on Southern Island and restart the script.")
        os._exit(1)

    while True:
        while not OpponentChanged():
            ButtonCombo(["A", "Up"])

        EncounterPokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            WaitFrames(1)
            continue

        # Exit and re-enter
        PressButton("B")
        FollowPath([
            (13, 99, MapDataEnum.SOUTHERN_ISLAND.value),
            (14, -99, MapDataEnum.SOUTHERN_ISLAND_A.value)
        ])


def ModeDeoxysPuzzle(do_encounter: bool = True):
    def StuckRetryPuzzle(success: bool):
        if not success:
            ResetGame()
            return True

    if not PlayerOnMap(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
        log.info("Please place the player below the triangle at its starting position on Birth Island, then save before"
                 " restarting the script.")
        os._exit(1)

    delay = 4

    while True:
        while not GetTrainer()["state"] == GameState.OVERWORLD:
            ButtonCombo(["A", 8])

        WaitFrames(60)

        # Center
        if GetTrainer()["posY"] != 13:
            Bonk("Up")
        ButtonCombo([delay, "A"])

        # Left
        FollowPath([(15, 14), (12, 14)])
        ButtonCombo([delay, "Left", "A", delay])

        # Top
        if StuckRetryPuzzle(FollowPath([(15, 14), (15, 9)], True, True)): continue
        ButtonCombo([delay, "Up", "A", delay])

        # Right
        if StuckRetryPuzzle(FollowPath([(15, 14), (18, 14)], True, True)): continue
        ButtonCombo([delay, "Right", "A", delay])

        # Middle Left
        if StuckRetryPuzzle(FollowPath([(15, 14), (15, 11), (13, 11)], True, True)): continue
        ButtonCombo([delay, "Left", "A", delay])

        # Middle Right
        FollowPath([(17, 11)])
        ButtonCombo([delay, "Right", "A", delay])

        # Bottom
        if StuckRetryPuzzle(FollowPath([(15, 11), (15, 13)], True, True)): continue
        ButtonCombo([delay, "Down", "A", delay])

        # Bottom Left
        FollowPath([(15, 14), (12, 14)])
        ButtonCombo([delay, "Left", "A", delay])

        # Bottom Right
        FollowPath([(18, 14)])
        ButtonCombo([delay, "Right", "A", delay])

        # Bottom
        FollowPath([(15, 14)])
        ButtonCombo([delay, "Down", delay, "A", delay])

        # Center
        if StuckRetryPuzzle(FollowPath([(15, 11)], True, True)): continue

        if not do_encounter:
            log.info("Deoxys puzzle completed. Saving game and starting resets...")
            config["bot_mode"] = "deoxys resets"
            config["deoxys_puzzle_solved"] = True
            SaveGame()
            WaitFrames(10)
            return True

        while not OpponentChanged():
            PressButton("A")
            WaitFrames(1)

        EncounterPokemon()

        while not GetTrainer()["state"] == GameState.OVERWORLD:
            continue

        for i in range(0, 4):
            PressButton("B")
            WaitFrames(15)

        # Exit and re-enter
        FollowPath([
            (15, 99, (26, 59)),
            (8, -99, MapDataEnum.BIRTH_ISLAND.value)
        ])


def ModeDeoxysResets():
    if not PlayerOnMap(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
        log.info("Please place the player below the triangle at its final position on Birth Island, then save before "
                 "restarting the script.")
        os._exit(1)

    deoxys_frames = GetRNGState(GetTrainer()["tid"], "deoxys")

    while True:
        # Mash A to reach overworld from intro/title
        while GetTrainer()["state"] != GameState.OVERWORLD:
            ButtonCombo(["A", 8])

        # Wait for area to load properly
        WaitFrames(60)

        if not PlayerOnMap(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
            log.info("Please place the player below the triangle at its final position on Birth Island, then save "
                     "before restarting the script.")
            os._exit(1)

        while True:
            emu = GetEmu()
            if emu["rngState"] in deoxys_frames:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
            else:
                while not OpponentChanged():
                    ButtonCombo(["A", 8])

                deoxys_frames["rngState"].append(emu["rngState"])
                WriteFile(f"stats/{GetTrainer()['tid']}/deoxys.json",
                          json.dumps(deoxys_frames, indent=4, sort_keys=True))
                EncounterPokemon()
            break
        continue


def ModeHoOh():
    if not PlayerOnMap(MapDataEnum.NAVEL_ROCK_I.value) and GetTrainer()["posX"] == 12:
        log.info("Please place the player on the steps in front of Ho-oh at Navel Rock and restart the script.")
        os._exit(1)

    while True:
        while not OpponentChanged():
            if GetTrainer()["posY"] == 9:
                break
            ButtonCombo(["Up"])
        else:
            EncounterPokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            WaitFrames(1)
            continue

        # Exit and re-enter
        PressButton("B")
        FollowPath([
            (12, 20),
            (99, 20, MapDataEnum.NAVEL_ROCK_H.value),
            (4, 5),
            (99, 5, MapDataEnum.NAVEL_ROCK_I.value),
            (12, 20),
            (12, 10)
        ])

def ModeLugia():
    trainer = GetTrainer()
    if not PlayerOnMap(MapDataEnum.NAVEL_ROCK_U.value) and trainer["posX"] == 11:
        log.info("Please place the player on the steps in front of Lugia at Navel Rock and restart the script.")
        os._exit(1)

    while True:
        while not OpponentChanged():
            if GetTrainer()["posY"] < 14:
                break
            ButtonCombo(["A", "Up"])
        else:
            EncounterPokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            WaitFrames(1)
            continue

        # Exit and re-enter
        PressButton("B")
        FollowPath([
            (11, 19),
            (99, 19, MapDataEnum.NAVEL_ROCK_T.value),
            (4, 5),
            (99, 5, MapDataEnum.NAVEL_ROCK_U.value),
            (11, 19),
            (11, 14)
        ])
