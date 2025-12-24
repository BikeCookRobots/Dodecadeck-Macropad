import usb_cdc
import time
import board
import digitalio
import usb_hid
import busio
import displayio
from fourwire import FourWire
from adafruit_display_text import label
import terminalio
import adafruit_ssd1683
import neopixel

# release any currently configured displays
displayio.release_displays()

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS 

class KeyboardHandler():
    def __init__(self):
        try:
            self.kbd = Keyboard(usb_hid.devices)
            print("keyboard initialized")
            self.layout = KeyboardLayoutUS(self.kbd)
        except:
            print("error in initiate keyboard")
        self.mode= 0

    def send_key(self,*args):
        print(args)
        if self.mode ==0:
            self.kbd.send(*args)
            time.sleep(0.2)
class ScreenHandler():
    def __init__(self):
        #inital screen setup
        print("initializing ScreenHandler")
        spi = busio.SPI(board.EPD_SCK, MOSI=board.EPD_MOSI, MISO=None)
        epd_cs = board.EPD_CS
        epd_dc = board.EPD_DC
        epd_reset = board.EPD_RESET
        epd_busy = board.EPD_BUSY
        display_bus = FourWire(spi, command=epd_dc, chip_select=epd_cs, reset=epd_reset, baudrate=1000000)
        time.sleep(1)
        
        self.display = adafruit_ssd1683.SSD1683(display_bus, width=400, height=300, busy_pin=epd_busy)
        self.display.rotation = 90
        rot = str(self.display.rotation)
        print(f"rotation: {rot}")
        text = " " *20
        font = terminalio.FONT
        font_color = 0xFFFFFF
        bg_color = 0x000000

        # Create the text label
        self.text_area = label.Label(font, text=text, color=font_color,background_color=bg_color,scale = 2)
        self.text_area.x = 10
        self.text_area.y = 15
        self.update_text(" ") 
        self.clock_area = label.Label(font, text="00:00ish", color = font_color, background_color=bg_color, scale = 2)
        self.clock_area.x = 200
        self.clock_area.y = 15

        self.num_images = 5
        self.loaded_image = 0
        # start by loading every image we intend to show
        self.pic0 = displayio.OnDiskBitmap("screen00.bmp")
        self.pic1 = displayio.OnDiskBitmap("screen01.bmp")
        self.pic2 = displayio.OnDiskBitmap("screen02.bmp")
        self.pic3 = displayio.OnDiskBitmap("screen03.bmp")
        self.pic4 = displayio.OnDiskBitmap("screen04.bmp")

        # display the first image
        self.image_group = displayio.Group()
        t= displayio.TileGrid(self.pic0, pixel_shader=self.pic0.pixel_shader,y=20)
        self.image_group.append(t)

        # text bg
        bitmap= displayio.Bitmap(self.display.width, 30, 2)
        # Create a two color palette
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0xffffff

        # Create a TileGrid using the Bitmap and Palette
        text_bg = displayio.TileGrid(bitmap, pixel_shader=palette,x=0,y=0)
        for x in range(0,299):
            for y in range(0,30):
                bitmap[x,y] = 0

        # add that to the display and refresh
        self.root = displayio.Group()
        self.root.append(self.image_group)
        self.root.append(text_bg)
        self.root.append(self.text_area)
        self.root.append(self.clock_area)
        self.display.root_group = self.root

        self.display.refresh()
        self.last_update = time.time()
        self.MIN_REFRESH_TIME = self.display.time_to_refresh + 10
        print("refresh time: ")
        print(self.MIN_REFRESH_TIME)
        self.display_ready = False
        self.update_queued = False

    def show_image(self,imgIndex):
        imgIndex = int(imgIndex)
        if imgIndex==0:
            self.image_group.pop()
            t = displayio.TileGrid(self.pic0, pixel_shader=self.pic0.pixel_shader)
        if imgIndex==1:
            self.image_group.pop()
            t = displayio.TileGrid(self.pic1, pixel_shader=self.pic1.pixel_shader)
        if imgIndex==2:
            self.image_group.pop()
            t = displayio.TileGrid(self.pic2, pixel_shader=self.pic2.pixel_shader)
        if imgIndex==3:
            self.image_group.pop()
            t = displayio.TileGrid(self.pic3, pixel_shader=self.pic3.pixel_shader)
        if imgIndex==4:
            self.image_group.pop()
            t = displayio.TileGrid(self.pic4, pixel_shader=self.pic4.pixel_shader)
        print(f"image {imgIndex} queued")
        self.loaded_image = imgIndex
        self.update_queued = True
        self.image_group.append(t)

    def cycle_image(self):
        inc = self.loaded_image + 1
        mod = inc % self.num_images  # this will allow us to automatically cycle between all the images we have
        self.show_image(mod)
    
    def get_display_ready(self):
        return self.display_ready
    
    def get_update_queued(self):
        return self.update_queued
    
    def update_image(self):
        if (self.update_queued == True) and (self.display_ready == True):
            print("updating image")
            self.last_update = time.time()
            self.update_queued = False
            self.display_ready = False
            self.display.refresh()
            time.sleep(5)
            print("successfully updated")
    def update_text(self,text):
        self.text_area.text = text
    def update_time(self,text):
        self.clock_area.text = text
    def request_refresh(self):
        print("refresh requested")
        self.update_queued = True
    def check_refresh_ready(self):
        # this method must be called every so often (every loop is fine) to check if we are ready to refresh. This is to set the display_ready variable to true
        now =time.time()
        if ((now - self.last_update) > int(self.MIN_REFRESH_TIME)) and (self.display_ready == False):
            self.display_ready = True
            print("ready to refresh")
            return True
        return False
class StatusLED():
    def __init__(self):
        pixel_pin = board.NEOPIXEL
        self.light = neopixel.NeoPixel(pixel_pin,1, brightness = 0.3)
    def show_red(self):
        self.light[0]=(255,0,0)
    def show_yellow(self):
        self.light[0]=(75,30,0)
    def show_green(self):
        self.light[0]=(0,255,0)
    def clear(self):
        self.light[0]=(0,0,0)
class SerialCom():
    def __init__(self):
        self.serial = usb_cdc.data
        self.command = 0
        self.rec_data =0
    def check_data(self):  
       if self.serial.in_waiting > 0:
           byte = self.serial.readline()
           time.sleep(0.5)
           try:
               self.command = byte.decode("utf-8")
               cmd_str = str(self.command)
               print("received command: ")
               print(cmd_str)
               if cmd_str[0]== "t":
                    self.apx_time = cmd_str[1:]
                    return 1 
               if cmd_str[0]== "m":
                    if len(cmd_str) > 12:
                        self.msg = cmd_str[1:13] + "..."
                    else:
                        self.msg = cmd_str[1:13]
                    return 2 
               if cmd_str[0]== "r":
                    # manual refresh
                    return 3 
               if cmd_str[0]== "s":
                    # set image to a number
                    self.rec_data = cmd_str[1]
                    return 4 
           except:
               print("failed to convert")
               return False
    def send_data(self,cmd):
        message = cmd+"\r\n"
        self.serial.write(message)
def main():
    print("Starting...")
    screen_handler = ScreenHandler()
    serial = SerialCom()
    keeb = KeyboardHandler()
    status_led = StatusLED()
    status_led.show_green()
    time.sleep(4)
    status_led.clear()

    # onboard LED
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT

    reading_light = digitalio.DigitalInOut(board.A0)
    reading_light.direction = digitalio.Direction.OUTPUT

    # tactile switches
    button01 =digitalio.DigitalInOut(board.MISO) 
    button02 =digitalio.DigitalInOut(board.D24) 
    button03 =digitalio.DigitalInOut(board.D12) 
    button04 =digitalio.DigitalInOut(board.D11) 

    # keyboard switches
    button05 =digitalio.DigitalInOut(board.D4) 
    button06 =digitalio.DigitalInOut(board.D1) # pin labeled TX 
    button07 =digitalio.DigitalInOut(board.D0) # pin labeled RX
    button08 =digitalio.DigitalInOut(board.MOSI) 
    button09 =digitalio.DigitalInOut(board.SCK) 
    button10 =digitalio.DigitalInOut(board.D25) 
    button11 =digitalio.DigitalInOut(board.D6) 
    button12 =digitalio.DigitalInOut(board.D9) 
    button13 =digitalio.DigitalInOut(board.D10) 
    button14 =digitalio.DigitalInOut(board.SDA) 
    button15 =digitalio.DigitalInOut(board.SCL) 
    button16 =digitalio.DigitalInOut(board.D5) 

    btn01Prev = False
    btn02Prev = False
    btn03Prev = False
    btn04Prev = False
    btn05Prev = False
    btn06Prev = False
    btn07Prev = False
    btn08Prev = False
    btn09Prev = False
    btn10Prev = False
    btn11Prev = False
    btn12Prev = False
    btn12Prev = False
    btn13Prev = False
    btn14Prev = False
    btn15Prev = False
    btn16Prev = False

    while True:
        # main loop

        if (button01.value): 
            btn01Prev = True
        if (button01.value == False and btn01Prev == True): 
            print("button 1 pressed")
            screen_handler.cycle_image()
            btn01Prev = False

        if (button02.value): 
            btn02Prev = True
        if (button02.value == False and btn02Prev == True): 
            print("button 2 pressed")
            #reading_light.value = True 
            #time.sleep(5)
            #reading_light.value = False 
            #time.sleep(5)
            btn02Prev = False

        if (button03.value): 
            btn03Prev = True
        if (button03.value == False and  btn03Prev == True): 
            print("button 3 pressed")
            #status_led.show_red()
            #time.sleep(5)
            #status_led.show_green()
            #time.sleep(5)
            #status_led.show_yellow()
            #time.sleep(5)
            #status_led.clear()
            btn03Prev= False

        if (button04.value): 
            btn04Prev = True
        if (button04.value == False and  btn04Prev == True): 
            print("button 4 pressed")
            btn04Prev= False

        if (button05.value): 
            btn05Prev = True
        if (button05.value == False and  btn05Prev == True): 
            print("button 5 pressed")
            keeb.send_key(Keycode.ALT,Keycode.F14)
            btn05Prev= False

        if (button06.value): 
            btn06Prev = True
        if (button06.value == False and  btn06Prev == True): 
            print("button 6 pressed")
            keeb.send_key(Keycode.ALT,Keycode.F13)
            btn06Prev= False

        if (button07.value): 
            btn07Prev = True
        if (button07.value == False and  btn07Prev == True): 
            print("button 7 pressed")
            keeb.send_key(Keycode.ALT,Keycode.F16)
            #serial.send_data("cmd01")
            btn07Prev= False

        if (button08.value):
            btn08Prev = True
        if (button08.value == False and btn08Prev == True): 
            print("button 8 pressed")
            keeb.send_key(Keycode.ALT,Keycode.F13)
            btn08Prev = False

        if (button09.value): 
            btn09Prev = True
        if (button09.value == False and  btn09Prev == True): 
            print("button 9 pressed")
            serial.send_data("cmd00")
            btn09Prev= False

        if (button10.value): 
            btn10Prev = True
        if (button10.value == False and  btn10Prev == True): 
            print("button 10 pressed")
            keeb.send_key(Keycode.ALT,Keycode.F15)
            btn10Prev= False

        if (button11.value): 
            btn11Prev = True
        if (button11.value == False and  btn11Prev == True): 
            print("button 11 pressed")
            btn11Prev= False

        if (button12.value): 
            btn12Prev = True
        if (button12.value == False and  btn12Prev == True): 
            print("button 12 pressed")
            btn12Prev= False

        if (button13.value): 
            btn13Prev = True
        if (button13.value == False and  btn13Prev == True): 
            print("button 13 pressed")
            serial.send_data("cmd01")
            btn13Prev= False

        if (button14.value): 
            btn14Prev = True
        if (button14.value == False and  btn14Prev == True): 
            print("button 14 pressed")
            btn14Prev= False

        if (button15.value): 
            btn15Prev = True
        if (button15.value == False and  btn15Prev == True): 
            print("button 15 pressed")
            btn15Prev= False

        if (button16.value): 
            btn16Prev = True
        if (button16.value == False and  btn16Prev == True): 
            print("button 16 pressed")
            btn16Prev= False

        screen_handler.check_refresh_ready()

        rr = screen_handler.get_display_ready()
        if not rr:
            status_led.show_yellow()
        else:
            status_led.clear()
        screen_handler.update_image()

        # check if we have a command from the server. includes upates to the title bar message, updates for the clock, and a command to refresh the screen
        serial_cmd = serial.check_data()
        if serial_cmd == 1:
            screen_handler.update_time(serial.apx_time)
        if serial_cmd == 2:
            screen_handler.update_text(serial.msg)
        if serial_cmd == 3:
            screen_handler.request_refresh()
        if serial_cmd == 4:
            screen_handler.show_image(serial.rec_data)
main()