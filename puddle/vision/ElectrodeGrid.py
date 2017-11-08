import math
import time
import re
import cv2
import numpy as np
np.set_printoptions(threshold = np.inf)

import Electrode
import Line
from hampy.hampy import detect_markers
from hampy.fiducialmarker import detect_fiducials
import HelperFunctions as func


class ElectrodeGrid:
    def __init__(self, filePathArray):
        self.filePathArray = filePathArray
        
        self.numRows, self.numColumns = 0, 0
        self.settingsData = {}
        self.electrodes = []
        # The size between the vias in the x and y directions
        self.electrode_size_mm = (0, 0)
        # The size of the QR code
        self.marker_size_mm = (0,0)
        # The distance between the center of the QR and the center of the first electrode
        self.elec_dis_QR_mm = (0, 0)
        # The angle between the center of the QR code to the center of the fiducial marker and the center of the QR code to the reference via/electrode
        self.referenceRotation = 0
        # The electrode that is being used as the reference (to be compared against the )
        self.electrodeToReference = [0,0]
        # Holds the average x and y size of the QR marker
        self.avgSizeX = 0
        self.avgSizeY = 0
        self.totalIterationsSize = 0
        self.prevQrID = None
        self.electrode_size_cam = None
        self.electrode_center = None
        self.marker = None
        self.fiducialMarker = None
        
    # Updates the running average for the marker size
    # INPUTS:
        # corners - the corners of the QR code
        # avgX - the current average width
        # avgY - the current average height
        # totalIterations - the current total iterations
    # OUTPUTS:
        # avgX - the new average width
        # avgY - the new average height
        # totalIterations - the new total iterations
    def updateSizeRunningAverage(self, corners):    
        sizeX = int(round(math.sqrt(func.findDist(*corners[0], *corners[1]))))
        sizeY = int(round(math.sqrt(func.findDist(*corners[0], *corners[2]))))
        self.avgSizeX = func.calcRunningAverage(self.avgSizeX, self.totalIterationsSize, sizeX)
        self.avgSizeY = func.calcRunningAverage(self.avgSizeY, self.totalIterationsSize, sizeY)
        self.totalIterationsSize += 1
    
    # Calculates the constants needed to correctly position the vias on the frame
    # INPUTS:
        # markerSizePixel - the observed size of the QR code in pixels
        # markerSizmm - the actual size of the QR code in mm
        # elecDisToQRmm - the actual x and y distance between the QR code and first electrode (or empty space on the top left of the grid)
        # electrodeSizemm - the actual difference between the vias in the x and y direction in mm
    # OUTPUTS:
        # electrode_center - the center of the first electrode (or empty space on the top left of the grid)
        # electrode_size_cam - the size of the electrodes in pixels
    def calcViaPlacementConstants(self, marker):
        # Find the multiplication difference between the observed and theoretical marker size
        tf_const = func.divPts(self.observedMarkerSize, self.marker_size_mm)
        # Assume that the QR code is a square and force the width and height to be equal
