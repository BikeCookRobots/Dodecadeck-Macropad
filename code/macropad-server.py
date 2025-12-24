import serial
import time
from openrgb import OpenRGBClient

# for open rgb integration run the following
# pip3 install openrgb-python

# change the COM port to match your board
device = serial.Serial(port='COM7',baudrate=115200)
last_update = time.time()

def serial_write(serial_port, msg):
    try:
        if serial_port:
            serial_port.write(msg.encode('utf-8'))
            print("[server - INFO] wrote a message")
        else:
            print("[server - ERROR] Missing port")
    except:
        print("[server - ERROR] Port write fail")

class openRGBHandler():
    def __init__(self):
        try:
            self.openrgb_cli = OpenRGBClient()
            print("[server - INFO] openRGB profiles:")
            for p in self.openrgb_cli.profiles:
                print(p)
            self.openrgb_toggle = 0
        except:
            print("[server - WARN] failed to start openRGB client")
        self.mode= 0
    def toggle_openRGB(self):
        if self.openrgb_toggle == 0:
            self.openrgb_cli.clear()
            self.openrgb_toggle = 1
        else:
            self.openrgb_cli.load_profile(0)
            self.openrgb_toggle = 0

def get_appx_time():
    now = time.localtime()
    hr = now.tm_hour
    mn = now.tm_min

    if mn > 57: hr = hr +1
    mn_rnd = round(mn/5) * 5
    if hr == 24: hr =0
    if mn_rnd == 60: mn_rnd =0
    rnd_time = str(hr) + ":" + str(mn_rnd).zfill(2)
    return rnd_time

def send_message(data):
    serial_write(device,f"m{data}\r\n")
    # while we are sending data, might as well update the clock
    time.sleep(0.3)
    send_time()

def send_time(): 
    time_string = get_appx_time()
    serial_write(device,f"t{time_string}ish\r\n")

def send_refresh_request(): 
    serial_write(device,f"r\r\n")

def send_image_request(img_index): 
    # allows you to queue up a particular image
    serial_write(device,f"s{img_index}\r\n")

print('[server - INFO] starting main loop')
send_time()
send_message(" ")
time.sleep(0.3)
send_image_request(2)
time.sleep(0.3)
send_refresh_request()
last_update = time.time()
orgb_client = openRGBHandler()

# TODO add error handling if the server cannot connect to the device
while True:
    if time.time() - last_update > 300:
        # no matter what send the updated time every 5 minutes
        send_time()
        time.sleep(0.3)
        send_refresh_request()
        last_update = time.time()
    if(device.in_waiting > 1):
        response = device.readline().decode()
        response = response.rstrip()
        match response:
            case "cmd00":
                # print("command 00 heard, doing something")
                send_message("something important") 
                last_update = time.time()
                send_refresh_request()
            case "cmd01":
                # print("command 01 heard, doing something else")
                orgb_client.toggle_openRGB()
