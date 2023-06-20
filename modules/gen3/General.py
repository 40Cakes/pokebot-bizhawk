import random
import logging

from modules.data.GameState import GameState
from modules.Config import GetConfig
from modules.Image import DetectTemplate
from modules.Inputs import ButtonCombo, HoldButton, PressButton, ReleaseAllInputs, WaitFrames
from modules.Menuing import StartMenu
from modules.Navigation import Bonk, FollowPath
from modules.Stats import EncounterPokemon, OpponentChanged
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)
config = GetConfig()


def ModeBonk():
    direction = config["direction"].lower()

    while True:
        pos1, pos2 = None, None
        log.info(f"Pathing {direction} until bonk...")

        while not OpponentChanged():
            if pos1 is None or pos2 is None:
                if direction == "horizontal":
                    pos1 = Bonk("Left")
                    pos2 = Bonk("Right")
                else:
                    pos1 = Bonk("Up")
                    pos2 = Bonk("Down")
            elif pos1 == pos2:
                pos1, pos2 = None, None
                continue

                FollowPath([(pos1[0], pos1[1]), (pos2[0], pos2[1])])
            OpponentChanged()

        EncounterPokemon()

        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue


def ModeBunnyHop():
    log.info("Bunny hopping...")
    i = 0
    while not OpponentChanged():
        if i < 250:
            HoldButton("B")
            WaitFrames(1)
        else:
            ReleaseAllInputs()
            WaitFrames(10)
            i = 0
        i += 1
    ReleaseAllInputs()
    EncounterPokemon()


def ModeFishing():
    log.info(f"Fishing...")
    ButtonCombo(["Select", 50])  # Cast rod and wait for fishing animation
    # started_fishing = time.time()
    while not OpponentChanged():
        if DetectTemplate("oh_a_bite.png") or DetectTemplate("on_the_hook.png"):
            PressButton("A")
            while DetectTemplate("oh_a_bite.png"):
                pass  # This keeps you from getting multiple A presses and failing the catch
        if DetectTemplate("not_even_a_nibble.png") or DetectTemplate("it_got_away.png"): ButtonCombo(
            ["B", 10, "Select"])
        if not DetectTemplate("text_period.png"): ButtonCombo(
            ["Select", 50])  # Re-cast rod if the fishing text prompt is not visible

    EncounterPokemon()


def ModeCoords():
    coords = config["coords"]
    pos1, pos2 = coords["pos1"], coords["pos2"]
    while True:
        while not OpponentChanged():
            FollowPath([(pos1[0], pos1[1]), (pos2[0], pos2[1])])
        EncounterPokemon()
        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue


def ModeSpin():  # TODO check if players direction changes, if not spam B (Pokenav)
    try:
        trainer = GetTrainer()
        home_coords = (trainer["posX"], trainer["posY"])
        log.info(f"Spinning on the spot, home position is {home_coords}")
        while True:
            trainer = GetTrainer()
            if OpponentChanged(): EncounterPokemon()
            if home_coords != (trainer["posX"], trainer[
                "posY"]):  # Note: this will likely fail if the trainer accidentally changes map bank/ID
                log.info(f"Trainer has moved off home position, pathing back to {home_coords}...")
                FollowPath([
                    (home_coords[0], trainer["posY"]),
                    (trainer["posX"], home_coords[1])
                ], exit_when_stuck=True)
            directions = ["Up", "Right", "Down", "Left"]
            directions.remove(trainer["facing"])
            PressButton(random.choice(directions))
            WaitFrames(2)
            if GetTrainer()["facing"] == trainer[
                "facing"]:  # Check if the trainer's facing direction actually changed, press B to cancel PokeNav as it prevents all movement
                PressButton("B")
    except Exception as e:
        log.exception(str(e))


def ModeSweetScent():
    log.info(f"Using Sweet Scent...")
    StartMenu("pokemon")
    PressButton("A")  # Select first pokemon in party
    # Search for sweet scent in menu
    while not DetectTemplate("sweet_scent.png"):
        PressButton("Down")
    ButtonCombo(["A", 300])  # Select sweet scent and wait for animation
    EncounterPokemon()


def ModePremierBalls():
    while not DetectTemplate("mart/times_01.png"):
        PressButton("A")
        if DetectTemplate("mart/you_dont.png"):
            return False
        WaitFrames(30)
    PressButton("Right")
    WaitFrames(15)
    if not DetectTemplate("mart/times_10.png") and not DetectTemplate("mart/times_11.png"):
        return False
    if DetectTemplate("mart/times_11.png"):
        PressButton("Down")
    return True
