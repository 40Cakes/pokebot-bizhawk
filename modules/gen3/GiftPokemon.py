# TODO
def collect_gift_mon(target: str):
    rng_frames = get_rngState(GetTrainer()["tid"], target)
    party_size = len(GetParty())

    if party_size == 6:
        log.info("Please leave at least one party slot open, then restart the script.")
        os._exit(1)

    while True:
        # Button mash through intro/title
        while GetTrainer()["state"] != GameState.OVERWORLD:
            press_button("A")
            wait_frames(8)
        
        # Text goes faster with B held
        hold_button("B")

        while len(GetParty()) == party_size:
            emu = GetEmu()
            if emu["rngState"] in rng_frames:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
                continue
            press_button("A")
            wait_frames(5)
        
        rng_frames["rngState"].append(emu["rngState"])
        write_file(f"stats/{GetTrainer()['tid']}/{target.lower()}.json", json.dumps(rng_frames, indent=4, sort_keys=True))

        mon = GetParty()[party_size]
        
        # Open the menu and find Gift mon in party
        release_button("B")

        if config["mem_hacks"] and not mon["shiny"]:
            log_encounter(mon)
            hold_button("Power")
            wait_frames(60)
            release_button("Power")
            continue

        while not find_image("start_menu/select.png"):
            press_button("B")

            for i in range(0, 4):
                if find_image("start_menu/select.png"):
                    break
                wait_frames(1)

        while find_image("start_menu/select.png"):
            press_button("B")
            
            for i in range(0, 4):
                if not find_image("start_menu/select.png"):
                    break
                wait_frames(1)

        start_menu("pokemon")

        wait_frames(60)

        i = 0
        while i < party_size:
            emu_combo(["Down", 15])
            i += 1

        emu_combo(["A", 15, "A", 60])

        log_encounter(mon)

        if not mon["shiny"]:
            hold_button("Power")
            wait_frames(60)
            release_button("Power")
        else:
            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")

def mode_beldum():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if (not player_on_map(MapDataEnum.MOSSDEEP_CITY_H.value) or not ((x == 3 and y == 3) or (x == 4 and y == 2))):
        log.info("Please face the player toward the Pokeball in Steven's house after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon("Beldum")

def mode_castform():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if (not player_on_map(MapDataEnum.ROUTE_119_B.value) or not ((x == 2 and y == 3) or (x == 3 and y == 2) or (x == 1 and y == 2))):
        log.info("Please face the player toward the scientist after saving the game, then restart the script.")
        os._exit(1)

    collect_gift_mon("Castform")

def mode_fossil():
    trainer = GetTrainer()
    x, y = trainer["posX"], trainer["posY"]

    if not player_on_map(MapDataEnum.RUSTBORO_CITY_B.value) or y != 8 and not (x == 13 or x == 15):
        log.info("Please face the player toward the Fossil researcher after handing it over, re-entering the room, and saving the game. Then restart the script.")
        os._exit(1)

    collect_gift_mon(config["fossil"])
