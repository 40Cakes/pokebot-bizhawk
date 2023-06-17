from modules.Stats import EncounterPokemon

def mode_move_between_coords():
    coords = config["coords"]
    pos1, pos2 = coords["pos1"], coords["pos2"]

    while True:
        foe_personality = last_opponent_personality

        while foe_personality == last_opponent_personality:
            follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])

        EncounterPokemon()

        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue
