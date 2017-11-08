import cv2
import numpy as np
import math 
import HelperFunctions as func

class Droplet:
    def __init__(self, key, contour, config, parents = None, children = None, actualVolume = -9999):

        self.config = config
        
        # The id of the droplet
        self.key = key
        # The contour of the droplet
        self.contour = contour
        self.approxContour = None
        self.area = None
        self.center = None
        self.framesInExistence = 0
        self.actualVolume = actualVolume
        # If the contour of the droplet is defined
        if self.contour is not None:
            # The approximate contour of the droplet (to smooth the droplet contour out)
            self.approxContour =  cv2.approxPolyDP(contour, 0.01*cv2.arcLength(contour, True), True)
            # Area of the droplet contour
            self.area = cv2.contourArea(self.approxContour)
            self.previousArea = 0
            # The center of the droplet
            M = cv2.moments(self.contour)
            self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            
        # The real contour of the droplet (for cases in which the droplet contour is temporarily overwritten)
        self.realContour = contour
        
        # The volume of the droplet
        self.volume = 0
        self.stdVol = 0
        self.meanVol = 0
        
        # The path tracker object of the droplet
        self.pathTracker = None
        # The output file for the droplet position
        self.outputFile = None
        
        # The electrode closest to the droplet
        self.closestElectrodes = []
        self.electrodeClosestToCenter = None
        self.lastElectrodeClosestToCenter = None
        # The current coordinate of the droplet
        self.currentLocations = []
        
        # The coordinate of the droplet in the previous update
        self.oldLocations = []
        
        # The coordinate of the previous electrode the droplet was on
        self.lastLocations = []
        
        self.distToLastElectrode = None
        
        # The contour of the droplet in the previous iteration
        self.oldContour = None
        # The point on the droplet contour that is the largest defect
        self.largestDefectPoint = None
        # The instantaneous speed (in pixels per frame) of the droplet
        self.speed = 0
        # The similarity of the area of the droplet to its min enclosing circle
        self.similarity = 0
        # True if the droplet has been irregular for multiple frames in a row
        self.dropletVeryIrregular = False
        # Stores the consecutive frames a droplet has been irregular or merged
        self.consecutiveTimesIrregular = 0
        self.consecutiveTimesMerged = {}
        self.epsilon = 0.001
        
        self.allVolumes = []
        
        # If children exist, store them
        if children is None:
            self.children = []
        else:
            self.children = children
        # If parents exist, store them
        if parents is None:
            self.parents = []
        else:
            self.parents = parents

        self.findIrregularity()
        
    # This function relocates the droplet from multiple contours
    # Inputs are the contours, the distance between electrodes in pixels, the maximum # of electrodes the droplet center can change by
    # the frame of irregularity until the droplet is considered very irregular, and the frame in between updates of this function
    def relocateDroplet(self, contours, pixelDistBtwnElectrodes, countUntilIrregular = 20, framesBetweenUpdates = 1):
        minScore = None
        bestContour = None
        
        # Find the contour with the minimum score (which is most likely to be the contour for the same droplet)
        for c in contours:
            score = self.findScore(c, pixelDistBtwnElectrodes)
            if minScore is None or minScore>score:
                minScore = score
                bestContour = c
                
        # Find the new center of the droplet
        M = cv2.moments(bestContour)
        bestCenter = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        # If the droplet seems to have moved a distance of more than 3 electrodes / 
        # then it probably doesn't exist (such as by moving off the electrode grid)
        if func.findDist(*self.center, *bestCenter) > (pixelDistBtwnElectrodes * self.config.maxTravelDist)**2:
            print("Droplet " + str(self.key) + " has moved too much this frame")
            # Mark this droplet as having no contour (so that it can be marked for removal later)
            bestContour = None
            self.oldContour = self.contour
            self.contour = bestContour
            self.realContour = self.contour
            return bestContour

        # Store the droplets old contour so that we can revert to it if necessary (such as when confirming a merge)
        self.oldContour = self.contour
        
        # Store the best contour
        self.contour = bestContour
        self.realContour = self.contour
        self.approxContour =  cv2.approxPolyDP(self.contour, self.epsilon*cv2.arcLength(self.contour, True), True)
        
        # Store the old center in order to determine the instantaneous speed of the droplet
        oldCenter = self.center
        
        # Store the center and area of the droplet
        M = cv2.moments(self.contour)
        self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        self.previousArea = self.area
        self.area = cv2.contourArea(self.approxContour)
        
        # Find the speed of the droplet
        self.speed = math.sqrt(func.findDist(*oldCenter, *self.center))/framesBetweenUpdates
        
        # Find the irregularity of the droplet
        self.findIrregularity()
        
        # If the droplet takes up less than 40% of the area of its min enclosing circle / 
        # then count the number of consecutive times the droplet has been irregular
        if self.similarity<0.4:
            self.consecutiveTimesIrregular += 1
        else:
            self.consecutiveTimesIrregular = 0
        # If the droplet is irregular for more the the threshold amount of frames (currently 20)
        # then mark it as very irregular, so that it can be removed if necessary
        if self.consecutiveTimesIrregular>countUntilIrregular:
            self.dropletVeryIrregular = True
        
        # Count the number of frames 
        self.framesInExistence += 1
        return bestContour
    
    # Finds the "sameness" score for a contour compared to the current contour
    def findScore(self, newContour, pixelDistBtwnElectrodes):
        M = cv2.moments(newContour)
        newContourCenter = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        
        # Find the percent change in center and area
        percentChangeInCenter = math.sqrt(func.findDist(*self.center, *newContourCenter))/pixelDistBtwnElectrodes
        percentChangeInArea = abs(self.area-cv2.contourArea(newContour))/self.area
        
        # Calculate the "sameness" score of the droplet on a scale
        score = percentChangeInCenter + percentChangeInArea*0.7
        return score
    
    def addToChildren(self, toAdd):
        self.children.append(toAdd)
    
    # Calculate different metrics for the "regularity" of the droplet
    def findIrregularity(self):
        if self.approxContour is None:
            return
        # Find what percent of the min enclosing circle is the droplet
        (x,y), r = cv2.minEnclosingCircle(self.approxContour)
        self.similarity = (cv2.contourArea(self.approxContour))/(math.pi * r**2)
        
        # Find convexity defects in the contour of the droplet
        # Convexity defects are points at which the droplet contour bends inwards relative to the contour hull
        self.hull = cv2.convexHull(self.contour, returnPoints = False)
        self.defects = cv2.convexityDefects(self.contour, self.hull)
        
        # Find the point with the largest defect distance
        self.largestDefectDepth = 0
        self.largestDefectPoint = None
        for i in range (self.defects.shape[0]):
            start, end, far, depth = self.defects[i, 0]
            # Find the distance of the defect in pixels
            defectDistance = depth/256.0
            if defectDistance>self.largestDefectDepth:
                self.largestDefectDepth = defectDistance
                # Store the point on the contour that is the largest defect
                self.largestDefectPoint = tuple(self.contour[far][0])
        # Find the distance of the droplet to the last electrode with a point polygon test
        # Point polygon test returns a positive distance if the electrode center is in the droplet contour, and negative if its outside
        if self.lastElectrodeClosestToCenter is not None:
            self.distToLastElectrode = cv2.pointPolygonTest(self.approxContour, self.lastElectrodeClosestToCenter.center, True)
            
    # Overwrites the droplet contour
    # NOTE: Doesn't reset old contour!!!! (on purpose)
    def setContour(self, contour):
        self.contour = contour
        # If the contour is not None (which means we aren't trying to force the droplet to delete itself, then recalculate contour related values)
        if contour is not None:
            self.approxContour =  cv2.approxPolyDP(self.contour, self.epsilon*cv2.arcLength(self.contour, True), True)
            # Store the center and area of the droplet
            M = cv2.moments(self.contour)
            self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            self.previousArea = self.area
            self.area = cv2.contourArea(self.contour)
            self.findIrregularity()
    
    # Finds the closest electrode(s) to the droplet
    # Inputs are the electrode grid and the fraction of an electrode that a via needs to be in/out of a droplet to be added to current locations
    def findClosestElectrodes(self, electrodeGrid, removeAddThreshold = 0.1):
        electrodeClosestToCenter = None
        minDist = None
        for electrode in electrodeGrid.electrodes:
            distToElectrode = cv2.pointPolygonTest(self.approxContour, electrode.center, True)
            squaredDist = func.findDist(*self.center,*electrode.center)
            # Find the electrode closest to the droplet center
            if minDist is None or squaredDist<minDist:
                minDist = squaredDist
                electrodeClosestToCenter = electrode
            if electrode in self.closestElectrodes:
                if distToElectrode < electrodeGrid.electrode_size_cam[0] * -1 * removeAddThreshold:
                    self.closestElectrodes.remove(electrode)
            else:
                if distToElectrode > electrodeGrid.electrode_size_cam[0] * removeAddThreshold:
                    self.closestElectrodes.append(electrode)
                    
        self.electrodeClosestToCenter = electrodeClosestToCenter
        
        if len(self.closestElectrodes) == 0:
            print("Droplet is not conclusively located on any electrode.\n")
            self.closestElectrodes.append(electrodeClosestToCenter)
        self.currentLocations = [electrode.location for electrode in self.closestElectrodes]
    
    # finds the droplet color
    def findDropletColor(self, frame):
        newImg = frame.copy()
        newImg = cv2.cvtColor(newImg, cv2.COLOR_BGR2YCrCb)
        extractedDropletImg = func.extractImgAtContour([self.approxContour], frame)
        b = extractedDropletImg[:,:,0]
        g = extractedDropletImg[:,:,1]
        r = extractedDropletImg[:,:,2]
        # Get the mean rgb values of the droplet
        self.color = [np.mean(b[b>0]), np.mean(g[g>0]), np.mean(r[r>0])]
        
    # Retrieves an array with all parent ids of the droplet by using recursion
    def getAllParentIds(self):
        # Base case for the recursion
        if len(self.parents) == 0:
            return []
        else:
            parentArray = [parent.key for parent in self.parents]
            for parent in self.parents:
                parentArray += parent.getAllParentIds()
        return parentArray
    
    # Retrieves an array with all child ids of the droplet by using recursion
    def getAllChildIds(self):
        # Base case for recursion
        if len(self.children) == 0:
            return []
        else:
            childArray = [child.key for child in self.children]
            for child in self.children:
                childArray += child.getAllChildIds()
        return childArray
    
    # Draws the approx contour of the droplet to the img
    def drawContour(self, img, color = (0,0,255), drawCenter = True):
        cv2.drawContours(img, [self.approxContour], -1, color, 1)
        # If drawcenter is true, draw the center of the contour to the image as well
        if drawCenter:
            cv2.circle(img, self.center, 3, (255,255,255), -1)