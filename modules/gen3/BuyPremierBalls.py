from modules.Image import DetectTemplate
from modules.Inputs import PressButton, WaitFrames

def mode_buyPremierBalls():
    while not DetectTemplate("mart/times_01.png"):
        PressButton("A")
        
        if DetectTemplate("mart/you_dont.png"):
            return False

        WaitFrames(30)

    PressButton("Right")
    WaitFrames(15)

    if not DetectTemplate("mart/times_10.png") and not DetectTemplate("mart/times_11.png"):
        return False

    if DetectTemplate("mart/times_11.png"):
        PressButton("Down")

    return True
