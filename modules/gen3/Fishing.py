from modules.Image import DetectTemplate
from modules.Inputs import EmuCombo, PressButton
from modules.Stats import EncounterPokemon, OpponentChanged

# TODO
def mode_fishing():
    log.info(f"Fishing...")
    EmuCombo(["Select", 50]) # Cast rod and wait for fishing animation
    started_fishing = time.time()
    while not OpponentChanged():
        if DetectTemplate("oh_a_bite.png") or DetectTemplate("on_the_hook.png"): 
            PressButton("A")
            while DetectTemplate("oh_a_bite.png"):
                pass #This keeps you from getting multiple A presses and failing the catch
        if DetectTemplate("not_even_a_nibble.png") or DetectTemplate("it_got_away.png"): EmuCombo(["B", 10, "Select"])
        if not DetectTemplate("text_period.png"): EmuCombo(["Select", 50]) # Re-cast rod if the fishing text prompt is not visible

    EncounterPokemon()
