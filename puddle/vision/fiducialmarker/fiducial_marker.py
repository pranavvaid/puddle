import cv2

class FiducialMarker:
    def __init__(self, contours = None):
        self.contours = contours
        
    def __repr__(self):
        return '<center = {}>'.format(self.center)
    
    @property
    def center(self):
        if self.contours is None:
            return None
        # Calculate the center of the contour using moments (as the contour is irregularly shaped)
        M = cv2.moments(self.contours)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        return center
    
    # Draw the contours of the marker to the img
    def draw_contour(self, img, color = (0,255,0), linewidth = 1):
        cv2.drawContours(img, [self.contours], -1, color, linewidth)