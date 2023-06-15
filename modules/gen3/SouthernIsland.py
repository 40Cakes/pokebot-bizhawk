# TODO
def mode_southernIsland():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.SOUTHERN_ISLAND_A.value) or
        not 5 <= trainer["posX"] == 13 and trainer["posY"] >= 12):
        log.info("Please place the player below the sphere on Southern Island and restart the script.")
        os._exit(1)

    while True:
        while not opponent_changed():
            emu_combo(["A", "Up"])

        identify_pokemon()

        # Wait until battle is over
        while GetTrainer()["state"] != GameState.OVERWORLD:
            continue

        # Exit and re-enter
        press_button("B")
        follow_path([
            (13, 99, MapDataEnum.SOUTHERN_ISLAND.value), 
            (14, -99, MapDataEnum.SOUTHERN_ISLAND_A.value)
        ])
