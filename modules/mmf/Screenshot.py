import io
import mmap
import logging

import cv2
import numpy
from PIL import Image, ImageFile

from modules.Config import GetConfig

ImageFile.LOAD_TRUNCATED_IMAGES = True
log = logging.getLogger(__name__)
config = GetConfig()


def GetScreenshot():
    while True:
        screenshot = None
        try:
            screenshot = Image.open(io.BytesIO(mmap.mmap(0, 24576, "bizhawk_screenshot-" + config["bot_instance_id"])))
            screenshot = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_BGR2RGB)
            return screenshot
        except Exception as e:
            log.debug("Failed to GetScreenshot(), trying again...")
            log.exception(str(e))
            if screenshot is not None:
                screenshot.close()
            # TODO return a black 240x160 image instead of None
            return None