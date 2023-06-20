import io
import time
import mmap
import cv2
import numpy
import array
import logging
from PIL import Image

from modules.Config import GetConfig
from modules.Inputs import WaitFrames

log = logging.getLogger(__name__)
config = GetConfig()

def GetScreenshot():
    i = 0
    while True:
        try:
            screenshot = Image.open(io.BytesIO(mmap.mmap(0, 24576, "bizhawk_screenshot-" + config["bot_instance_id"])))
            screenshot = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_BGR2RGB)
            return screenshot
        except Exception as e:
            log.debug("Failed to GetScreenshot(), trying again...")
            log.exception(str(e))
            if screenshot is not None:
                screenshot.close()
            if i >= 5:
                return None
            i += 1