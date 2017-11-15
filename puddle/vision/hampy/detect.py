import cv2

from numpy import array, all, zeros, ones, rot90
from matplotlib.mlab import find

from .hamming_marker import HammingMarker, marker_size
from .hamming import decode
import numpy as np
np.set_printoptions(threshold = np.inf)

def detect_markers(img, marker_ids=None):
    # Determine width and height of image
    width, height, _ = img.shape
    
    # Convert image to grayscale, locate all edges using canny detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 100)
#    cv2.imshow('edges', edges)

    # Locate all contours on a copy of the edges image
    _, contours, _ = cv2.findContours(edges.copy(),
                                      cv2.RETR_TREE,
                                      cv2.CHAIN_APPROX_NONE)

    # Keep large contours
    min_area = width * height * .001
    contours = [c for c in contours if cv2.contourArea(c) > min_area]

    warped_size = 90 * 10
    canonical_marker_coords = array(((0, 0),
                                     (warped_size - 1, 0),
                                     (warped_size - 1, warped_size - 1),
                                     (0, warped_size - 1)),
                                    dtype='float32')

    markers = []
    a = img.copy()
    meanLight = None
    for c in contours:    
        # Keep contours that approximate to square and are concave
        approx_curve = cv2.approxPolyDP(c, len(c) * 0.01, True)
        cv2.drawContours(a, [approx_curve], -1, (255,255,255), 1)
        if not (len(approx_curve) == 4 and cv2.isContourConvex(approx_curve)):
            continue
        
        # Determine smallest convex shape that holds marker/contour
        sorted_curve = array(cv2.convexHull(approx_curve, clockwise=False),
                             dtype='float32')

        # Crop perspective to contour, reshape to marker
        persp_transf = cv2.getPerspectiveTransform(sorted_curve,
                                                   canonical_marker_coords)
        warped_gray = cv2.warpPerspective(gray, persp_transf,
                                         (warped_size, warped_size))
        
        # Find the mean brightness/color of the marker
        meanLight = cv2.mean(warped_gray)[0]
        
        # Convert to a black or white image using an adaptive threshold
        # The blockSize parameter was determined by utilizing a trackbar to change the parameter until noise was minimized
        warped_bin = cv2.adaptiveThreshold(warped_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 231, 1)
        warped_bin = cv2.bitwise_not(warped_bin)
        marker = warped_bin.reshape([marker_size,
                                     warped_size // marker_size,
                                     marker_size,
                                     warped_size // marker_size])  # Needs // int division to not create a float in py3
        marker = marker.mean(axis=3).mean(axis=1)
        marker.mean()
        marker[marker < 127] = 0
        marker[marker >= 127] = 1
    
        # Eliminate the entirely black or white markers
        # for robustness purposes
        sub_marker = marker[1:-1, 1:-1]
        sub_size = marker_size - 2
        if (all(sub_marker == zeros((sub_size, sub_size))) or
                all(sub_marker == ones((sub_size, sub_size)))):
            continue

        _, _, marker_w, marker_h = cv2.boundingRect(c)
        
        totalRotation = 0
        # Rotate orientation until id match (hamming decoding)
        # Otherwise, not valid marker.
        for _ in range(4):
            try:
                code = decode(sub_marker).flatten()[::-1]
                id = (2 ** find(code == 1)).sum()
                markers.append(HammingMarker(id=id, contours=approx_curve, img_size=(marker_w, marker_h), rotationApplied = totalRotation))
            except ValueError:  # The hamming code is incorrect
                pass
            sub_marker = rot90(sub_marker)
            totalRotation += 90
    #cv2.imshow('a', a)
    # Remove duplicates
    markers = {m.id: m for m in markers}.values()
    return markers
