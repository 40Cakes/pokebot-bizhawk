from modules.data.GameState import GameState
from modules.Inputs import EmuCombo, PressButton
from modules.Stats import EncounterPokemon, OpponentChanged

# TODO
def mode_rayquaza():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.SKY_PILLAR_G.value) or
        not (trainer["posX"] == 14 and trainer["posY"] <= 12)):
        log.info("Please place the player below Rayquaza at the Sky Pillar and restart the script.")
        os._exit(1)

    while True:
        while not OpponentChanged():
            EmuCombo(["A", "Up"]) # Walk up toward Rayquaza while mashing A
        
        EncounterPokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue

        # Exit and re-enter
        PressButton("B")
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
