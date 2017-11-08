import cv2
import numpy as np
import dropletdetector
import UserConfig
import ElectrodeGrid
import HelperFunctions as func
import threading

#frame = cv2.imread("C:\\Users\\Pranav\\Desktop\\Capture2.png")
cap = cv2.VideoCapture("C:\\Users\\Pranav\\Desktop\\MergeandSplit.mp4")
class Vision:
    
    def __init__(self, vidSource = None):
        self.frame = None
        self.allElectrodes = []
        self.config = UserConfig.UserConfig('config.txt')
        self.detector = dropletdetector.DropletDetector(self.config)
        self.electrodeGrid = ElectrodeGrid.ElectrodeGrid(["input/Cartridge1FullData.txt", "input/Cartridge2FullData.txt", "input/Cartridge3FullData.txt", "input/Cartridge3InverseFullData.txt"])
        if vidSource is not None:
            self.cap = cv2.VideoCapture(vidSource)
    
    def read_img(self, imgSource):
        ret, self.frame = imgSource.read()
        
    def process_image(self, img):
        self.electrodeGrid.findVias(img)
        self.detector.updateExclusionZone(self.electrodeGrid, [1,1], [1,6], int(self.electrodeGrid.marker.center[1]), self.config.frameSize[0], [2,2], [2,12])
        grayImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.process_image_for_droplets(grayImg)
        self.process_image_background(grayImg)
        im = img.copy()
        self.detector.displayDropletsToImg(im, self.electrodeGrid)
        func.displayKeyFeatures(im, marker = self.electrodeGrid.marker)
        cv2.imshow('im', im)
        
    def process_image_background(self, grayImg):
        self.detector.updateBackground(grayImg)
        
    def process_image_for_droplets(self, grayImg):
        self.detector.updateExclusionZone(self.electrodeGrid, [1,1], [1,6], int(self.electrodeGrid.marker.center[1]), self.config.frameSize[0], [2,2], [2,12])
        self.detector.detectDroplets(grayImg, self.electrodeGrid)
        
    
#    def process_image_for_droplets(self, img, cell_size):
#        background = np.full((img.shape[0], img.shape[1]), 255, dtype = np.uint8)
#        absDiff = cv2.absdiff(background, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
#        
#        # Find the droplet by applying a binary threshold to the image with the background subtracted
#        __, diffThresh = cv2.threshold(absDiff, 3, 255, cv2.THRESH_BINARY)
#        
#        # Find the contours on the thresholded image
#        _,cnts,_ = cv2.findContours(diffThresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
#        a = img.copy()
#        for e in self.allElectrodes:
#            cv2.circle(a, e, 2, -1, -1)
#        cv2.imshow('a', cv2.drawContours(a, cnts, -1, (255,0,255), 3))
#        if cv2.waitKey() == 1:
#            pass
#        
#        contourCenters = []
#        
#        for cnt in cnts:
#            M = cv2.moments(cnt)
#            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
#            contourCenters.append(center)
#            print(determineCurrentLocations(cnt, self.allElectrodes, 200))
#        return [findClosestElectrode(*center, cell_size) for center in contourCenters]
        
    
def findClosestElectrode(x, y, cell_size):
    return (int(round((x+cell_size/2)/cell_size-1, 0)), int(round((y+cell_size/2)/cell_size-1, 0)))

def determineCurrentLocations(dropletContour, electrodeGrid, cell_size):
    currentElectrodes = []
    for electrodeCenter in electrodeGrid:
        distToElectrode = cv2.pointPolygonTest(dropletContour, electrodeCenter, True)
        if(distToElectrode>0):
            currentElectrodes.append(electrodeCenter)
    return [(int(round((x+cell_size/2)/cell_size-1, 0)), int(round((y+cell_size/2)/cell_size-1, 0))) for x,y in currentElectrodes]
    

v = Vision()
while cap.isOpened():
    ret, frame = cap.read()
    frame = cv2.resize(frame, (768, 432))
    v.process_image(frame)
    cv2.imshow('f', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break