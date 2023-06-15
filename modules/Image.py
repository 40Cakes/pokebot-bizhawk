import cv2
import numpy
from PIL import Image, ImageGrab, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

def find_image(file: str): # Function to find an image in a BizHawk screenshot
    try:
        threshold = 0.999
        template = cv2.imread(f"data/templates/{GetEmu()['language']}/" + file, cv2.IMREAD_UNCHANGED)
        hh, ww = template.shape[:2]

        screenshot = GetScreenshot()    
        correlation = cv2.matchTemplate(screenshot, template[:,:,0:3], cv2.TM_CCORR_NORMED) # Do masked template matching and save correlation image
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(correlation)
        max_val_corr = float('{:.6f}'.format(max_val))
        if max_val_corr > threshold: 
            # Debug image detection - shows a window with a red square around the detected match
            #loc = numpy.where(correlation >= threshold)
            #result = screenshot.copy()
            #for point in zip(*loc[::-1]):
            #    cv2.rectangle(result, point, (point[0]+ww, point[1]+hh), (0,0,255), 1)
            #    cv2.imshow(f"match", result)
            #    cv2.waitKey(1)
            return True
        else:
            return False
        
    except Exception as e:
        log.exception(str(e))
        return False
