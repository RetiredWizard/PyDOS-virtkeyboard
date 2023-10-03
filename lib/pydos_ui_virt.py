import board
import displayio
import dotclockframebuffer
import framebufferio
import adafruit_imageload
import terminalio
from adafruit_display_text import bitmap_label as label

import busio
import adafruit_focaltouch
import time

from sys import stdin,stdout,implementation
from supervisor import runtime

class PyDOS_UI:
    
    def __init__(self):
        # Setup Touch detection
        SCL_pin = board.IO41  # set to a pin that you want to use for SCL
        SDA_pin = board.IO42  # set to a pin that you want to use for SDA
        IRQ_pin = board.IO40  # select a pin to connect to the display's interrupt pin ("IRQ") - not used in this code

        self.i2c = busio.I2C(SCL_pin, SDA_pin)
        self.ft = adafruit_focaltouch.Adafruit_FocalTouch(self.i2c, debug=False)
        self.touches = []
        
        self.SHIFTED = False
        self.CAPLOCK = False

        displayio.release_displays()

        keyboard_bitmap,keyboard_palette = adafruit_imageload.load("/lib/keyboard.bmp",bitmap=displayio.Bitmap,palette=displayio.Palette)
        htile=displayio.TileGrid(keyboard_bitmap,pixel_shader=keyboard_palette)
        htile.x=15
        htile.y=220
        self._kbd_group = displayio.Group()
        self._kbd_group.append(htile)

        fb=dotclockframebuffer.DotClockFramebuffer(**board.TFT,**board.TIMINGS800)
        self._display=framebufferio.FramebufferDisplay(fb)

        self._touched = False

    def serial_bytes_available(self):
        self._touched = False
        if self.virt_touched():
            retval = 1
            self._touched = True
        else:        
            # Does the same function as supervisor.runtime.serial_bytes_available
            retval = runtime.serial_bytes_available

        return retval


    def uart_bytes_available(self):
        # Does the same function as supervisor.runtime.serial_bytes_available
        retval = runtime.serial_bytes_available

        return retval


    def read_keyboard(self,num):
        if self.virt_touched() or self._touched:
            if self.touches[0]['x'] > 740 and self.touches[0]['y'] < 75:
                retVal = '\n'
            else:
                retVal = self.read_virtKeyboard(num)
                if retVal == "":
                    retVal = '\n'
        else:
            retVal = stdin.read(num)

        return retVal
    
    def get_screensize(self):
        return (19,65)

    def _identifyLocation(self,xloc,yloc):
        row1Keys = [600,555,510,465,420,375,330,285,240,195,150,105,60,0]
        row1Letters = ['\x08','=','-','0','9','8','7','6','5','4','3','2','1','`']
        row1Uppers = ['\x08','+','_',')','(','*','&','^','%','$','#','@','!','~']
        row2Keys = [615,570,525,485,440,395,350,305,260,215,175,130,80,0]
        row2Letters = ['\\',']','[','p','o','i','u','y','t','r','e','w','q','\x09']
        row2Uppers = ['|','}','{']
        row3Keys = [590,545,500,455,410,365,320,275,230,185,140,95,0]
        row3Letters = ['\n',"'",';','l','k','j','h','g','f','d','s',"a",'C']
        row3Uppers = ['\n','"',':']
        row4Keys = [565,520,475,430,385,340,295,250,205,160,115,0]
        row4Letters = ['S','/','.',',','m','n','b','v','c','x','z','S']
        row4Uppers = ['S','?','>','<']
        row5Keys = [640,460,200,110,0]
        row5Letters = ['X','',' ','','\x1b']

        if yloc < 231:
            retKey = ""
        elif yloc > 413:                 # 435
            #print(row5Letters[next(a[0] for a in enumerate(row5Keys) if a[1]<xloc)])
            retKey = row5Letters[next(a[0] for a in enumerate(row5Keys) if a[1]<=xloc)]
        elif yloc >= 368:                # 390
            #print(row4Letters[next(a[0] for a in enumerate(row4Keys) if a[1]<xloc)])
            retKey = row4Letters[next(a[0] for a in enumerate(row4Keys) if a[1]<=xloc)]
        elif yloc >= 323:                # 345
            #print(row3Letters[next(a[0] for a in enumerate(row3Keys) if a[1]<xloc)])
            retKey = row3Letters[next(a[0] for a in enumerate(row3Keys) if a[1]<=xloc)]
        elif yloc >= 277:                # 300
            #print(row2Letters[next(a[0] for a in enumerate(row2Keys) if a[1]<xloc)])
            retKey = row2Letters[next(a[0] for a in enumerate(row2Keys) if a[1]<=xloc)]
        else:                            # 255
            #print(row1Letters[next(a[0] for a in enumerate(row1Keys) if a[1]<xloc)])
            retKey = row1Letters[next(a[0] for a in enumerate(row1Keys) if a[1]<=xloc)]

        if retKey == 'S':
            if not self.SHIFTED:
                self.SHIFTED = True
            elif not self.CAPLOCK:
                self.SHIFTED = False
            retKey = ''
        elif retKey == 'C':
            self.CAPLOCK = not self.CAPLOCK
            self.SHIFTED = self.CAPLOCK
            retKey = ''
        elif retKey == 'X':
            retKey = '\x00'


        if self.CAPLOCK:
            self.SHIFTED = True
        
        if len(retKey) != 0 and self.SHIFTED:
            self.SHIFTED = self.CAPLOCK
                
            if retKey.upper() != retKey:
                retKey = retKey.upper()
            else:
                if retKey in row1Letters:
                    retKey = row1Uppers[row1Letters.index(retKey)]
                elif retKey in row2Letters[0:3]:
                    retKey = row2Uppers[row2Letters.index(retKey)]
                elif retKey in row3Letters[0:3]:
                    retKey = row3Uppers[row3Letters.index(retKey)]
                elif retKey in row4Letters[0:4]:
                    retKey = row4Uppers[row4Letters.index(retKey)]

        return retKey
    
    def virt_touched(self):
        if self.ft.touched:
            self.touches = self.ft.touches
            if self.touches != []:
                return True

        self.touches = []
        return False

    def read_virtKeyboard(self,num=0):
        #self._display.show(None)
        #self._display.refresh()
        self._display.show(self._kbd_group)

        font = terminalio.FONT
        color = 0xFFFFFF
        keyString = ""
        keyedTxt = label.Label(font, text=keyString, color=color)
        keyedTxt.x = 15
        keyedTxt.y = 200
        keyedTxt.scale = 2
        self._kbd_group.append(keyedTxt)
        
        shftIndicator = label.Label(font,text="",color=0x00FF00)
        shftIndicator.x = 15
        shftIndicator.y = 15
        shftIndicator.scale = 2
        self._kbd_group.append(shftIndicator)
        capsIndicator = label.Label(font,text="",color=0x00FF00)
        capsIndicator.x = 90
        capsIndicator.y = 15
        capsIndicator.scale = 2
        self._kbd_group.append(capsIndicator)

        while self.virt_touched():
            pass

        self.SHIFTED = self.CAPLOCK
        shftIndicator.text = ('SHIFT' if self.SHIFTED else '')
        capsIndicator.text = ('LOCK' if self.CAPLOCK else '')

        keysPressed = 0
        while True:
            if self.virt_touched():
                point = self.touches[0]
                pressedKey = self._identifyLocation(point["x"],point["y"])
                
                if pressedKey == '\x08':
                    keyString = keyString[:-1]
                    keyedTxt.text = keyString
                    pressedKey = ''
                elif pressedKey == '\n':
                    break
                elif pressedKey == '\x00':
                    keyString = ""
                    break
                keyString += pressedKey
                    
                shftIndicator.text = ('SHIFT' if self.SHIFTED else '')
                capsIndicator.text = ('LOCK' if self.CAPLOCK else '')
                if len(pressedKey) != 0:
                    keyedTxt.text = keyString.replace('\x1b',"E")
                    keysPressed += 1
                    if num > 0 and keysPressed >= num:
                        break
                    
                while self.virt_touched():
                    pass

            time.sleep(0.0001)

#        display.root_group = displayio.CIRCUITPYTHON_TERMINAL
        while len(self._kbd_group) > 1:
            self._kbd_group.pop()
        self._display.show(None)
        return keyString

Pydos_ui = PyDOS_UI()

def input(disp_text=None):

    if disp_text != None:
        print(disp_text,end="")
        
    keys = ''
    while True:
        if Pydos_ui.uart_bytes_available():
            done = False
            while Pydos_ui.uart_bytes_available():
                keys += stdin.read(1)
                if keys[-1] != '\x08':
                    print(keys[-1],end="")
                else:
                    if len(keys) > 1:
                        print('\x08 \x08',end="")
                    keys = keys[:-2]

                if keys[-1:] == '\n':
                    keys = keys[:-1]
                    done = True
                    break
            if done:
                break
        elif Pydos_ui.virt_touched():
            if Pydos_ui.touches[0]['x'] > 740 and Pydos_ui.touches[0]['y'] < 75:
                keys = ''
            else:
                keys = Pydos_ui.read_virtKeyboard()
            print(keys)
            while Pydos_ui.virt_touched():
                pass
            break
        
    return keys
