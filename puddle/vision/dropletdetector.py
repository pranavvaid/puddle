import numpy as np
import cv2
import math
import HelperFunctions as func
import Droplet
import Line
import threading
import copy

def nothing(x):
    pass

class DropletDetector:
    def __init__(self, config):
        
        self.lock = threading.Lock()
        
        self.config = config
        self.frameSize = config.frameSize
        
        # Holds the cumulative array of values
        self.cumulative = np.zeros((self.frameSize[0], self.frameSize[1]))
        self.cumMean = np.zeros((self.frameSize[0], self.frameSize[1]), dtype = np.uint8)  
        
        self.backgroundRetrieved = False
                
        # All droplets that existed. Ever.
        self.allDropletsThatExisted = []
        
        # A binary mask of the droplet locations
        self.dropletMask = np.zeros((self.frameSize[0], self.frameSize[1]), np.uint8)
        
        # All currently existing droplets
        self.droplets = []
        
        # Droplets that were removed because they were found to be too irregular
        self.removedDroplets = []
        
        # Droplets that have yet to be confirmed as real
        self.dropletBuffer = []
        
        # The number of droplets that are expected, the number initialized, and the current state of initialization (0, 1, or 2)
        self.numDroplets = config.numDroplets
        self.totalDropletsInitialized = 0
        self.allDropletsInitialized = 0
        
        # A contour of the exclusion zone (where the droplets will start off)
        self.exclusionZone = None
        
        # The line along which droplets will be initialized        
        self.initializationLine = Line.Line(0,0,1,1)
        self.exclusionZoneInitialized = False
            
        # The next available id for a droplet
        self.nextAvailableKey = 0
        
        # The weights for the previous background and the incoming frame in determining the background image
        self.previousWeight = 0.9999
        self.incomingWeight = 0.0001
        
        
    # Updates the background image
    def updateBackground(self, grayFrame):
        self.updateDropletMask()
        
        # At the first frame, "pop" the background everywhere besides the exclusion zone
        if not self.backgroundRetrieved:
            # Pop the background everywhere besides the exclusion area (divide by 255 to get a np array of float64)
            self.cumulative += func.extractImgAtContour(self.exclusionZone, grayFrame, invImg = True, frameSize = self.frameSize)/255
            self.backgroundRetrieved = True
            
        # Called when all droplet are outside the initialization area (allDropletsInitialized is 1)
        if self.allDropletsInitialized == 1:
            # Pop the background at the exclusion area (divide by 255 to get a np array of float64)
            self.cumulative += func.extractImgAtContour(self.exclusionZone, grayFrame, frameSize = self.frameSize)/255
            # Signify that the exclusion area is able to be used now by setting allDropletsInitialized to 2
            self.allDropletsInitialized = 2
            # Make the background more responsize to change (now that we know where all droplets are)
            self.previousWeight = 0.99
            self.incomingWeight = 0.01
            print("ALL INITIALIZED")
            
        # Find where the droplet is not there, divide by 255 to get values of either 0 or 1
        invMask = cv2.bitwise_not(self.dropletMask)/255
        
        # Temporarily store the old background before it is overwritten
        old = self.cumulative
        
        # Do an IIR filter for the background
        self.cumulative = self.cumulative*self.previousWeight + grayFrame/255*self.incomingWeight
        
        # Don't change the background at places where the droplets are located
        self.cumulative[invMask==0] = old[invMask==0]
        
        # Convert the background to an integer scale (rather than a float), so that we can subtract it from the frame
        self.cumMean = np.array(self.cumulative*255, dtype = np.uint8)
        
    def updateDropletMask(self):
        self.dropletMask = np.zeros((self.frameSize[0],self.frameSize[1]), np.uint8)
        
        # Fill in the mask at areas where the droplet is located
        for droplet in self.droplets:
            cv2.drawContours(self.dropletMask, [droplet.approxContour], -1, (255), -1)
            
        # Dilate the mask to form a cushion around the location where the droplet is / 
        # so that if the droplet moves, the droplet mask still contains the droplet
        self.dropletMask = cv2.dilate(self.dropletMask, None, iterations = 5)
        # If the exclusion area is active then add it to the droplet mask (so it won't be updated)
        if self.allDropletsInitialized == 0:
            cv2.drawContours(self.dropletMask, self.exclusionZone, -1, (255), -1)
    
    def updateExclusionZone(self, electrodeGrid, bound1, bound2, topBound, bottomBound, initializationBound1, initializationBound2):
        if not self.exclusionZoneInitialized:
            b1 = next((electrode for electrode in electrodeGrid.electrodes if electrode.location == bound1), None).center
            b2 = next((electrode for electrode in electrodeGrid.electrodes if electrode.location == bound2), None).center
            boundingLine = Line.Line(*b1, *b2)
            topRightBound = int(boundingLine.solveForX(topBound))
            bottomRightBound = int(boundingLine.solveForX(bottomBound))
            
            self.exclusionZone = [np.array([[[0, topBound]], [[topRightBound, topBound]],[[bottomRightBound, bottomBound]], [[0, bottomBound]]])]
            initPoint1 = tuple(sum(coord) for coord in zip(next((electrode for electrode in electrodeGrid.electrodes if electrode.location == initializationBound1), None).center, (electrodeGrid.electrode_size_cam[0]*0.75, 0)))
            initPoint2 = tuple(sum(coord) for coord in zip(next((electrode for electrode in electrodeGrid.electrodes if electrode.location == initializationBound2), None).center, (electrodeGrid.electrode_size_cam[0]*0.75, 0)))
            
            self.initializationLine = Line.Line(*initPoint1, *initPoint2)
            self.exclusionZoneInitialized = True
    
    def initializeNewDroplets(self, contours):
        # Array of the currently known contours of droplets
        dropletContours = [d.realContour for d in self.droplets]
        for c in contours:
            M = cv2.moments(c)
            cCenter = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            # If a contour is within a certain pixel value of the initialization line and not already a droplet, then make that contour a new droplet
            if not func.containsArray(c, dropletContours) and self.initializationLine.findDistanceToPoint(cCenter)<10:
                newDroplet = Droplet.Droplet(self.nextAvailableKey, c, self.config, actualVolume = self.config.initVolume)
                self.modifyDroplets(append = newDroplet)
                self.allDropletsThatExisted.append(newDroplet)
                self.nextAvailableKey += 1
                self.totalDropletsInitialized += 1
                if self.allDropletsInitialized == 1:
                    print("More contours were detected than expected!")
                # If the total number of droplets initialized by the program matches the user specified initial droplets, then all droplets are initialized
                if self.totalDropletsInitialized == self.numDroplets and self.allDropletsInitialized == 0:
                    self.allDropletsInitialized = 1
    
    # Finds the droplets previously detected from among the provided contours
    def findDroplets(self, contours, electrodeGrid):
        self.lock.acquire()
        for i in range(len(self.droplets)):
            self.droplets[i].relocateDroplet(contours, electrodeGrid.electrode_size_cam[0])
        self.lock.release()
        
    # Filters out contours unlikely to be droplets
    def filterContours(self, contours):
        filteredContours = []
        # Remove any contours that are too elongated or small
        for c in contours:
            _, (w, h), _ = cv2.minAreaRect(c)
            if w != 0 and h != 0 and w/h < 9 and h/w < 9 and cv2.contourArea(c)>50 and cv2.contourArea(c)<20000:
                filteredContours.append(c)
        return filteredContours
    
    # Detects the droplets in a grayscale frame
    def detectDroplets(self, grayFrame, electrodeGrid):
        # Blur the grayscale frame (to get rid of noise)
        blurBackground = self.cumMean
        # If the droplets have not been initialized, then temporarily add the exclusion zone to the background (to prevent a ghost contour)
        if self.allDropletsInitialized == 0:
            blurBackground = self.cumMean + func.extractImgAtContour(self.exclusionZone, grayFrame, frameSize = self.frameSize)
            
        # Find the difference between the grayscale frame and the background
        absDiff = cv2.absdiff(grayFrame, blurBackground)
        
        # Find the droplet by applying a binary threshold to the image with the background subtracted
        __, diffThresh = cv2.threshold(absDiff, 3, 255, cv2.THRESH_BINARY)
        
        #If the droplets have not been initialized, make sure the exclusion zone is ignored by forcing the difference there to be 0
        if self.allDropletsInitialized == 0:
            cv2.drawContours(diffThresh, self.exclusionZone, -1, (0), -1)  
            
        # Get rid of noise by eroding the image
        diffThresh = cv2.erode(diffThresh, None, iterations=1)

        # Find the contours on the thresholded image
        _,cnts,_ = cv2.findContours(diffThresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter out small, large, or irregular contours
        cnts = self.filterContours(cnts)
        
        # As long as contours were found, and not too many droplets were found at once (which would suggest false droplet detection due to background shift) /
        # then proceed by finding droplets in the frame and removing irregular droplets
        if len(cnts)>0 and len(cnts)<len(self.droplets)*2 + self.numDroplets + 1:
                # Refind the droplets from among the contours
                self.findDroplets(cnts, electrodeGrid)
                # Remove any droplets that are too irregular from the current droplets, as well as droplets that have a "None" as a contour
                self.removeIrregularDroplets()
                # If all droplets have not yet been initialized, then allow for new droplets to be initialized
                if self.allDropletsInitialized == 0:
                    self.initializeNewDroplets(cnts)
                # Find any droplets that have been merged
                self.findMergedDroplets()
                # If all droplets have been initialized, then try to detect splitted droplets
                # Do not do this when droplets have not been initialized, as the unaccounted droplets may be registered as splitted droplets
                if self.allDropletsInitialized == 2:
                    self.findSplittedDroplets(cnts, electrodeGrid)

    # Detects any merging of droplets
    def findMergedDroplets(self, framesToConfirmMerge = 3):
        numTerms = len(self.droplets)
        dropletsCopy = list(self.droplets)
        # For each droplet
        i = 0
        while i < numTerms:
            # Start the merged droplets array with the currently selected droplet
            mergedDroplets = [dropletsCopy[i]]
            j = i+1
            # For all the other droplets in the droplets array
            while j<numTerms:
                # If the two droplets have the same center, it means they merged
                if dropletsCopy[i].center == dropletsCopy[j].center:
                    # Make sure that the merge has been detected for enough consecutive frames before confirming it
                    if dropletsCopy[i].consecutiveTimesMerged.get(dropletsCopy[j].key, 0) >= framesToConfirmMerge or dropletsCopy[j].consecutiveTimesMerged.get(dropletsCopy[i].key, 0) >= framesToConfirmMerge:
                        # Add the droplet to the merged droplets array and remove it from the dropletsCopy array (so it won't be considered for a merge again)
                        mergedDroplets.append(dropletsCopy[j])
                        dropletsCopy.remove(dropletsCopy[j])
                        j -= 1
                        numTerms -= 1
                    # If the merge has not been confirmed, then make the droplets retain their pre-merge contour (until the merge can be confirmed)
                    else:
                        dropletsCopy[i].setContour(dropletsCopy[i].oldContour)
                        dropletsCopy[j].setContour(dropletsCopy[j].oldContour)
                        
                    # Increment the consecutive times the 2 droplets have been merged
                    dropletsCopy[i].consecutiveTimesMerged[dropletsCopy[j].key] = dropletsCopy[i].consecutiveTimesMerged.get(dropletsCopy[j].key,0) + 1
                    dropletsCopy[j].consecutiveTimesMerged[dropletsCopy[i].key] = dropletsCopy[j].consecutiveTimesMerged.get(dropletsCopy[i].key,0) + 1
                else:
                    # If the droplets have not been merged then make sure the consecutiveTimesMerged is 0
                    dropletsCopy[i].consecutiveTimesMerged[dropletsCopy[j].key] = 0
                    dropletsCopy[j].consecutiveTimesMerged[dropletsCopy[i].key] = 0
                j+=1
                
            # If 2 or more droplets merged during this function call, then add the merged droplet (with a new id) to the merged droplet array
            if len(mergedDroplets)>1:
                # Make the merged droplets parents of the new droplets
                newDroplet = Droplet.Droplet(self.nextAvailableKey, dropletsCopy[i].contour, self.config, parents = mergedDroplets, actualVolume = sum([d.actualVolume for d in mergedDroplets]))
                
                # Add the merged droplets as a child of the droplets that have merged
                for droplet in mergedDroplets:
                    droplet.children.append(newDroplet)
                self.nextAvailableKey += 1
                
                # Add the new merged droplet to the droplets array and remove the old droplet from the droplets array
                # The other droplet was removed in the above if statement
                dropletsCopy.append(newDroplet)
                self.allDropletsThatExisted.append(newDroplet)
                dropletsCopy.remove(dropletsCopy[i])
            i += 1
        self.modifyDroplets(newList = dropletsCopy)
    
    # Detects any splitting of droplets
    def findSplittedDroplets(self, cnts, electrodeGrid):
        dropletContours = [d.realContour for d in self.droplets]
        newDroplets = []
        for i in range(len(cnts)):
            # If a contour is found that is not currently a droplet
            if not func.containsArray(cnts[i], dropletContours):
                # Create a new temporary droplet based on that contour. We'll check if its valid in the next few lins
                tempDroplet = Droplet.Droplet(self.nextAvailableKey, cnts[i], self.config)
                tempDroplet.findClosestElectrodes(electrodeGrid)
                
                # Find all possible parent droplets by seeing what droplets had
                # Determine possible parents by finding droplets in previous frames that were on the electrode(s) that the new temporary droplet is on
                possibleParents = [droplet for droplet in self.droplets if any(currentLocation in droplet.lastLocations for currentLocation in tempDroplet.currentLocations)]
                # If no droplets in a previous frame were on the same electrodes as the new droplet, then consider all droplets as possible parents
                if len(possibleParents) == 0:
                    print("No conclusive parents were found, determining parent based on center locations")
                    possibleParents = list(self.droplets)
                
                # From the possible parents, find the one that has the center closest to the temporary droplet
                minDist = None
                closestDroplet = None
                for droplet in possibleParents:
                    currentDist = func.findDist(*tempDroplet.center, *droplet.center)
                    if minDist is None or currentDist<minDist:
                        minDist = currentDist
                        closestDroplet = droplet
                # Find the irregularity of the droplet
                tempDroplet.findIrregularity()
                # If there is no possible parent droplet, the parent droplet is invalid, or the parent droplet is too far away, then don't add the temp droplet to the droplets array
                if closestDroplet is None or closestDroplet.contour is None or minDist>(electrodeGrid.electrode_size_cam[0]*self.config.maxTravelDist)**2:
                    continue
                # Add the temp droplet to the droplets array
                self.nextAvailableKey += 1
                tempDroplet.parents = [closestDroplet]
                
                # Assign the other droplet from the split (the droplet that retained the parent id) a new id
                newDroplet2 = Droplet.Droplet(self.nextAvailableKey, closestDroplet.contour, self.config, parents = [closestDroplet])
                newDroplet2.findIrregularity()
                self.nextAvailableKey += 1
                
                newDroplets.append(tempDroplet)
                newDroplets.append(newDroplet2)
                
                # Add the new droplets as children to the parent droplets
                closestDroplet.children.append(tempDroplet)
                closestDroplet.children.append(newDroplet2)
                self.modifyDroplets(remove = closestDroplet)
        self.modifyDroplets(appendList = newDroplets)
        self.allDropletsThatExisted += newDroplets
    
    # Removes any droplets that are irregular and adjust the parent-child relationships accordingly
    def removeIrregularDroplets(self):
        dropletCopy = list(self.droplets)
        for droplet in dropletCopy:
            # Remove any invalid droplets
            if droplet.contour is None:
                print(droplet.key)
                print(droplet.area)
                self.modifyDroplets(remove = droplet)

    def modifyDroplets(self, append = None, remove = None, newList = None, appendList = None):
        self.lock.acquire()
        if append is not None:
            self.droplets.append(append)
        if remove is not None:
            self.droplets.remove(remove)
        if newList is not None:
            self.droplets =  newList
        if appendList is not None:
            self.droplets += appendList
        self.lock.release()
    
    def accessDroplets(self):
        self.lock.acquire()
        dropletData = copy.deepcopy(self.droplets)
        self.lock.release()
        return dropletData

    # Displays a droplet to the frame
    def displayDropletsToImg(self, img, electrodeGrid, contourColor = (255,255,255), drawCenter = False):
        # For each droplet, draw its contours and expected path (if provided)
        for droplet in self.droplets:
            droplet.drawContour(img, color = contourColor, drawCenter = drawCenter)