# TODO
def mode_buyPremierBalls():
    while not find_image("mart/times_01.png"):
        press_button("A")
        
        if find_image("mart/you_dont.png"):
            return False

        wait_frames(30)

    press_button("Right")
    wait_frames(15)

    if not find_image("mart/times_10.png") and not find_image("mart/times_11.png"):
        return False

    if find_image("mart/times_11.png"):
        press_button("Down")

    return True
