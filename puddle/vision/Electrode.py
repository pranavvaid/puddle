## Creates the object of electrode

#import hardware_def
from queue import *

#FluxlPad_height = hardware_def.FluxlPad_height
#FluxlPad_width = hardware_def.FluxlPad_width

class Electrode:
    dropCount = 0
    dropFinished = 0
    steps = 0
    # done == False

    def __init__(self, x, y, center = None, initialKey = 1): # type):
        self.volume = 0
        self.numVolumes = 0
        # self.name = name
        self.location = [x,y]
        # self.type = type # Type of actuator (sensor, normal electrode, dispenser...)
        self.state = False
        self.neighbors = False
        self.center = center
        # What integer the electrode is represent by in the text file
        self.initialKey = initialKey
        
        self.totalCircleSimilarity = []
        self.averageCircleSimilarity = 0
        
        self.totalDefects = []
        self.averageDefects = 0
        
        self.totalStickyMoves = []
        self.averageStickyMoves = 0
        
        self.functionScore = 0
        
        self.totalHeights = []
        self.averageHeight = 0
    
        self.distance = 0
        
    def addVolume(self, volume):
        self.volume = (self.volume * self.numVolumes + volume)/(self.numVolumes+1)
        self.numVolumes += 1
    
    # Adds data about the similarity of the droplet to a circle at that electrode
    def addCircleSimilarity(self, circleSimilarity):
        self.totalCircleSimilarity.append(circleSimilarity)
        self.averageCircleSimilarity = sum(self.totalCircleSimilarity)/len(self.totalCircleSimilarity)
    
    # Adds data about the largest defect in the droplet contour at that electrode
    # minDepthForDefect is the maximum depth of a defect (in pixels) necessary for the defect to be considered a significant defect
    def addDefect(self, defectDepth, minDepthForDefect = 20):
        if defectDepth > minDepthForDefect:
            self.totalDefects.append(defectDepth)
            self.averageDefects = sum(self.totalDefects)/len(self.totalDefects)
    
    # Adds data about how much a droplet sticks to that electrode when it has moved on to the next frame
    # minDistForSticky is the minimum distance that the center of the previous electrode has to be from the droplet to be considered sticky
        # A negative numbers (e.g. -2) means that it can be 2 pixels outside of the contour, while a positive number means it must be inside the contour
    def addStickyMove(self, distance, minDistForSticky = -2):
        if distance>minDistForSticky:
            self.totalStickyMoves.append(distance)
            self.averageStickyMoves = sum(self.totalStickyMoves)/len(self.totalStickyMoves)
    
    def addHeight(self, height):
        self.totalHeights.append(height)
        self.averageHeight = sum(self.totalHeights)/len(self.totalHeights)
    
    def location(self):
        return self.location

    def position_y(self):
        return self.y

#    def numOfDrops(self):
#        return Drop.dropCount
#
#    def finishedDrop(self):
#        return Drop.dropFinished
#
#    def stepsDone(self):
#        return Drop.steps
#
#    #Sets next step in sequence to current.
#    def nextS(self):
#        if self.path.qsize() > 0:
#            self.x = self.path.get()
#            self.y = self.path.get()
#            Drop.steps -= 1
#            # print ("Location:", self.x, self.y, "Path of size:", int(self.path.qsize()/2))
#        if self.path.empty() and not self.done:
#            Drop.dropFinished += 1
#            self.done = True
#            # print ("There are", Drop.dropFinished, "drops finished")

    # #Creates path to move to input coordinates
    def moveto(self, x_des, y_des):
        # print ("in move to", self.x, self.y, "des: ", x_des, y_des)
        while x_des != self.lastX or y_des != self.lastY:
            # print ("not there yet ", )
            if self.lastX < x_des:
                self.move_right(1)
            elif self.lastX > x_des:
                self.move_left(1)

            if self.lastY < y_des:
                self.move_down(1)
            elif self.lastY > y_des:
                self.move_up(1)


    def resetCoord(self, x_des, y_des):
        self.x = x_des
        self.y = y_des

    def returnto(self):
        self.x = self.lastX
        self.y = self.lastY
        
    def center(self):
        return self.center


    # def testElectrode(self):
    #     delay_t = 0
    #     for w in FluxlPad_width:
    #         for h
    #         self.move_right(1)
    #
    #     self.move




