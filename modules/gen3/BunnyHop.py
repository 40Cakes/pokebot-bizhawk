# TODO
def mode_bunnyHop():
    log.info("Bunny hopping...")
    i = 0
    while not opponent_changed():
        if i < 250:
            hold_button("B")
            wait_frames(1)
        else:
            release_all_inputs()
            wait_frames(10)
            i = 0
        i += 1
    release_all_inputs()
    identify_pokemon()
