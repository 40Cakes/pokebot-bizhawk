import logging
import os

from modules.data.MapData import mapRSE  # mapFRLG
from modules.Inputs import HoldButton, PressButton, ReleaseAllInputs, ReleaseButton, WaitFrames
from modules.Stats import EncounterPokemon, OpponentChanged
from modules.mmf.Emu import GetEmu
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)

emu = GetEmu()
log.info("Detected game: " + emu["detectedGame"])
if any([x in emu["detectedGame"] for x in ["Emerald"]]):  # "Ruby", "Sapphire"
    MapDataEnum = mapRSE
# if any([x in emu["detectedGame"] for x in ["FireRed", "LeafGreen"]]):
#    MapDataEnum = mapFRLG
else:
    log.error("Unsupported game detected...")
    input("Press enter to continue...")
    os._exit(1)


def Bonk(direction: str, run: bool = True):  # Function to run until trainer position stops changing
    PressButton("B")  # press and release B in case of a random pokenav call

    HoldButton(direction)
    last_x = GetTrainer()["posX"]
    last_y = GetTrainer()["posY"]

    move_speed = 8 if run else 16

    dir_unchanged = 0
    while dir_unchanged < move_speed:
        if run:
            HoldButton("B")
            WaitFrames(1)

        trainer = GetTrainer()
        if last_x == trainer["posX"] and last_y == trainer["posY"]:
            dir_unchanged += 1
            continue

        last_x = trainer["posX"]
        last_y = trainer["posY"]
        dir_unchanged = 0

        if OpponentChanged():
            return None

    ReleaseAllInputs()
    WaitFrames(1)
    PressButton("B")
    WaitFrames(1)

    return [last_x, last_y]


def FollowPath(coords: list, run: bool = True, exit_when_stuck: bool = False):
    direction = None

    for x, y, *map_data in coords:
        log.info(f"Moving to: {x}, {y}")

        stuck_time = 0

        ReleaseAllInputs()
        while True:
            if run:
                HoldButton("B")

            if OpponentChanged():
                EncounterPokemon()
                return

            if GetTrainer()["posX"] == x and GetTrainer()["posY"] == y:
                ReleaseAllInputs()
                break
            elif map_data:
                # On map change
                if GetTrainer()["mapBank"] == map_data[0][0] and GetTrainer()["mapId"] == map_data[0][1]:
                    ReleaseAllInputs()
                    break

            last_pos = [GetTrainer()["posX"], GetTrainer()["posY"]]
            if GetTrainer()["posX"] == last_pos[0] and GetTrainer()["posY"] == last_pos[1]:
                stuck_time += 1

                if stuck_time % 60 == 0:
                    log.info("Bot hasn't moved for a while. Is it stuck?")
                    ReleaseButton("B")
                    WaitFrames(1)
                    PressButton("B")  # Press B occasionally in case there's a menu/dialogue open
                    WaitFrames(1)

                    if exit_when_stuck:
                        ReleaseAllInputs()
                        return False
            else:
                stuck_time = 0

            if GetTrainer()["posX"] > x:
                direction = "Left"
            elif GetTrainer()["posX"] < x:
                direction = "Right"
            elif GetTrainer()["posY"] < y:
                direction = "Down"
            elif GetTrainer()["posY"] > y:
                direction = "Up"

            HoldButton(direction)
            WaitFrames(1)

        ReleaseAllInputs()
    return True


def PlayerOnMap(map_data: tuple):
    trainer = GetTrainer()
    on_map = trainer["mapBank"] == map_data[0] and trainer["mapId"] == map_data[1]
    log.debug(
        f"Player was not on target map of {map_data[0]},{map_data[1]}. Map was {trainer['mapBank']}, {trainer['mapId']}")
    return on_map
