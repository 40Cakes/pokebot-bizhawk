from modules.Inputs import PressButton, WaitFrames
from modules.Stats import OpponentChanged

# TODO
def mode_deoxysPuzzle(do_encounter: bool = True):
    def retry_puzzle_if_stuck(success: bool):
        if not success: 
            reset_game()
            return True

    if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
        log.info("Please place the player below the triangle at its starting position on Birth Island, then save before restarting the script.")
        os._exit(1)

    delay = 4

    while True:
        while not GetTrainer()["state"] == GameState.OVERWORLD:
            emu_combo(["A", 8])

        WaitFrames(60)

        # Center
        if GetTrainer()["posY"] != 13:
            run_until_obstructed("Up")
        emu_combo([delay, "A"])

        # Left
        follow_path([(15, 14), (12, 14)])
        emu_combo([delay, "Left", "A", delay])

        # Top
        if retry_puzzle_if_stuck(follow_path([(15, 14), (15, 9)], True, True)): continue
        emu_combo([delay, "Up", "A", delay])

        # Right
        if retry_puzzle_if_stuck(follow_path([(15, 14), (18, 14)], True, True)): continue
        emu_combo([delay, "Right", "A", delay])

        # Middle Left
        if retry_puzzle_if_stuck(follow_path([(15, 14), (15, 11), (13, 11)], True, True)): continue
        emu_combo([delay, "Left", "A", delay])

        # Middle Right
        follow_path([(17, 11)])
        emu_combo([delay, "Right", "A", delay])

        # Bottom
        if retry_puzzle_if_stuck(follow_path([(15, 11), (15, 13)], True, True)): continue
        emu_combo([delay, "Down", "A", delay])

        # Bottom Left
        follow_path([(15, 14), (12, 14)])
        emu_combo([delay, "Left", "A", delay])

        # Bottom Right
        follow_path([(18, 14)])
        emu_combo([delay, "Right", "A", delay])

        # Bottom
        follow_path([(15, 14)])
        emu_combo([delay, "Down", delay, "A", delay])

        # Center
        if retry_puzzle_if_stuck(follow_path([(15, 11)], True, True)): continue

        if not do_encounter:
            log.info("Deoxys puzzle completed. Saving game and starting resets...")
            config["bot_mode"] = "deoxys resets"
            config["deoxys_puzzle_solved"] = True
            save_game()
            WaitFrames(10)
            return True

        while not OpponentChanged():
            PressButton("A")
            WaitFrames(1)

        identify_pokemon()

        while not GetTrainer()["state"] == GameState.OVERWORLD:
            continue

        for i in range(0, 4):
            PressButton("B")
            WaitFrames(15)

        # Exit and re-enter
        follow_path([
            (15, 99, (26, 59)), 
            (8, -99, MapDataEnum.BIRTH_ISLAND.value)
        ])

def mode_deoxysResets():
    if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
        log.info("Please place the player below the triangle at its final position on Birth Island, then save before restarting the script.")
        os._exit(1)

    deoxys_frames = get_rngState(GetTrainer()["tid"], "deoxys")

    while True:
        # Mash A to reach overworld from intro/title
        while GetTrainer()["state"] != GameState.OVERWORLD:
            emu_combo(["A", 8])

        # Wait for area to load properly
        WaitFrames(60)

        if not player_on_map(MapDataEnum.BIRTH_ISLAND.value) or GetTrainer()["posX"] != 15:
            log.info("Please place the player below the triangle at its final position on Birth Island, then save before restarting the script.")
            os._exit(1)

        while True:
            emu = GetEmu()
            if emu["rngState"] in deoxys_frames:
                log.debug(f"Already rolled on RNG state: {emu['rngState']}, waiting...")
            else:
                while not OpponentChanged():
                    emu_combo(["A", 8])

                deoxys_frames["rngState"].append(emu["rngState"])
                write_file(f"stats/{GetTrainer()['tid']}/deoxys.json", json.dumps(deoxys_frames, indent=4, sort_keys=True))
                identify_pokemon()
            break
        continue
