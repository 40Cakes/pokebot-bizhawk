from modules.Stats import OpponentChanged

# TODO
def mode_move_until_obstructed():
    direction = config["direction"].lower()

    while True:
        pos1, pos2 = None, None
        foe_personality = last_opponent_personality
        log.info(f"Pathing {direction} until obstructed...")

        while foe_personality == last_opponent_personality:
            if pos1 == None or pos2 == None:
                if direction == "horizontal":
                    pos1 = run_until_obstructed("Left")
                    pos2 = run_until_obstructed("Right")
                else:
                    pos1 = run_until_obstructed("Up")
                    pos2 = run_until_obstructed("Down")
            else:
                if pos1 == pos2:
                    pos1 = None
                    pos2 = None
                    continue

                follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])
            OpponentChanged()

        identify_pokemon()

        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue