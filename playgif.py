import board
import gifio
import bitmaptools
import displayio
import time
from os import getenv
from pydos_ui import Pydos_ui
try:
    from pydos_ui import input
except:
    pass

try:
    type(envVars)
except:
    envVars = {}

if 'display' in dir(Pydos_ui):
    display = Pydos_ui.display
elif '_display' in envVars.keys():
    display = envVars['_display']
elif 'DISPLAY' in dir(board):
    display = board.DISPLAY
else:
    try:
        import framebufferio
        import dotclockframebuffer
    except:
        import adafruit_ili9341

    displayio.release_displays()

    if 'TFT_PINS' in dir(board):
        sWdth = getenv('PYDOS_TS_WIDTH')
        if sWdth == None:
            if board.board_id == "makerfabs_tft7":
                sWdth = input("What is the resolution Width of the touch screen? (1024/800/...): ")
            else:
                sWdth = board.TFT_TIMINGS['width']
            if 'updateTOML' in dir(Pydos_ui):
                Pydos_ui.updateTOML("PYDOS_TS_WIDTH",str(sWdth))

        if sWdth == 1024 and "TFT_TIMINGS1024" in dir(board):
            disp_bus=dotclockframebuffer.DotClockFramebuffer(**board.TFT_PINS,**board.TFT_TIMINGS1024)
        else:
            disp_bus=dotclockframebuffer.DotClockFramebuffer(**board.TFT_PINS,**board.TFT_TIMINGS)
        display=framebufferio.FramebufferDisplay(disp_bus)
    else:
        if 'SPI' in dir(board):
            spi = board.SPI()
        else:
            spi = busio.SPI(clock=board.SCK,MOSI=board.MOSI,MISO=board.MISO)
        disp_bus=displayio.FourWire(spi,command=board.D10,chip_select=board.D9, \
            reset=board.D6)
        display=adafruit_ili9341.ILI9341(disp_bus,width=320,height=240)

splash = displayio.Group()

fname = input("Enter filename:")
try:
    while Pydos_ui.virt_touched():
        pass
except:
    pass
input('Press "Enter" to continue, press "q" to quit')

odgcc = gifio.OnDiskGif(fname)
with odgcc as odg:

    if getenv('PYDOS_DISPLAYIO_COLORSPACE',"").upper() == 'BGR565_SWAPPED':
        colorspace = displayio.Colorspace.BGR565_SWAPPED
    else:
        colorspace = displayio.Colorspace.RGB565_SWAPPED

    scalefactor = display.width / odg.width
    if display.height/odg.height < scalefactor:
        scalefactor = display.height/odg.height

    if scalefactor < 1:
        print(f'scalefactor: {scalefactor}')
        bitframe = displayio.Bitmap(display.width,display.height,2**odg.bitmap.bits_per_value)
        bitmaptools.rotozoom(bitframe,odg.bitmap,scale=scalefactor)
        facecc = displayio.TileGrid(bitframe, \
            pixel_shader=displayio.ColorConverter(input_colorspace=colorspace))
    else:
        facecc = displayio.TileGrid(odg.bitmap, \
            pixel_shader=displayio.ColorConverter(input_colorspace=colorspace))

    splash.append(facecc)

    display.root_group = splash

    start = 0
    next_delay = -1
    cmnd = ""
    # Display repeatedly.
    while cmnd.upper() != "Q":

        if Pydos_ui.serial_bytes_available():
            cmnd = Pydos_ui.read_keyboard(1)
            print(cmnd, end="", sep="")
            if cmnd in "qQ":
                break
        while time.monotonic() > start and next_delay > time.monotonic()-start:
            pass
        next_delay = odg.next_frame()
        start = time.monotonic()
        if next_delay > 0:
            if scalefactor < 1:
                bitmaptools.rotozoom(bitframe,odg.bitmap,scale=scalefactor)

splash.pop()
odgcc = None
facecc.bitmap.deinit()
facecc = None
if scalefactor < 1:
    bitframe.deinit()
    bitframe = None
display.root_group = displayio.CIRCUITPYTHON_TERMINAL
