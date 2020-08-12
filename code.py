import board
import busio
import time
import json

from digitalio import DigitalInOut
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_requests as requests

from rtc import RTC
from adafruit_ntp import NTP

import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

requests.set_socket(socket, esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")

print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])

print("Connecting to AP...")
# This copes with two AP's, trying each in turn
choice = 0
while not esp.is_connected:
    try:
        if choice == 0:
            esp.connect_AP(secrets["ssid"], secrets["password"])
        elif choice == 1:
            esp.connect_AP(secrets["ssid2"], secrets["password2"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        choice += 1
        if choice >= 2:
            choice = 0
        continue

print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

# Get NTP time, may make several attempts
ntp = NTP(esp)
ntp.set_time()
while not ntp.valid_time:
    print("time not valid...")
    time.sleep(5)
    ntp.set_time(60 * 60)

# Get the RTC time, not NTP updates RTC silently
rtc = RTC()
print("{:02}/{:02}/{:04} {:02}:{:02}".format(
    rtc.datetime.tm_mday, rtc.datetime.tm_mon, rtc.datetime.tm_year,
    rtc.datetime.tm_hour, rtc.datetime.tm_min
))

# Use the OpenWeather API
# london,gb is the location and can be changed appropriately
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather?q=london,gb&units=metric&appid=" + secrets["open_weather"]

def update_weather():
    print("updating weather...")
    response = requests.get(WEATHER_URL)
    weather = json.loads(response.text)
    weather_main = weather['main']
    temp = weather_main['temp']
    pressure = weather_main['pressure']
    humidity = weather_main['humidity']
    desc = weather['weather'][0]['description']
    response.close()
    return (temp, pressure, humidity, desc)

(temp, pressure, humidity, desc) = update_weather()

# Fonts should already be on your PyPortal for the original software installed
font = bitmap_font.load_font("fonts/Arial-16.bdf")
big_font = bitmap_font.load_font("fonts/Arial-Bold-24.bdf")

vert_spacing = 30

background_bitmap = "/gore card.bmp"

if board.DISPLAY.width == 480:
    background_bitmap = "/gore card titano.bmp"

# gore card.bmp should be replaced with a suitable 320x240 bitmap
with open(background_bitmap, "rb") as bitmap_file:
    bitmap = displayio.OnDiskBitmap(bitmap_file)
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=displayio.ColorConverter())

    time_area = label.Label(big_font, text = "{:02}:{:02}:{:02}".format(
        # rtc.datetime.tm_mday, rtc.datetime.tm_mon, rtc.datetime.tm_year,
        rtc.datetime.tm_hour, rtc.datetime.tm_min, rtc.datetime.tm_sec), color=0xff00ff, max_glyphs = 30)
    time_area.x = 10
    time_area.y = 15

    date_area = label.Label(font, text = "{:02}/{:02}/{:04}".format(
        rtc.datetime.tm_mday, rtc.datetime.tm_mon, rtc.datetime.tm_year), max_glyphs = 30)
    date_area.x = 10
    date_area.y = 50

    temp_area = label.Label(font, text = "temp: {}C".format(temp), max_glyphs = 30)
    temp_area.x = 10
    temp_area.y = 50 + vert_spacing

    pressure_area = label.Label(font, text = "pressure: {}".format(pressure), max_glyphs = 30)
    pressure_area.x = 10
    pressure_area.y = 50 + vert_spacing * 2

    humidity_area = label.Label(font, text = "humidity: {}%".format(humidity), max_glyphs = 30)
    humidity_area.x = 10
    humidity_area.y = 50 + vert_spacing * 3

    desc_area = label.Label(font, text = desc, max_glyphs = 30)
    desc_area.x = 10
    desc_area.y = 50 + vert_spacing * 4

    text_group = displayio.Group(max_size = 7)
    text_group.append(tile_grid)
    text_group.append(time_area)
    text_group.append(date_area)
    text_group.append(temp_area)
    text_group.append(pressure_area)
    text_group.append(humidity_area)
    text_group.append(desc_area)

    board.DISPLAY.show(text_group)

    counter = 0
    while True:
        time_area.text = "{:02}:{:02}:{:02}".format(
            # rtc.datetime.tm_mday, rtc.datetime.tm_mon, rtc.datetime.tm_year,
            rtc.datetime.tm_hour, rtc.datetime.tm_min, rtc.datetime.tm_sec)
        time.sleep(1)
        counter += 1
        if counter > 60 * 60:
            (temp, pressure, humidity, desc) = update_weather()
            temp_area.text = "temp: {}C".format(temp)
            pressure_area.text = "pressure: {}".format(pressure)
            humidity_area.text = "humidity: {}%".format(humidity)
            desc_area.text = desc
            counter = 0
