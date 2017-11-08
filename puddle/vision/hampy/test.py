import cv2

from hampy import detect_markers

img = cv2.imread('Picture1.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
markers = detect_markers(img)

for m in markers:
    print ('Found marker {} at {}') #, format(m.id, m.center))
    m.draw_contour(img)
    
#imshow(img)
cv2.imshow('test',img)

cv2.waitKey(0)
