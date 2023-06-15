# TODO
def mode_kyogre():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.MARINE_CAVE_A.value) or
        not 5 <= trainer["posX"] <= 14 and 26 <= trainer["posY"] <= 27):
        log.info("Please place the player below Kyogre in Marine Cave and restart the script.")
        os._exit(1)

    while True:
        follow_path([(9, 26)])

        identify_pokemon()

        # Exit and re-enter
        follow_path([
            (9, 27), 
            (18, 27), 
            (18, 14), 
            (14, 14), 
            (14, 4), 
            (20, 4), 
            (20, 99, MapDataEnum.MARINE_CAVE.value), 
            (14, -99, MapDataEnum.MARINE_CAVE_A.value), 
            (14, 4), 
            (14, 14), 
            (18, 14), 
            (18, 27), 
            (14, 27)
        ])
