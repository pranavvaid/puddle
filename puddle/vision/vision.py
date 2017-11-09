import cv2
import numpy as np
import dropletdetector
import UserConfig
import ElectrodeGrid
import HelperFunctions as func
import threading
import time

class Vision:
    
    def __init__(self):
        self.frame = None
        self.allElectrodes = []
        self.config = UserConfig.UserConfig('config.txt')
        self.detector = dropletdetector.DropletDetector(self.config)
        self.electrodeGrid = ElectrodeGrid.ElectrodeGrid(["input/Cartridge1FullData.txt", "input/Cartridge2FullData.txt", "input/Cartridge3FullData.txt", "input/Cartridge3InverseFullData.txt"])
        
    def process_image(self, img, recenter = False):
        startTime = time.time()
        if recenter:
            self.electrodeGrid.findVias(img)
        self.detector.updateExclusionZone(self.electrodeGrid, [1,1], [1,6], int(self.electrodeGrid.marker.center[1]), self.config.frameSize[0], [2,2], [2,12])
        grayImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.process_image_for_droplets(grayImg)
        self.process_image_background(grayImg)
#            im = img.copy()
#            self.detector.displayDropletsToImg(im, self.electrodeGrid)
#            func.displayKeyFeatures(im, marker = self.electrodeGrid.marker)
#            cv2.imshow('im', im)
        totTime = time.time() - startTime
        print("Vision FPS: " + str(1/totTime))
            
    def process_image_background(self, grayImg):
        self.detector.updateBackground(grayImg)
        
    def process_image_for_droplets(self, grayImg):
        self.detector.updateExclusionZone(self.electrodeGrid, [1,1], [1,6], int(self.electrodeGrid.marker.center[1]), self.config.frameSize[0], [2,2], [2,12])
        self.detector.detectDroplets(grayImg, self.electrodeGrid)
        
v = Vision()

frame2 = None
cap = cv2.VideoCapture("C:\\Users\\Pranav\\Desktop\\MergeandSplit.mp4")
flag = True
recenterFlag = True
def read_img():
    
    while cap.isOpened():
        startTime = time.time()
        ret, frame = cap.read()
        if frame is None:
            break
        global frame2
        frame2 = cv2.resize(frame, (1280, 720))
        if time.time()-startTime < 1/30:
            time.sleep((1/30)-(time.time()-startTime))
        totTime = time.time() - startTime
        print("\nRead FPS: " + str(1/totTime))
    global flag
    flag = False
    
            
import sys

if __name__ == "__main__":
    print("start")
    videoSource = threading.Thread(target = read_img)
    print("begin")
    videoSource.start()

    while flag:
        sys.stdout.flush()
        f = frame2
        if f is not None:
            v.process_image(f, recenter = recenterFlag)
            recenterFlag = False
        

#while cap.isOpened():
#    ret, frame = cap.read()
#    frame = cv2.resize(frame, (768, 432))
#    v.process_image(frame)
#    cv2.imshow('f', frame)
#    if cv2.waitKey(1) & 0xFF == ord('q'):
#        break