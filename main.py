# ---------- References
# --- https://stackoverflow.com/questions/38153754/can-you-fit-multiple-buttons-in-one-grid-cell-in-tkinter
# --- https://bytes.com/topic/python/answers/935717-tkinter-text-widget-check-if-text-edited
# --- https://cs111.wellesley.edu/archive/cs111_fall14/public_html/labs/lab12/tkintercolor.html
# --- https://web.archive.org/web/20150321101604/http://effbot.org/tkinterbook/tkinter-events-and-bindings.htm
# ---------- Imports
# ----- Internal Libs
from os import path,system
from enum import Enum
import time
# ----- External Libs
import numpy as np
from PIL import Image
import cv2
# ----- User Generated Libs
# ---------- Initialize
cap = None
# https://docs.opencv.org/3.4/d7/df6/classcv_1_1BackgroundSubtractor.html
bg_subtractor = cv2.createBackgroundSubtractorMOG2()
CGA = Image.new('P', (1,1))
# https://en.wikipedia.org/wiki/Enhanced_Graphics_Adapter#:~:text=Many%20EGA%20cards%20have%20DIP,use%208%C3%9714%20text.
# https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124
CGAcolours = [ 
    0x00, 0x00, 0x00, # Black
    0xAA, 0x00, 0x00, # Red
    0x00, 0xAA, 0x00, # Green
    0xFF, 0xFF, 0x55, # Yellow
    0x00, 0x00, 0xAA, # Blue
    0xFF, 0x55, 0xFF, # Magenta
    0x55, 0xFF, 0xFF, # Cyan
    0xFF, 0xFF, 0xFF, # White
]
CGA.putpalette(CGAcolours)
CBAcolorsAscii = [
    "\033[30;40m \033[0m", # Black
    "\033[31;41m \033[0m", # Red
    "\033[32;42m \033[0m", # Green
    "\033[33;43m \033[0m", # Yellow
    "\033[34;44m \033[0m", # Blue
    "\033[35;45m \033[0m", # Magenta
    "\033[36;46m \033[0m", # Cyan
    "\033[37;47m \033[0m"  # White
]
# ---------- Methods
def listAllCameras():
    print("Searching for all Camera Indexes")
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(str(index)+":"+cap.getBackendName()+",")
        cap.release()
        index += 1
    print("Found Cameras at: ")
    print(arr)

def updateLoop():
    while True:
        frame = fetchFrame()
        if frame is None:
            break
        #convertPixelToAscii(frame)
        #time.sleep(.1)
        cv2.imshow("preview", frame)
        cv2.waitKey(1)

def fetchFrame():
    #print("Fetching Frame")
    ret, frame = cap.read()
    # Check if the frame was successfully captured
    if not ret:
        print("Empty Frame! Breaking!")
        return None
    result = pixelate(remap_colors(frame))
    #result = findContours(frame)
    return result

# https://stackoverflow.com/questions/73072588/how-do-i-reduce-the-color-palette-of-an-image-in-python-3
def remap_colors(frame):
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).quantize(colors=len(CGAcolours),palette=CGA,dither=Image.Dither.NONE).convert('RGB')
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# https://stackoverflow.com/questions/55508615/how-to-pixelate-image-using-opencv-in-python
def pixelate(frame):
    # Get input size
    height, width = frame.shape[:2]
    # Desired "pixelated" size
    w, h = (80, 24)
    # Resize input to "pixelated" size
    temp = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
    # Initialize output image
    return cv2.resize(temp, (width, height), interpolation=cv2.INTER_NEAREST)

# https://stackoverflow.com/questions/51705792/how-to-contour-human-body-in-an-image-using-ppencv
def findContours(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #edges = cv2.Canny(frame,150,200)
    _, thresh = cv2.threshold(frame, 127, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
    #for cnt in contours:
    #    size = cv2.contourArea(cnt)
    #    if size > 100:
    #        cv2.drawContours(frame, [cnt], -1, (255,0,0), 3)
    return frame

def removeBackground(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    fg_mask = bg_subtractor.apply(frame)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    result = cv2.bitwise_and(frame, frame, mask=fg_mask)
    return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

def convertPixelToAscii(frame):
    countOfLines = 0
    asciioutput = []
    asciioutput.append("---- TOP ----\r\n")
    countOfLines = countOfLines + 1
    height, width, channels = frame.shape
    tileOffsetH = 5
    tileOffsetW = 5
    for h in range (tileOffsetH,height,round(height/24)):
            asciioutput.append("|")
            for w in range (tileOffsetW,width,round(width/80)):
                b,g,r = (frame[h,w])
                foundMatch=False
                asciiColorIdx = 0
                for i in range (0,len(CGAcolours)-1,3):
                    if(r==CGAcolours[i] and g==CGAcolours[i+1] and b==CGAcolours[i+2]):
                        asciioutput.append(CBAcolorsAscii[asciiColorIdx])
                        foundMatch = True
                    asciiColorIdx = asciiColorIdx+1
                if(not foundMatch):
                    asciioutput.append(CBAcolorsAscii[0]) 
            asciioutput.append("|\r\n")
            countOfLines = countOfLines + 1
    asciioutput.append("---- BOT ----\r\n")
    countOfLines = countOfLines + 1
    print("\033[H", end="")
    print(''.join(asciioutput), end="")

# ---------- Main
if __name__ == '__main__':
    #
    #listAllCameras()
    # https://stackoverflow.com/questions/57733862/ansi-escape-code-wont-work-on-python-interpreter
    system('') # This fixes issues with ansi not working with certain exit codes
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error opening video stream or file")
        exit
    print("Camera detected, getting frame from: "+cap.getBackendName())
    cv2.startWindowThread()
    cv2.namedWindow("preview")
    updateLoop()