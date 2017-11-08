# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 12:21:34 2017

@author: Pranav
"""

class UserConfig:
    
    def __init__(self, configFilePath):
        self.configFilePath = configFilePath
        self.configData = {}
        
        self.numDroplets = 1
        self.initVolume = 4
        self.maxTravelDist = 5
        self.frameSize = [480, 640]
        self.QRUpdateRate = 5
        self.dropletHeight = 0.37
        
        self.readConfigFile()
        self.storeConfigData()
        
    def readConfigFile(self):        
        # Open the provided file, throw an excenption if an error occurs
        try:
            file = open(self.configFilePath, 'r')
        except IOError as e:
            print(e)
            return
        except:
            print ("Unexpected error reading file", self.configFilePath)
            return
        
        for line in file:
            # Find the end of the keyword (designated by the colon)
            i = line.find(":")
            keyword = None
            
            # Retrieve the keyword
            if i>=0:
                keyword = line[:i]
                line = line[i:]
                
            # Find the beginning of the data (designated by the first open parentheses)
            openParenth = line.find("(")
            if openParenth < 0:
                openParenth = line.find("[")
            
            # Store the data collected in a dictionary
            if openParenth >= 0:
                data = line[openParenth:]
                self.configData[keyword] = eval(data)
        file.close()
    
    def storeConfigData(self):
        self.numDroplets = self.configData["Number of Droplets"]
        self.initVolume = self.configData["Droplet initial volume"]
        self.maxTravelDist = self.configData["Maximum droplet travel distance"]
        self.frameSize = self.configData["Frame size"]
        self.QRUpdateRate = self.configData["QR Code update rate (seconds)"]
        self.dropletHeight = self.configData["Default droplet height"]