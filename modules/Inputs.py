def hold_button(button: str): # Function to update the hold_input object
    global hold_input
    log.debug(f"Holding: {button}...")

    hold_input[button] = True
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

def release_button(button: str): # Function to update the hold_input object
    global hold_input
    log.debug(f"Releasing: {button}...")

    hold_input[button] = False
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

def release_all_inputs(): # Function to release all keys in all input objects
    global press_input, hold_input
    log.debug(f"Releasing all inputs...")

    for button in ["A", "B", "L", "R", "Up", "Down", "Left", "Right", "Select", "Start", "Power"]:
        hold_input[button] = False
        hold_input_mmap.seek(0)
        hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))

def press_button(button: str): # Function to update the press_input object
    global g_current_index

    match button:
        case 'Left':
            button = 'l'
        case 'Right':
            button = 'r'
        case 'Up':
            button = 'u'
        case 'Down':
            button = 'd'
        case 'Select':
            button = 's'
        case 'Start':
            button = 'S'
        case 'SaveRAM':
            button = 'x'

    index = g_current_index
    input_list_mmap.seek(index)
    input_list_mmap.write(bytes(button, encoding="utf-8"))
    input_list_mmap.seek(100) #Position 0-99 are inputs, position 100 keeps the value of the current index
    input_list_mmap.write(bytes([index+1]))

    g_current_index +=1
    if g_current_index > 99:
        g_current_index = 0