#        avgtf_const = (tf_const[0] + tf_const[1])/2
#        tf_const = [avgtf_const, avgtf_const]
        
        # pixels from qr code to electrode
        elec_dis_cam = func.multPts(tf_const, self.elec_dis_QR_mm)
        
        # pixel size of each electrode 
        self.electrode_size_cam = func.multPts(tf_const, self.electrode_size_mm)
        
        # center of first electrode (even if there isnt really an electrode there)
        self.electrode_center = marker.center + elec_dis_cam
    
    def storeDataFromTextfile(self):
        # The size between the vias in the x and y directions
        self.electrode_size_mm = self.settingsData["Electrode Size (mm)"]
        # The size of the QR code
        self.marker_size_mm = self.settingsData["Marker Size (mm)"]
        # The distance between the center of the QR and the center of the first electrode
        self.elec_dis_QR_mm = self.settingsData["Dist to 1st electrode (mm)"]
        # The angle between the center of the QR code to the center of the fiducial marker and the center of the QR code to the reference via/electrode
        self.referenceRotation = self.settingsData["Reference Rotation (radians)"]
        # The electrode that is being used as the reference (to be compared against the )
        self.electrodeToReference = self.settingsData["Electrode to reference"]
        self.avgSizeX, self.avgSizeY, self.totalIterationsSize = 0,0,0
    
    # Reads a text file containing the cartridge data
    # INPUTS:
        # gridKey - the key/ID associated with the grid that is to be read
        # filePathArray - an array containing all file paths that contain cartridge data
    # OUTPUTS:
        # cartridgeFound - a boolean that states whether the cartridge data was found in the filePathArray
    def readElectrodes(self, gridKey):
        startTimeStamp = time.time()  
        for file_path in self.filePathArray:
            # Open the provided file, throw an excenption if an error occurs
            try:
                file = open(file_path, 'r')
            except IOError as e:
                print(e)
                return
            except:
                print ("Unexpected error reading file", file_path)
                return
            
            line_num = 0
            countElectrodes = 0
            readingMapData = False
            cartridgeFound = False
    
            
            for line in file:
                # Are we reading the key for this electrode grid?
                readingKey = False
                # Find the end of the keyword (designated by the colon)
                i = line.find(":")
                keyword = None
                # Retrieve the keyword
                if i>=0:
                    keyword = line[:i]
                    line = line[i:]
                    # If we are reading the key, set the var to True so we can check if its the right key
                    if keyword == "Key":
                        readingKey = True
                # Find the beginning of the data (designated by the first open parentheses)
                openParenth = line.find("(")
                if openParenth < 0:
                    openParenth = line.find("[")
                
                # Store the data collected in a dictionary
                if openParenth >= 0:
                    data = line[openParenth:]
                    self.settingsData[keyword] = eval(data)
                    # If the key is incorrect then stop reading this file
                    if readingKey and self.settingsData[keyword] != gridKey:
                        break
                    elif readingKey and self.settingsData[keyword] == gridKey:
                        cartridgeFound = True
                
                # If we are reading the electrode map, check how many ones there are (otherwise 1's in the data may mess up the reading)
                if readingMapData:
                    # The number of columns is equal to the number of integers in one row
                    self.numColumns = len(re.findall('\d+', line))
                    # Fill out the electrode grid
                    for m in re.finditer('[1-9]', line):
                        countElectrodes += 1
                        self.electrodes.append(Electrode.Electrode(int(m.start() / 2), line_num, initialKey = int(m.group(0))))
                    line_num += 1
               
                # If the electrode grid is about to appear, set readingMapData to true
                if keyword == "Electrode Map":
                    readingMapData = True
            file.close()
            # If the correct cartridge was found, then don't check the rest of the files in the array
            if cartridgeFound:
                break
        # The number of rows is the total number of lines provided
        self.numRows = line_num
        return cartridgeFound
    
    # This function locates the vias by using the QR and fiducial marker
    # INPUTS:
        # img - the image to sarch
        # prevQrID - the previous QR code ID
    # OUTPUTS:
    #       electrodes - an array of the Electrode objects
    #       prevQrID - the QR code that was just used to detect the vias
    def findVias(self, img):
        startTimeStamp = time.time()    
        
        markers = detect_markers(img)
        maxArea = 20000
        for m in markers:
            maxArea = cv2.contourArea(m.contours) * 2
            break
        fiducialMarker = detect_fiducials(img, maxArea)
        if fiducialMarker is None: # FIX : Should have some sort of buffer/max limit to # of times fiducial marker cannot be detected
            fiducialMarker = self.fiducialMarker
        for m in markers:
            # If the QR code has changes or this is the first iteration, then update the cartridge data
            if self.prevQrID == None or self.prevQrID != m.id:
                # Read the data for the electrode grid from the text file given the key
                idFound = self.readElectrodes(m.id)
                print("Marker ID: " + str(m.id))
                if idFound:
                    self.storeDataFromTextfile()
                else:
                    return None
                self.prevQrID = m.id
            box = [c[0] for c in m.contours]
            corners = func.identifyCorners(box)
            
            # Find the top horizontal bound of the QR code
            topBorderQR = Line.Line(*corners[0], *corners[1], color = (255,255,255))
    
            # Calculate the actual marker size by finding the distance between the corners and keeping a running average
            self.updateSizeRunningAverage(corners)
            self.observedMarkerSize = [self.avgSizeX, self.avgSizeY]
    
            self.calcViaPlacementConstants(m)
            
            # Set the point to rotate around as the center of the marker
            pivotPoint = m.center
    
            # The total rotation by which points will be rotated
            totalRot = math.atan(topBorderQR.m)
            
            # Find the reference electrode in the electrodes array, and calculate its rotated center
            referenceElectrode = next((electrode for electrode in self.electrodes if electrode.location == self.electrodeToReference), None)
            unrotatedReferenceCenter = self.electrode_center + func.multPts(referenceElectrode.location, self.electrode_size_cam)
            rotatedReferenceCenter = func.rotate(unrotatedReferenceCenter, pivotPoint, totalRot)
            
            # If the fiducial marker was found, find the difference between what the rotation offset should be and what is observed -
            # and add that rotation to the total rotation to get the correct rotation
            if fiducialMarker:
                extraRot = self.referenceRotation - Line.Line(*m.center, *rotatedReferenceCenter).findAngle(Line.Line(*m.center, *fiducialMarker.center))
                totalRot += extraRot
            else:
                print("FIDUCIAL MARKER NOT FOUND. NO REDUNDANCY USED")
            
            # Go through all the electrodes and rotate their centers by the calculated value
            for electrode in self.electrodes:
                # find the unrotated center of the electrode
                center = self.electrode_center + func.multPts(electrode.location, self.electrode_size_cam)
                # find the rotated center of the electrodes
                electrode.center = func.roundPt((func.rotate(center, pivotPoint, totalRot)))
            self.marker = m
            self.fiducialMarker = fiducialMarker
            labeled = img.copy()
            func.displayKeyFeatures(labeled, marker = m, topBorder = topBorderQR, displayID = True, fiducialMarker = fiducialMarker, electrodes = self.electrodes)
            #cv2.imshow("label", labeled)
        return self.electrodes
    
    def calcFunctioningScores(self, circleSimilarityWeight = 1, defectWeight = 1, stickyMoveWeight = 1):
        for electrode in self.electrodes:
            if len(electrode.totalCircleSimilarity) > 0:
                electrode.functionScore = circleSimilarityWeight * (1-electrode.averageCircleSimilarity) + defectWeight * electrode.averageDefects*len(electrode.totalDefects)/50 + stickyMoveWeight * electrode.averageStickyMoves*len(electrode.totalStickyMoves)/50
            else:
                electrode.functionScore = -999
            #print(str(electrode.location), electrode.functionScore)
    
    def addIrregularitiesToElectrodes(self, droplets, stationarySpeedThreshold = 4.5):
        for droplet in droplets:
            # If the droplet is not a large droplet (it hasn't been created by merging 2 small droplets)
            if len(droplet.parents) < 2:
                # Find the electrode closest to the defect point and add the info to that electrode
                closestElectrodeToDefectPoint = func.findClosestElectrode(*droplet.largestDefectPoint, self.electrodes)
                closestElectrodeToDefectPoint.addDefect(droplet.largestDefectDepth, minDepthForDefect = self.electrode_size_cam[0]*0.4)
                if droplet.lastLocations != []:
                    previousElectrodes = [next((electrode for electrode in self.electrodes if electrode.location == lastLocation), None) for lastLocation in droplet.lastLocations]
                    # If the droplet is stationary/not moving, then check for sticky moves
                    if droplet.speed < stationarySpeedThreshold and droplet.distToLastElectrode is not None:
                        for previousElectrode in previousElectrodes:
                            previousElectrode.addStickyMove(droplet.distToLastElectrode)
                    # If the droplet is moving, then check for its similarity to a circle
                    else:
                        for previousElectrode in previousElectrodes:
                            previousElectrode.addCircleSimilarity(droplet.similarity)
                            
                            
    def updatePositionMatrix(self, droplets):
        self.currentPositions = np.zeros((self.numRows, self.numColumns), dtype = np.int16)
        self.currentPositions = np.chararray((self.numRows, self.numColumns), unicode = True)
        for electrode in self.electrodes:
            self.currentPositions[electrode.location[1]][electrode.location[0]] = '-'
        for i in range(self.numRows):
            for j in range(self.numColumns):
                if self.currentPositions[i][j] == '':
                    self.currentPositions[i][j] = '*'
        for droplet in droplets:
            for location in droplet.currentLocations:
                self.currentPositions[location[1]][location[0]] = droplet.key
                                     
    def updateScoresIrregularitiesPositions(self, droplets, stationarySpeedThreshold = 4, circleSimilarityWeight = 1, defectWeight = 1.5, stickyMoveWeight = 1.5):
        self.addIrregularitiesToElectrodes(droplets, stationarySpeedThreshold = stationarySpeedThreshold)
        self.calcFunctioningScores(circleSimilarityWeight = circleSimilarityWeight, defectWeight = defectWeight, stickyMoveWeight = stickyMoveWeight)
        self.updatePositionMatrix(droplets)