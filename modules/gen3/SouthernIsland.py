from data.GameState import GameState
from modules.Inputs import EmuCombo, PressButton
from modules.Stats import EncounterPokemon, OpponentChanged

# TODO
def mode_southernIsland():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.SOUTHERN_ISLAND_A.value) or
        not 5 <= trainer["posX"] == 13 and trainer["posY"] >= 12):
        log.info("Please place the player below the sphere on Southern Island and restart the script.")
        os._exit(1)

    while True:
        while not OpponentChanged():
            EmuCombo(["A", "Up"])

        EncounterPokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue

        # Exit and re-enter
        PressButton("B")
        follow_path([
            (13, 99, MapDataEnum.SOUTHERN_ISLAND.value), 
            (14, -99, MapDataEnum.SOUTHERN_ISLAND_A.value)
        ])
