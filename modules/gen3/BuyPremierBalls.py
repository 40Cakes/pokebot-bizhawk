from modules.Inputs import PressButton, WaitFrames

# TODO
def mode_buyPremierBalls():
    while not find_image("mart/times_01.png"):
        PressButton("A")
        
        if find_image("mart/you_dont.png"):
            return False

        WaitFrames(30)

    PressButton("Right")
    WaitFrames(15)

    if not find_image("mart/times_10.png") and not find_image("mart/times_11.png"):
        return False

    if find_image("mart/times_11.png"):
        PressButton("Down")

    return True
