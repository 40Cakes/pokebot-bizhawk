from modules.Inputs import PressButton

# TODO
def mode_sweetScent():
    log.info(f"Using Sweet Scent...")
    start_menu("pokemon")
    PressButton("A") # Select first pokemon in party

    # Search for sweet scent in menu
    while not find_image("sweet_scent.png"): 
        PressButton("Down")

    emu_combo(["A", 300]) # Select sweet scent and wait for animation
    identify_pokemon()
