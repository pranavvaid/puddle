
import time
import cv2
import numpy as np
import math

def showTimeElapsed(startTime, thresholdTime, functionName):
    return

# This function finds the distance between 2 points
# INPUTS: 2 coordinates, (x1,y1) and (x2,y2)
# OUTPUTS: Returns the squared distance between the coordinates
def findDist(x1,y1,x2,y2):
    return ((x2-x1)**2 + (y2-y1)**2)

# This function returns true or false depending on if two points are closer than MIN_DIST (in pixels)
# INPUTS: 2 coordinates, (x1,y1) and (x2,y2)
## OUTPUTS: Returns True if the two coordinates are closer than MIN_DIST, returns false otherwise
#def closeBy(x1,y1,x2,y2):
#    return findDist(x1,y1,x2,y2) <= userV.MIN_DIST

# This finds the point slope form equation of a line given two points. A vertical line is represented with an extremely high slope.
# INPUTS: 2 coordinates, (x1,y1) and (x2,y2)
# OUTPUTS: Returns the slope and y-intercept of a line going through the two points
def fitLine(x1,y1,x2,y2):
    # If the line is vertical, avoid a divide by 0 error by slightly offsetting x1 and x2
    if x2 == x1:
        x2 = x1 + 0.00001
    
    m = (y2-y1)/(x2-x1)
    b = y1 - m*x1
    return m,b

# This function returns a value of n that is clamped between minn and maxn
# INPUTS: n - variable
#         minn - min value the variable should be clamped to
#         maxn - max value the variable should be clamped to
# OUTPUTS: A value that is clamed between minn and maxn
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

# Divides 2 points by each other
def divPts(a, b):
    return [x/y for x, y in zip(a, b)]

# Multiplies 2 points together
def multPts(a, b):
    return [x*y for x, y in zip(a, b)]

# Rounds a point to the nearest int
def roundPt(pt):
    return int(round(pt[0])), int(round(pt[1]))

# This function finds the closest electrode to the points provided
# INPUTS:
#       Coordinates (x1,y1)
#       electrodes - an array of the known Electrode objects
# OUTPUTS:
#       minElectrode - the closest electrode
def findClosestElectrode(x1, y1, electrodes):
    startTimeStamp = time.time()
    
    minDist = None
    minElectrode = None
    for electrode in electrodes:
        squaredDist = findDist(x1,y1,*electrode.center)
        if minDist is None or squaredDist<minDist:
            minDist = squaredDist
            minElectrode = electrode
    showTimeElapsed(startTimeStamp, userV.THRESHOLD_TIME, "findClosestElectrode")
    return minElectrode
    
# Identifies the corners of a series of points
# INPUTS: An array of points to be scanned
# OUTPUTS: The top left, top right, bottom left, and bottom right points. If these points do not exist, None is returned for that value
def identifyCorners(points):
    topLeft = None
    topRight = None
    bottomLeft = None
    bottomRight = None

    # Find the top left, top right, bottom left, and bottom right points of the array
    for pt in points:
        if topLeft is None or (((pt[0]<topLeft[0] and not closeBy(pt[0], 0, topLeft[0], 0))) or ((pt[1]<topLeft[1] and not closeBy(0, pt[1], 0, topLeft[1])))):
            topLeft = pt
        if topRight is None or (((pt[0]>topRight[0] and not closeBy(pt[0], 0, topRight[0], 0))) or ((pt[1]<topRight[1] and not closeBy(0, pt[1], 0, topRight[1])))):
            topRight = pt
        if bottomLeft is None or (((pt[0]<bottomLeft[0] and not closeBy(pt[0], 0, bottomLeft[0], 0))) or ((pt[1]>bottomLeft[1] and not closeBy(0, pt[1], 0, bottomLeft[1])))):
            bottomLeft = pt
        if bottomRight is None or (((pt[0]>bottomRight[0] and not closeBy(pt[0], 0, bottomRight[0], 0))) or ((pt[1]>bottomRight[1] and not closeBy(0, pt[1], 0, bottomRight[1])))):
            bottomRight = pt
    return [topLeft,topRight,bottomLeft,bottomRight]

def closeBy(x1,y1,x2,y2):
    return findDist(x1,y1,x2,y2) <= 625

# Rotates a point
# INPUTS:
    # point - the point to be rotated
    # origin - the point that is the center for the rotation
    # angle - the angle (in radians) by which to rotate the point
# OUTPUTS:
    # nx, ny - the rotated x and y coordinate of the point
def rotate(point, origin, angle):
    ox, oy = origin
    px, py = point

    nx = ox + (px - ox) * math.cos(angle) - (py - oy) * math.sin(angle)
    ny = oy + (px - ox) * math.sin(angle) + (py - oy) * math.cos(angle)
    return nx, ny

# Calculates the running average of a series
# INPUTS:
    # currentAvg - the current running average
    # totalTermsBefore - the total number of terms (not including the term that is to be added)
    # newNum - the number to add to the running average
# OUTPUTS:
    # newAvg - the new average
def calcRunningAverage(currentAvg, totalTermsBefore, newNum):
    prevTotal = currentAvg * totalTermsBefore
    newTotal = prevTotal + newNum
    newAvg = newTotal / (totalTermsBefore+1)
    return newAvg;
    
# Displays key features the program uses onto the image
# INPUTS:
    # marker - HammingMarker object for the QR code
    # topBorder - the line that defines the top border of the QR code
    # displayID - whether the QR code id should be displayed
    # fiducialMarker - the FiducialMarker object for the fiducial marker
