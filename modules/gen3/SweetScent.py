from modules.Image import DetectTemplate
from modules.Inputs import EmuCombo, PressButton
from modules.Stats import EncounterPokemon

# TODO
def mode_sweetScent():
    log.info(f"Using Sweet Scent...")
    start_menu("pokemon")
    PressButton("A") # Select first pokemon in party

    # Search for sweet scent in menu
    while not DetectTemplate("sweet_scent.png"): 
        PressButton("Down")

    EmuCombo(["A", 300]) # Select sweet scent and wait for animation
    EncounterPokemon()
