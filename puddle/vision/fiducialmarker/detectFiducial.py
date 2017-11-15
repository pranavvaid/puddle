import argparse
import cv2
import numpy as np
from .fiducial_marker import FiducialMarker

import math
def findDist(x1,y1,x2,y2):
    return ((x2-x1)**2 + (y2-y1)**2)

def detect_fiducials(img, maxArea):
    # Determine width and height of image
    width, height, _ = img.shape
    
    '''
    2 Options for edge detection (need to check which is faster/more reliable)
    OPTION 1:
        Blurring
        Canny edge detection threshold is 180 to 200 (or 70 to 200)
        Epsilon = 0.04
    OPTION 2:
        No Blurring
        Canny edge detection threshold is 240 to 250
        Epsilon = 0.02
    '''
    '''
    # Blur the image, convert to grayscale, and look for edges
    blurred = cv2.GaussianBlur(img, (5,5), 0)
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    #edges = cv2.Canny(gray, 180, 200)
    edges = cv2.Canny(gray, 70, 200)
    '''
    # Blur the image, convert to grayscale, and look for edges
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 200)
     # Locate all contours on a copy of the edges image
    _, contours, _ = cv2.findContours(edges.copy(),
                                      cv2.RETR_TREE,
                                      cv2.CHAIN_APPROX_NONE)
    # Keep large contours
    min_area = width * height * .001
    contours = [c for c in contours if cv2.contourArea(c) > min_area]
    
    finalPentagon = None
    minScore = None
    for c in contours:
        if cv2.contourArea(c) > maxArea:
            continue
        # Approximate detected contours to a polygon
        approx_curve = cv2.approxPolyDP(c, len(c) * 0.04, True)
        
        # If the curve is not convex and a pentagon then restart to the next pentagon
        if not (len(approx_curve) == 5 and cv2.isContourConvex(approx_curve)):
            continue
        # Determine the pentagon that is most likely to be the fiducial marker by assigning a score based on regularity of the shape and its area
        sidelengths = np.array([math.sqrt(findDist(*approx_curve[i-1][0], *approx_curve[i][0])) for i in range(len(approx_curve)-1)])
        score = np.std(sidelengths)/12 - cv2.contourArea(c)/2500
        # Find the pentagon with the minimum score
        if minScore is None or minScore>score:
            finalPentagon = FiducialMarker(contours = c)
            minScore = score
    return finalPentagon