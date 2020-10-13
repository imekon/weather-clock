# weather-clock
PyPortal Weather and Clock

by Pete Goodwin (imekon)

You'll need to install the following libraries from the Adafruit libraries package

* adafruit_ntp

Also add a `tz_offset` key to your `secrets.py`, specifying your local timezone's offset from UTC in hours, like this:
```
secrets = {
  ...
  'tz_offset' : 9,  # Tokyo is UTC+9
  ...
```

## NTP

This requests the time from an NTP server and will set time and RTC silently for you, or fail. The code tries again repeatedly until it gets a time. It doesn't ask again.

## RTC

This is the real time clock and is set by NTP. It does drift, so periodically (once a day), you could get NTP to set the time again.

## OpenWeather

You will need an account with them (it's free) and an API key to put in the secrets.py file under "open_weather".

The weather details are not updated once the display is running.

## Display

I used the fonts already on the PyPortal and supplied my own background graphic "gore card.bmp", you should either use one already there or supply your own.

Once the code hits the loop at the bottom all it ever updates is the time from the RTC.
