# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 13:07:56 2017

@author: Pranav
"""

import HelperFunctions as func
import cv2
import math

# The Line class models a line in y = mx + b form
# It is initially declared by defining two sets of points
class Line:
    # Initialize a line by defining two points on the line. The line color can be edited.
    def __init__(self, x1, y1, x2, y2, color = (0,0,100)):
        self.x1, self.y1, self.x2, self.y2 = x1,y1,x2,y2
        self.m,self.b = func.fitLine(x1,y1,x2,y2)
        self.secondCoordDeclared = True
        self.color = color
    
    # Returns the slope and intercept of the current line
    def getSlopeIntercept(self):
        return self.m,self.b
    
    # Returns the points that are being used to define the line    
    def getPoints(self):
        return self.x1,self.y1,self.x2,self.y2
    
    # Solve for y in y = mx + b, when given x
    def solveForY(self,xVal):
        return self.m * xVal + self.b
    
    # Solve for x in y = mx + b, when given y    
    def solveForX(self,yVal):
        return (yVal-self.b)/self.m
    
    # Set the equation of a line given the slope and one point
    def setEquationWithSlope(self,m,x1,y1):
        self.m = m
        self.b = y1 - self.m * x1
        self.x1 = x1
        self.y1 = y1
        self.secondCoordDeclared = False
        self.x2 = 0
        self.y2 = self.solveForY(0)
    
    # Display the line to the frame
    def dispToImg(self, img, xCoord):
        if self.secondCoordDeclared:
            cv2.line(img, (int(self.x1),int(self.y1)), (int(self.x2),int(self.y2)), self.color, thickness=1)
        else:
            self.x2 = xCoord
            self.y2 = self.solveForY(xCoord)
            cv2.line(img, (self.x1,self.y1), (xCoord,int(self.solveForY(xCoord))), self.color, thickness=1)
    
    # Find the intersection of 2 lines by using Cramer's Rule
    def findIntersection(self,other,shouldRound = False):
        yDiffThis = self.y1 - self.y2
        xDiffThis = self.x2 - self.x1
        detThis = -1 * (self.y2 * self.x1 - self.x2*self.y1)
        
        yDiffOther = other.y1 - other.y2
        xDiffOther = other.x2 - other.x1
        detOther = -1 * (other.y2 * other.x1 - other.x2*other.y1)
        
        detOverall = yDiffThis * xDiffOther - xDiffThis * yDiffOther
        detX = detThis * xDiffOther - xDiffThis* detOther
        detY = yDiffThis * detOther - detThis * yDiffOther
        if detOverall != 0:
            if not shouldRound:
                return (detX/detOverall, detY/detOverall)
            else:
                return (int(round(detX/detOverall,0)), int(round(detY/detOverall,0)))
        else:
            print("WARNING: Intersection of lines could not be found - the lines are either parallel or coinciding")
            return -99999,-99999
    
    # Find the angle with another line
    def findAngle(self, other):
        return math.atan((self.m-other.m)/(1+self.m*other.m))
    
    def pointHorizontalSide(self, point):
        if self.m != 0 and point[0]<self.solveForX(point[1]):
            return -1
        elif self.m != 0 and point[0] > self.solveForX(point[0]):
            return 1
        else:
            return 0
    
    # Find the shortest distance from the line to a point
    def findDistanceToPoint(self, point):
        return abs(self.b + self.m*point[0] - point[1])/math.sqrt(1+self.m*self.m)