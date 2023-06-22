# This script displays the current screenshot that is stored in memory
import cv2
import time

from modules.Config import GetConfig
from modules.mmf.Screenshot import GetScreenshot

config = GetConfig()

poll_interval = 100 # Time to wait before checking for the next frame (ms)

while True:
    try:
        screenshot = GetScreenshot()
        cv2.imshow(f"ViewScreenshot-{config['bot_instance_id']}", screenshot)
        cv2.waitKey(1)
        time.sleep(poll_interval/1000)
    except Exception as e:
        print(str(e))