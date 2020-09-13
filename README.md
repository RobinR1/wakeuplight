# Particle.io and WS2811 wake-up light

Here's a few things that may help you build a wake-up light with a Particle.io Photon and a string of WS2811 ("NeoPixel") RGB LEDs.

<a href="http://www.youtube.com/watch?v=mR70EShMsQE" target="_blank">![The wake-up light on my bed](http://img.youtube.com/vi/mR70EShMsQE/0.jpg)]</a>

## Hardware

For my wake-up light, I have connected 21 WS2811 LEDs to pin D6 of a Particle Photon. The Particle and power leads of the LED string feed off a 5V power adapter. 

I usually power my LED creations with WS2811 LED "strings" (instead of strips). These are water proof (not really needed in the bedroom) and can be seperated by about 7cm, which is good to hang 21 LEDs over the width of our bed. I have used some mighty duct tape magic to hang the contraption from my bed frame.

## Software

### Particle.io code

The code that runs on the Particle is in `wakeuplight.ino`. It has two example functions:

* Start a 30 minute light sequence, simulating dawn and sunrise, with function `wakeup`
* Set the LEDs to a specified color, with function `rgbColor` which accepts values of the format `123,123,123` denoting R, G, B bytes.

If you want to run this from the Particle Build IDE, copy this code into a new project and add the "NEOPIXEL" library.
 
### An example cronjob

You can start the wake-up light from a cronjob, e.g., at 7 each morning

```
0 7 * * 1,2,3,4,5 curl https://api.particle.io/v1/devices/MYDEVICEID/wakeup -d access_token=MYACCESSTOKEN -d "args=blah"
```

### An example HTML/JS color controller

You can control the wake-up light's color from a native color picker using the JavaScript in the included `index.html`. Make sure to set your device ID and access token in the HTML file.

### Python Webservice

The wakeuplight webservice is a small webservice written in Python 3 listening on port 5002 to manage the wakeuplight cronjobs using a local `/etc/cron.d/wakelight` cron-file and to control the wakeuplight directly. 
Currently schedules only support a call to the `wakeup`-function, and to turn the light OFF. Direct control of the light only supports setting an RGB value.

Following methods are currently supported:
#### GET /schedules
Returns a JSON array containing all currently defined cronjobs using following format:
```
{
  "<id>": {
    "day": "<1-31> or *", 
    "month": "<1-12> or *", 
    "dow": "<0-7> or *", 
    "enabled": true/false, 
    "ontime": {
      "hour": "<0-23> or *", 
      "minute": "<0-59> or *"
    }, 
    "offtime": {
      "hour": "<0-23> or *", 
      "minute": "<0-59> or *"
    }
  }, 
  ...
}
```
where
 * `<id>` is an auto-generated ID of the schedule
 * `day` is a cron-formatted definition of the days to activate the schedule on
 * `month` is a cron-formatted definition of the months to activate the schedule on
 * `dow` is a cron-formatted definition of the days of the week to activate this schedule on
 * `enabled`defines if the schedule is enabled (`true`) or disabled ('false`)
 * `ontime` defines the time to schedule the wakeuplight to turn on
  * `hour` is a cron-formatted definition of the hour to turn the wakeuplight on
  * `minute` is a cron-formatted definition of the minute to turn the wakeuplight on
 * `offtime` (optional) defines the time to schedule the wakeuplight to turn off (is absent when there is no off-time defined for this schedule)
  * `hour` is a cron-formatted definition of the hour to turn the wakeuplight off
  * `minute` is a cron-formatted definition of the minute to turn the wakeuplight off

#### PUT /addschedule
Adds a new schedule to the local cronjob file `/etc/cron.d/wakelight` and expects a JSON body in following format:
```
{
  "onhour": "<0-23>"
  "onminute": "<0-59>
  "offhour": "<0-23>"
  "offminute": "<0-59>"
  "day": "<1-31>"
  "month": "<1-12>"
  "dow": "<0-7>"
  "enabled": true/false
}
```
where:
* `onhour` (cron-formatted string) is the hour to turn the wakeuplight ON. Note that the companion app only supports a single hour in range 0-23.
* `onminute`(cron-formatted string) is the minute to turn the wakeuplight ON. Note that the companion app only supports a single minute in range 0-59.
* `offhour` (cron-formatted string) (optional) is the hour to turn the wakeuplight OFF (can be omitted if the light should not be turned off by this schedule).
* `offminute` (cron-formatted string) (optional, but required if `offhour` is defined) is the minute to turn the wakeuplight OFF.
* `day` (cron-formatted string) days of the month to activate this schedule. Note that the companion app only supports `*`.
* `month` (cron-formatted string) months of the year to activate this schedule. Note that the companion app only support `*`.
* `dow` (cron-formatted string) days of the week to activate this schedule.

#### PUT /editschedule/`<id>`
Changes the existing schedule with ID:`<id>` and expect a JSON body identical to the `/addschedule`-method
  
#### DELETE /editschedule/`<id>`
Delete the existing schedule with ID:`<id>`.
Warning: schedules with an ID higher than the one of the schedule being deleted will shift down a place. Hence the next scheduled schedule will now get the ID of the schedule you just deleted.
  
#### PUT /editschedulestate/`<id>`
Enables or disables the existing schedule with ID:`<id>` and expects a JSON body in following format:
```
{
  "enabled": true/false
}
```
where:
* `enabled` (boolean) defines wether to enable (`true`) or disable (`false`) the schedule

#### PUT /setRGB
Sets the current RGB values of the wakeuplight. In other words, turn on the light now with a desired RGB value or turn it off (RGB: 0,0,0). It expects a JSON body in following format:
```
{
  "rgb":"<r>,<g>,<b>"
}
```
where:
* `rgb` (string) is the rgb value to set the light to in format `0-255,0-255,0-255` respectively representing the desired red, green and blue values.

### Android Companion
This is an Android 9 or higher app created on the [Kodular](https://www.kodular.io/) platform to easily schedule and control the wakelight using the Python Webservice from your android device. (Currently only tested on a smartphone, but should be usable on an Android tablet too)
The app requires direct access to the server running the webservice, so if you need it to work outside of your internal wifi network, you will have to expose the webservice to the internet, which I **strongly** do not recommend as the webservice currently has no form of authentication or security built in. 

When the app is first run, it will require you to enter the URL to the webservice. After that, it will open on the Schedule view, where you can add, edit or delete schedules. You can switch to the Actions view by swiping right or pressing the Action-tab to choose and RGB value by using 3 sliders for Red, Green and Blue and then pressing the ON button. To turn the light off, press the OFF button which will issue RGB 0,0,0 to the light.

#### Build
To build this app, you need to 
 * zip the contents of the wakeuplight_companion-directory into a zipfile named `wakeup_light_companion.aia`. 
 * Import it into [Kodular Creator](https://creator.kodular.io)
 * Export > Android APK
