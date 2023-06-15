# TODO
def mode_starters():
    choice = config["starter"].lower()
    starter_frames = get_rngState(GetTrainer()['tid'], choice)

    if choice not in ["treecko", "torchic", "mudkip"]:
        log.info(f"Unknown starter \"{config['starter']}\". Please edit the value in config.yml and restart the script.")
        os._exit(1)

    log.info(f"Soft resetting starter Pokemon...")
    
    while True:
        release_all_inputs()

        while GetTrainer()["state"] != GameState.OVERWORLD: 
            press_button("A")

        # Short delay between A inputs to prevent accidental selection confirmations
        while GetTrainer()["state"] == GameState.OVERWORLD: 
            emu_combo(["A", 10])

        # Press B to back out of an accidental selection when scrolling to chosen starter
        if choice == "mudkip":
            while not find_image("mudkip.png"): 
                emu_combo(["B", "Right"])
        elif choice == "treecko":
            while not find_image("treecko.png"): 
                emu_combo(["B", "Left"])

        while True:
            emu = GetEmu()
            if emu["rngState"] in starter_frames["rngState"]:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
            else:
                while GetTrainer()["state"] == GameState.MISC_MENU: 
                    press_button("A")

                starter_frames["rngState"].append(emu["rngState"])
                write_file(f"stats/{GetTrainer()['tid']}/{choice}.json", json.dumps(starter_frames, indent=4, sort_keys=True))

                while not find_image("battle/fight.png"):
                    press_button("B")

                    if config["mem_hacks"] and GetParty()[0]:
                        if identify_pokemon(starter=True):
                            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                        else:
                            reset_game()
                            break
                else:
                    while True:
                        if GetParty()[0]:
                            if identify_pokemon(starter=True): 
                                input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can provide inputs). Press Enter to continue...")
                            else:
                                reset_game()
                                break
            continue
