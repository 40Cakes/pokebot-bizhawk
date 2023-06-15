# TODO
def mode_groudon():
    trainer = GetTrainer()
    if (not player_on_map(MapDataEnum.TERRA_CAVE_A.value) or
        not 11 <= trainer["posX"] <= 20 and 26 <= trainer["posY"] <= 27):
        log.info("Please place the player below Groudon in Terra Cave and restart the script.")
        os._exit(1)

    while True:
        follow_path([(17, 26)])

        identify_pokemon()

        # Exit and re-enter
        follow_path([
            (7, 26), 
            (7, 15), 
            (9, 15), 
            (9, 4), 
            (5, 4), 
            (5, 99, MapDataEnum.TERRA_CAVE.value), 
            (14, -99, MapDataEnum.TERRA_CAVE_A.value), 
            (9, 4), (9, 15), 
            (7, 15), 
            (7, 26), 
            (11, 26)
        ])
