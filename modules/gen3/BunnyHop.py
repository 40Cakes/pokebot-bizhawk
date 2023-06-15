from modules.Inputs import ReleaseAllInputs, WaitFrames
from modules.Stats import OpponentChanged

# TODO
def mode_bunnyHop():
    log.info("Bunny hopping...")
    i = 0
    while not OpponentChanged():
        if i < 250:
            hold_button("B")
            WaitFrames(1)
        else:
            ReleaseAllInputs()
            WaitFrames(10)
            i = 0
        i += 1
    ReleaseAllInputs()
    identify_pokemon()
