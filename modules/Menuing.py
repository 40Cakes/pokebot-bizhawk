def start_menu(entry: str): # Function to open any start menu item - presses START, finds the menu entry and opens it
    if not entry in ["bag", "bot", "exit", "option", "pokedex", "pokemon", "pokenav", "save"]:
        return False

    log.info(f"Opening start menu entry: {entry}")
    filename = f"start_menu/{entry.lower()}.png"
    
    release_all_inputs()

    while not find_image("start_menu/select.png"):
        emu_combo(["B", "Start"])
        
        for i in range(0, 10):
            if find_image("start_menu/select.png"):
                break
            wait_frames(1)

    wait_frames(5)

    while not find_image(filename): # Find menu entry
        emu_combo(["Down", 10])

    while find_image(filename): # Press menu entry
        emu_combo(["A", 10])

def bag_menu(category: str, item: str): # Function to find an item in the bag and use item in battle such as a pokeball
    if not category in ["berries", "items", "key_items", "pokeballs", "tms&hms"]:
        return False

    log.info(f"Scrolling to bag category: {category}...")

    while not find_image(f"start_menu/bag/{category.lower()}.png"):
        emu_combo(["Right", 25]) # Press right until the correct category is selected

    wait_frames(60) # Wait for animations

    log.info(f"Scanning for item: {item}...")
    
    i = 0
    while not find_image(f"start_menu/bag/items/{item}.png") and i < 50:
        if i < 25: emu_combo(["Down", 15])
        else: emu_combo(["Up", 15])
        i += 1

    if find_image(f"start_menu/bag/items/{item}.png"):
        log.info(f"Using item: {item}...")
        while GetTrainer()["state"] == GameState.BAG_MENU: 
            emu_combo(["A", 30]) # Press A to use the item
        return True
    else:
        return False

def pickup_items(): # If using a team of Pokemon with the ability "pickup", this function will take the items from the pokemon in your party if 3 or more Pokemon have an item
    if GetTrainer()["state"] != GameState.OVERWORLD:
        return

    item_count = 0
    pickup_mon_count = 0
    party_size = len(GetParty())

    i = 0
    while i < party_size:
        pokemon = GetParty()[i]
        held_item = pokemon['heldItem']

        if pokemon["speciesName"] in pickup_pokemon:
            if held_item != 0:
                item_count += 1

            pickup_mon_count += 1
            log.info(f"Pokemon {i}: {pokemon['speciesName']} has item: {item_list[held_item]}")

        i += 1

    if item_count < config["pickup_threshold"]:
        log.info(f"Party has {item_count} item(s), won't collect until at threshold {config['pickup_threshold']}")
        return

    wait_frames(60) # Wait for animations
    start_menu("pokemon") # Open Pokemon menu
    wait_frames(65)

    i = 0
    while i < party_size:
        pokemon = GetParty()[i]
        if pokemon["speciesName"] in pickup_pokemon and pokemon["heldItem"] != 0:
            # Take the item from the pokemon
            emu_combo(["A", 15, "Up", 15, "Up", 15, "A", 15, "Down", 15, "A", 75, "B"])
            item_count -= 1
        
        if item_count == 0:
            break

        emu_combo([15, "Down", 15])
        i += 1

    # Close out of menus
    for i in range(0, 5):
        press_button("B")
        wait_frames(20)

def save_game(): # Function to save the game via the save option in the start menu
    try:
        log.info("Saving the game...")

        i = 0
        start_menu("save")
        while i < 2:
            while not find_image("start_menu/save/yes.png"):
                wait_frames(10)
            while find_image("start_menu/save/yes.png"):
                emu_combo(["A", 30])
                i += 1
        wait_frames(500) # Wait for game to save
        press_button("SaveRAM") # Flush Bizhawk SaveRAM to disk
    except Exception as e:
        log.exception(str(e))

def reset_game():
    log.info("Resetting...")
    hold_button("Power")
    wait_frames(60)
    release_button("Power")

