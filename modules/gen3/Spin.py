# TODO
def mode_spin(): # TODO check if players direction changes, if not spam B (dumb Pokenav)
    trainer = GetTrainer()
    home_coords = (trainer["posX"], trainer["posY"])
    log.info(f"Spinning on the spot, home position is {home_coords}")
    while True:
        trainer = GetTrainer()
        if opponent_changed(): identify_pokemon()
        if home_coords != (trainer["posX"], trainer["posY"]): # Note: this will likely fail if the trainer accidentally changes map bank/ID
            log.info(f"Trainer has moved off home position, pathing back to {home_coords}...")
            follow_path([
                (home_coords[0], trainer["posY"]), 
                (trainer["posX"], home_coords[1])
            ], exit_when_stuck=True)
        directions = ["Up", "Right", "Down", "Left"]
        directions.remove(trainer["facing"])
        press_button(random.choice(directions))
        wait_frames(2)
