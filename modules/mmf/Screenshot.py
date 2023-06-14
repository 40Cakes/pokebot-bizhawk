import io
import time
import mmap
import cv2
import numpy
from PIL import Image

from modules.Config import GetConfig

config = GetConfig()

def GetScreenshot():
    try:
        screenshot = Image.open(io.BytesIO(mmap.mmap(0, 24576, "bizhawk_screenshot-" + config["bot_instance_id"])))
        screenshot = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_BGR2RGB)
        return screenshot
    except Exception as e:
        if screenshot is not None:
            screenshot.close()
        return None