def catch_pokemon(): # Function to catch pokemon
    try:
        while not find_image("battle/fight.png"):
            release_all_inputs()
            emu_combo(["B", "Up", "Left"]) # Press B + up + left until FIGHT menu is visible
        
        if config["manual_catch"]:
            input("Pausing bot for manual catch (don't forget to pause pokebot.lua script so you can provide inputs). Press Enter to continue...")
            return True
        else:
            log.info("Attempting to catch Pokemon...")
        
        if config["use_spore"]: # Use Spore to put opponent to sleep to make catches much easier
            log.info("Attempting to sleep the opponent...")
            i, spore_pp = 0, 0
            
            opponent = GetOpponent()
            ability = opponent["ability"][opponent["altAbility"]]
            can_spore = ability not in no_sleep_abilities

            if (opponent["status"] == 0) and can_spore:
                for move in GetParty()[0]["enrichedMoves"]:
                    if move["name"] == "Spore":
                        spore_pp = move["pp"]
                        spore_move_num = i
                    i += 1

                if spore_pp != 0:
                    emu_combo(["A", 15])
                    if spore_move_num == 0: seq = ["Up", "Left"]
                    elif spore_move_num == 1: seq = ["Up", "Right"]
                    elif spore_move_num == 2: seq = ["Left", "Down"]
                    elif spore_move_num == 3: seq = ["Right", "Down"]

                    while not find_image("spore.png"):
                        emu_combo(seq)

                    emu_combo(["A", 240]) # Select move and wait for animations
            elif not can_spore:
                log.info(f"Can't sleep the opponent! Ability is {ability}")

            while not find_image("battle/bag.png"): 
                release_all_inputs()
                emu_combo(["B", "Up", "Right"]) # Press B + up + right until BAG menu is visible

        while True:
            if find_image("battle/bag.png"): press_button("A")

            # Preferred ball order to catch wild mons + exceptions 
            # TODO read this data from memory instead
            if GetTrainer()["state"] == GameState.BAG_MENU:
                can_catch = False

                # Check if current species has a preferred ball
                if opponent["speciesName"] in config["pokeball_override"]:
                    species_rule = config["pokeball_override"][opponent["speciesName"]]
                    
                    for ball in species_rule:
                        if bag_menu(category="pokeballs", item=ball):
                            can_catch = True
                            break

                # Check global pokeball priority 
                if not can_catch:
                    for ball in config["pokeball_priority"]:
                        if bag_menu(category="pokeballs", item=ball):
                            can_catch = True
                            break

                if not can_catch:
                    log.info("No balls to catch the Pokemon found. Killing the script!")
                    os._exit(1)

            if find_image("gotcha.png"): # Check for gotcha! text when a pokemon is successfully caught
                log.info("Pokemon caught!")

                while GetTrainer()["state"] != GameState.OVERWORLD:
                    press_button("B")

                wait_frames(120) # Wait for animations
                
                if config["save_game_after_catch"]: 
                    save_game()
                
                return True

            if GetTrainer()["state"] == GameState.OVERWORLD:
                return False
    except Exception as e:
        log.exception(str(e))
        return False

def battle(): # Function to battle wild pokemon
    # This will only battle with the lead pokemon of the party, and will run if it dies or runs out of PP
    ally_fainted = False
    foe_fainted = False

    while not ally_fainted and not foe_fainted and GetTrainer()["state"] != GameState.OVERWORLD:
        log.info("Navigating to the FIGHT button...")

        while not find_image("battle/fight.png") and GetTrainer()["state"] != GameState.OVERWORLD:
            emu_combo(["B", 10, "Up", 10, "Left", 10]) # Press B + up + left until FIGHT menu is visible
        
        if GetTrainer()["state"] == GameState.OVERWORLD:
            return True

        best_move = find_effective_move(GetParty()[0], GetOpponent())
        
        if best_move["power"] <= 10:
            log.info("Lead Pokemon has no effective moves to battle the foe!")
            flee_battle()
            return False
        
        press_button("A")

        wait_frames(5)

        log.info(f"Best move against foe is {best_move['name']} (Effective power is {best_move['power']})")

        i = int(best_move["index"])

        if i == 0:
            emu_combo(["Up", "Left"])
        elif i == 1:
            emu_combo(["Up", "Right"])
        elif i == 2:
            emu_combo(["Down", "Left"])
        elif i == 3:
            emu_combo(["Down", "Right"])
        
        press_button("A")

        wait_frames(5)

        while GetTrainer()["state"] != GameState.OVERWORLD and not find_image("battle/fight.png"):
            press_button("B")
            wait_frames(1)
        
        ally_fainted = GetParty()[0]["hp"] == 0
        foe_fainted = GetOpponent()["hp"] == 0
    
    if ally_fainted:
        log.info("Lead Pokemon fainted!")
        flee_battle()
        return False
    elif foe_fainted:
        log.info("Battle won!")
        return True
    return True

def is_valid_move(move: dict):
    return not move["name"] in config["banned_moves"] and move["power"] > 0

def find_effective_move(ally: dict, foe: dict):
    i = 0
    move_power = []

    for move in ally["enrichedMoves"]:
        power = move["power"]

        # Ignore banned moves and those with 0 PP
        if not is_valid_move(move) or ally["pp"][i] == 0:
            move_power.append(0)
            i += 1
            continue

        # Calculate effectiveness against opponent's type(s)
        matchups = type_list[move["type"]]

        for foe_type in foe["type"]:
            if foe_type in matchups["immunes"]:
                power *= 0
            elif foe_type in matchups["weaknesses"]:
                power *= 0.5
            elif foe_type in matchups["strengths"]:
                power *= 2

        # STAB
        for ally_type in ally["type"]:
            if ally_type == move["type"]:
                power *= 1.5

        move_power.append(power)
        i += 1

    # Return info on the best move
    move_idx = move_power.index(max(move_power))
    return {
        "name": ally["enrichedMoves"][move_idx]["name"],
        "index": move_idx,
        "power": max(move_power)
    }

def flee_battle(): # Function to run from wild pokemon
    try:
        log.info("Running from battle...")
        while GetTrainer()["state"] != GameState.OVERWORLD:
            while not find_image("battle/run.png") and GetTrainer()["state"] != GameState.OVERWORLD: 
                emu_combo(["Right", 5, "Down", "B", 5])
            while find_image("battle/run.png") and GetTrainer()["state"] != GameState.OVERWORLD: 
                press_button("A")
            press_button("B")
        wait_frames(30) # Wait for battle fade animation
    except Exception as e:
        log.exception(str(e))
