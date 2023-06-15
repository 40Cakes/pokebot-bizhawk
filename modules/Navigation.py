def run_until_obstructed(direction: str, run: bool = True): # Function to run until trainer position stops changing
    press_button("B") # press and release B in case of a random pokenav call

    hold_button(direction)
    last_x = GetTrainer()["posX"]
    last_y = GetTrainer()["posY"]

    if run: move_speed = 8
    else: move_speed = 16

    dir_unchanged = 0
    while dir_unchanged < move_speed:
        if run: 
            hold_button("B")
        
        wait_frames(1)

        trainer = GetTrainer()
        if last_x == trainer["posX"] and last_y == trainer["posY"]: 
            dir_unchanged += 1
            continue

        last_x = trainer["posX"]
        last_y = trainer["posY"]
        dir_unchanged = 0

        if opponent_changed():
            return None

    release_all_inputs()
    wait_frames(1)
    press_button("B")
    wait_frames(1)

    return [last_x, last_y]

def follow_path(coords: list, run: bool = True, exit_when_stuck: bool = False):
    possibly_stuck = False
    direction = None

    for x, y, *map_data in coords:
        log.info(f"Moving to: {x}, {y}")

        stuck_time = 0
        last_pos = [0, 0]

        if run:
            hold_button("B")

        while True:
            if direction != None:
                release_button(direction)

            if opponent_changed():
                identify_pokemon()
                return

            trainer = GetTrainer()
            last_pos = [trainer["posX"], trainer["posY"]]

            if map_data != []:
                # On map change
                if (trainer["mapBank"] == map_data[0][0] and trainer["mapId"] == map_data[0][1]):
                    break
            elif last_pos[0] == x and last_pos[1] == y:
                break
            
            if trainer["posX"] > x:
                direction = "Left"
            elif trainer["posX"] < x:
                direction = "Right"
            elif trainer["posY"] < y:
                direction = "Down"
            elif trainer["posY"] > y:
                direction = "Up"

            if trainer["posX"] == last_pos[0] and trainer["posY"] == last_pos[1]:
                stuck_time += 1

                if stuck_time == 120:
                    log.info("Bot hasn't moved for a while. Is it stuck?")
                    
                    if exit_when_stuck:
                        release_all_inputs()
                        return False

                # Press B occasionally in case there's a menu/dialogue open
                if stuck_time % 120 == 0:
                    release_button("B")
                    wait_frames(1)
                    press_button("B")
            else:
                stuck_time = 0

            hold_button(direction)
            wait_frames(1)

    release_all_inputs()
    return True

def player_on_map(map_data: tuple):
    trainer = GetTrainer()
    on_map = trainer["mapBank"] == map_data[0] and trainer["mapId"] == map_data[1]
    log.debug(f"Player was not on target map of {map_data[0]},{map_data[1]}. Map was {trainer['mapBank']}, {trainer['mapId']}")
    return on_map
