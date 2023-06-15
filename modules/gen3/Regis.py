# TODO
def mode_regiTrio():
    if (not player_on_map(MapDataEnum.DESERT_RUINS.value) and
        not player_on_map(MapDataEnum.ISLAND_CAVE.value) and
        not player_on_map(MapDataEnum.ANCIENT_TOMB.value)):
        log.info("Please place the player below the target Regi in Desert Ruins, Island Cave or Ancient Tomb, then restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["Up", "A"])

        identify_pokemon()

        while not GetTrainer()["state"] == GameState.OVERWORLD:
            continue

        # Exit and re-enter
        press_button("B")
        follow_path([
            (8, 21), 
            (8, 11)
        ])
