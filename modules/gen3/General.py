import random
import logging

from modules.data.GameState import GameState
from modules.Config import GetConfig
from modules.Image import DetectTemplate
from modules.Inputs import ButtonCombo, HoldButton, ReleaseButton, PressButton, ReleaseAllInputs, WaitFrames
from modules.Menuing import StartMenu, IsValidMove
from modules.Navigation import Bonk, FollowPath
from modules.Stats import EncounterPokemon, OpponentChanged
from modules.mmf.Pokemon import GetParty
from modules.mmf.Trainer import GetTrainer
from modules.mmf.Bag import GetBag

log = logging.getLogger(__name__)
config = GetConfig()


def ModeBonk():
    direction = config["bonk_direction"].lower()

    while True:
        log.info(f"Pathing {direction} until bonk...")

        AutoStop()
        while not OpponentChanged():
            if direction == "horizontal":
                pos1 = Bonk("Left")
                pos2 = Bonk("Right")
            else:
                pos1 = Bonk("Up")
                pos2 = Bonk("Down")
            if pos1 == pos2:
                continue

            FollowPath([pos1, pos2])

        EncounterPokemon()

        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue


def ModeBunnyHop():
    log.info("Bunny hopping...")
    i = 0
    
    AutoStop()
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
    
    AutoStop()
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
        AutoStop()
        while not OpponentChanged():
            FollowPath([(pos1[0], pos1[1]), (pos2[0], pos2[1])], exit_when_stuck=True)
        EncounterPokemon()
        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue


def ModeSpin():  # TODO check if players direction changes, if not spam B (Pokenav)
    try:
        trainer = GetTrainer()
        home_coords = (trainer["posX"], trainer["posY"])
        log.info(f"Spinning on the spot, home position is {home_coords}")
        while True:
            AutoStop()
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
            if GetTrainer()["facing"] == trainer["facing"]:
                # Check if the trainer's facing direction actually changed, press B to cancel PokeNav as it prevents
                # all movement
                PressButton("B")
    except Exception as e:
        log.exception(str(e))

def ModePetalburgLoop():
    try:
        trainer = GetTrainer()
        party = GetParty()
        log.info(f"Entering Petalburg fight/heal loop")
        talkCycle = 0
        while True:
            trainer = GetTrainer()
            posX = trainer["posX"]

            AutoStop()
            if OpponentChanged(): EncounterPokemon()

            party = GetParty()
            tapB = False # For getting out of PokeNav and/or pickup imperfections
            if party:
                isHighHealth = party[0]["hp"] > party[0]["maxHP"] * 0.5
                
                hasViableMoves = False
                for i, move in enumerate(party[0]["enrichedMoves"]):
                    # Ignore banned moves and those with 0 PP
                    if IsValidMove(move) and party[0]["pp"][i] > 0:
                        hasViableMoves = True
                if not (isHighHealth and hasViableMoves):
                    # Not in a state to battle, gotta go back to heal
                    if posX < 7 or posX > 20:
                        # Outside and to the right of the Pokemon Center
                        HoldButton("B")
                        PressButton("Left")
                    elif posX > 7 and posX < 20:
                        # Somehow overshot Pokemon Center, gotta walk back right a bit
                        PressButton("Right")
                        tapB = True
                    else:
                        # Right in front of or inside Pokemon Center. Enter building, walk up to Nurse Joy and mash A through her dialogue to heal
                        PressButton("Up")
                        if talkCycle > 2:
                            HoldButton("A")
                else:
                    # First pokemon in party (probably) has enough HP and PP to actually battle
                    if posX == 7:
                        # Inside Pokemon Center, try to walk down and mash B through Nurse Joy dialogue if it's open
                        PressButton("Down")
                        if talkCycle > 2:
                            HoldButton("B")
                    elif posX > 7:
                        # Outside and still in the Rustboro tile, run right
                        PressButton("Right")
                        HoldButton("B")
                    elif posX < 4 or trainer["facing"] == "Left":
                        # In the same tile as the grass, but not in the grass yet. Or in the grass and facing left, so we want to turn right as simpler a alternative to spinning
                        PressButton("Right")
                        tapB = True
                    else:
                        # Must be in the grass and not facing left, so turn left as a simpler alternative to spinning
                        PressButton("Left")
                        tapB = True

            WaitFrames(2)
            talkCycle = (talkCycle + 1) % 4 # to pace button mashing of text boxes and force A/B button holding to reset
            if talkCycle == 0:
                ReleaseAllInputs()

            if tapB:
                WaitFrames(1)
                if GetTrainer()["facing"] == trainer["facing"]:
                    # Check if the trainer's facing direction actually changed, press B to cancel PokeNav as it prevents
                    # all movement
                    PressButton("B")
    except Exception as e:
        log.exception(str(e))#


def ModeSweetScent():
    log.info(f"Using Sweet Scent...")
    AutoStop()
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

def AutoStop():
    if config["auto_stop"]: 
        bag = GetBag()
        for item in bag["Poké Balls"]:
            if item["quantity"] > 0:
                return
    else:
        return

    log.info(f"Ran out of Balls, pausing the bot...")
    input("Press Enter to continue...")