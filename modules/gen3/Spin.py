import random
import logging

from modules.Inputs import PressButton, WaitFrames
from modules.Stats import EncounterPokemon, OpponentChanged
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)

def Spin(): # TODO check if players direction changes, if not spam B (Pokenav)
    try:
        trainer = GetTrainer()
        home_coords = (trainer["posX"], trainer["posY"])
        log.info(f"Spinning on the spot, home position is {home_coords}")
        while True:
            trainer = GetTrainer()
            if OpponentChanged(): EncounterPokemon()
            if home_coords != (trainer["posX"], trainer["posY"]): # Note: this will likely fail if the trainer accidentally changes map bank/ID
                log.info(f"Trainer has moved off home position, pathing back to {home_coords}...")
                follow_path([
                    (home_coords[0], trainer["posY"]), 
                    (trainer["posX"], home_coords[1])
                ], exit_when_stuck=True)
            directions = ["Up", "Right", "Down", "Left"]
            directions.remove(trainer["facing"])
            PressButton(random.choice(directions))
            WaitFrames(2)
    except Exception as e:
        log.exception(str(e))
