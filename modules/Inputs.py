import json
import mmap
import time
import logging

from modules.Config import GetConfig
from modules.mmf.Emu import GetEmu

log = logging.getLogger(__name__)
config = GetConfig()

default_input = {"A": False, "B": False, "L": False, "R": False, "Up": False, "Down": False, "Left": False,
                 "Right": False, "Select": False, "Start": False, "Light Sensor": 0, "Power": False, "Tilt X": 0,
                 "Tilt Y": 0, "Tilt Z": 0, "SaveRAM": False}

input_list_mmap = mmap.mmap(-1, 4096, tagname="bizhawk_input_list-" + config["bot_instance_id"],
                            access=mmap.ACCESS_WRITE)
input_list_mmap.seek(0)

hold_input_mmap = mmap.mmap(-1, 4096, tagname="bizhawk_hold_input-" + config["bot_instance_id"],
                            access=mmap.ACCESS_WRITE)
hold_input = default_input

g_current_index = 1  # Variable that keeps track of what input in the list we are on.

for i in range(100):  # Clear any prior inputs from last time script ran in case you haven't refreshed in Lua
    input_list_mmap.write(bytes('a', encoding="utf-8"))


def HoldButton(button: str):
    """
    Function to update the hold_input object
    :param button: Button to hold
    """
    global hold_input
    log.debug(f"Holding: {button}...")

    hold_input[button] = True
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))


def ReleaseButton(button: str):
    """
    Function to update the hold_input object
    :param button: Button to release
    """
    global hold_input
    log.debug(f"Releasing: {button}...")

    hold_input[button] = False
    hold_input_mmap.seek(0)
    hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))


def ReleaseAllInputs():
    """Function to release all keys in all input objects"""
    global hold_input
    log.debug(f"Releasing all inputs...")

    for button in ["A", "B", "L", "R", "Up", "Down", "Left", "Right", "Select", "Start", "Power"]:
        hold_input[button] = False
        hold_input_mmap.seek(0)
        hold_input_mmap.write(bytes(json.dumps(hold_input), encoding="utf-8"))


def PressButton(button: str):
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
    input_list_mmap.seek(100)  # Position 0-99 are inputs, position 100 keeps the value of the current index
    input_list_mmap.write(bytes([index + 1]))

    g_current_index += 1
    if g_current_index > 99:
        g_current_index = 0


def ButtonCombo(sequence: list):
    """
    Function to send a sequence of inputs and delays to the emulator
    :param sequence: List of button/wait inputs to execute
    """
    for k in sequence:
        if type(k) is int:
            WaitFrames(k)
        else:
            PressButton(k)
            WaitFrames(1)


def WaitFrames(frames: float):
    time.sleep(max((frames / 60.0) / GetEmu()["speed"], 0.02))
