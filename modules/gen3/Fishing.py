# TODO
def mode_fishing():
    log.info(f"Fishing...")
    emu_combo(["Select", 50]) # Cast rod and wait for fishing animation
    started_fishing = time.time()
    while not opponent_changed():
        if find_image("oh_a_bite.png") or find_image("on_the_hook.png"): 
            press_button("A")
            while find_image("oh_a_bite.png"):
                pass #This keeps you from getting multiple A presses and failing the catch
        if find_image("not_even_a_nibble.png") or find_image("it_got_away.png"): emu_combo(["B", 10, "Select"])
        if not find_image("text_period.png"): emu_combo(["Select", 50]) # Re-cast rod if the fishing text prompt is not visible

    identify_pokemon()