def displayKeyFeatures(img, marker = None, topBorder = None, displayID = False, fiducialMarker = None, electrodes = None):
    if marker:
        # Draw a contour around the QR code and its center
        marker.draw_contour(img, linewidth = 1)
        cv2.circle(img, roundPt((marker.center[0], marker.center[1])), 3, (255, 0, 0), -1)
        if displayID:
            # Print the code associated with the QR code
            cv2.putText(img, str(marker.id), tuple(int(p) for p in marker.center),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    # Draw the top border of the QR Code
    if topBorder:
        topBorder.dispToImg(img, 99999)
    # If a fiducial marker was found draw its contours and center
    if fiducialMarker:
        fiducialMarker.draw_contour(img)
        cv2.circle(img, (int(round(fiducialMarker.center[0])), int(round(fiducialMarker.center[1]))),2, (255,255,255), -1)
    # Print the via centers
    if electrodes:
        for electrode in electrodes:
            cv2.circle(img, electrode.center, 3, (255, 0, 0), -1)

# This function prints out the matrix to the console
# INPUTS:
#       matrixToPrint - the matrix to display to the console
#       additionalInfo - a dictionary containing the header of a new line as the key, and the value that should be displayed after the header as the value
#       whiteSpace - the number of empty lines to print before printing out the matrix (to make the console easier to read)
# OUTPUTS: matrix printed to console
def printCurrentMatrix(matrixToPrint, currentCoord, additionalInfo = {}, whiteSpace = 10):
    #Print the numpy array with the current position, and the coordinate of the droplet
    for i in range(0,whiteSpace):
        print()
    print("CURRENT POSITION OF DROPLET: \n")
    print (matrixToPrint)
    print("\nCurrent Coordinate of Droplet: " + str(currentCoord) + "\n")
    # Print any additional info provided (such as volume)
    for key in additionalInfo:
        print(key + str(additionalInfo[key]))
 
# Finds the area of an object/shape in mm^2, given its area in pixels^2
# INPUTS: areaInPixelsSquared - the area of the object in interest in terms of pixels^2
# OUTPUTS: The area of the object in interest in terms of mm^2
def findActualArea(areaInPixelsSquared, pixelsPerMMX, pixelsPerMMY):
    return areaInPixelsSquared / (pixelsPerMMX * pixelsPerMMY)

# Calulates the volume of an object in mm^3
# INPUTS: 
#       baseArea - the volume of the object in interest in terms of mm^3
#       height - the height of the droplet
#       shape - the shape of the object (currently, only cylinder is supported)       
# OUTPUTS: The volume of the object in interest in terms of mm^3
def calcVol(baseArea, height, shape = "cylinder"):
    if(shape == "cylinder"):
        return baseArea * height;
    else:
        return -1;

# This function deletes all contours from the contoursArray that is not in the range from minX to maxX or minY to maxY
# INPUTS:
#       contoursArray - reference to a list containing the contours
#       minX, minY - the minimum X and Y value that the contour center can be located at (to remain in the array)
#       maxX, maxY - the maximum X and Y value that the countour center can be located at (to remain in the array)
# OUTPUTS: contoursArray updated to contain only valid contours
def cleanUpContours(contoursArray, minX, minY, maxX, maxY):
    arraySize = len(contoursArray)
    i = 0
    # For each element in the contours array
    # We use a while loop rather than a for loop beacause elements from the array are removed in the loop
    while i<arraySize:
        # Find the center of the contour
        M = cv2.moments(contoursArray[i])
        approxCenterX = int(M["m10"] / M["m00"])
        approxCenterY = int(M["m01"] / M["m00"])
        
        # If the center is not in the range
        if(not minX<approxCenterX<maxX or not minY<approxCenterY<maxY):
            contoursArray.pop(i)
            # Update the max value i should go to (because the size of contoursArray is now different)
            arraySize = len(contoursArray)
            # Subtract 1 from i (to make sure an element will not be skipped)
            i = i-1;
        # Increment i
        i = i+1;
    # If no contours were found, print a warning
    if len(contoursArray) == 0:
        print("WARNING: No viable contours were found. Vias may not have been detected properly, HSV bounds may be incorrect, or no droplet is present")

def containsArray(smallArray, largeArray):
    smallArray = np.array(smallArray)
    for subArray in largeArray:
        subElements = np.reshape(subArray, (np.array(subArray).size))
        smallElements = np.reshape(smallArray, (smallArray.size))
        if len(subElements) != len(smallElements):
            continue
        #print(all(subElements[i] == smallElements[i] for i in range(len(smallElements))))
        if(all(subElements[i] == smallElements[i] for i in range(len(smallElements)))):
            return True
    return False

# Extracts a particular region of an image based on a contour
def extractImgAtContour(contour, parentImg, invImg = False, frameSize = [480, 640]):
    areaToColor = np.zeros((frameSize[0],frameSize[1]), dtype=np.uint8)
    imgOfArea = np.zeros((frameSize[0],frameSize[1]), dtype=np.uint8)
    # Fill in the contour area
    cv2.drawContours(areaToColor, contour, -1, (255), -1)
    if invImg:
        # Get the image everywhere besides the contour area
        imgOfArea = cv2.bitwise_and(parentImg, parentImg, mask = cv2.bitwise_not(areaToColor)) 
    else:
        # Get the image inside the contour area
        imgOfArea = cv2.bitwise_and(parentImg, parentImg, mask = areaToColor)
    return imgOfArea