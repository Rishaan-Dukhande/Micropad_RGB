# Rishaan RGB micro hackpad

RGBmicro is a 2 key macropad with a joystick, an OLED Display, and 3 led's. It has a case and uses QMK firmware

<img src=Images/ProjectPicture.png alt="RGBmicro" width="300"/>

It serves as rgb controller to help learn how to controller rgb colors (red, green, and blue) from values 0 to 255.

## Features:
- Portable Acrylic case with openings for connection?
- Seeeduino XIAO SAMD21 controller
- RGB LEDs for bright color display,
- 2 buttons to cycle through red, green, and blue colors, an analog joystick to control brightness
- Small OLED screen that displays the current RGB value in real time.
- 128x32 OLED Display



## PCB
Here's my PCB! It was made in KiCad. The silkscreen was imported from a Figma image.

Schematic
<img src=Images/Schematic.png alt="Schematic" width="300"/>

PCB
<img src=Images/PCB.png alt="Schematic" width="300"/>

## Sizes

- Board size: 58mm x 70mm
- 2 layer PCB
- Designed in KiCad 9.0

## Firmware

Written in CircuitPython. The main.py file controls:

- Joystick analog input → PWM brightness control
- Button 1 → cycle forward through R, G, B colors
- Button 2 → cycle backward through R, G, B colors
- OLED display → shows current R, G, B values in real time

## BOM:
Here is everything used in the RGBmicro hackpad

- 1x Seeeduino XIAO SAMD21
- 1x SSD1306 0.91" OLED I2C 128x32
- 1x Analog thumbstick joystick module
- 3x RGB LED 5mm common cathode
- 1x 100Ω resistor
- 2x 33Ω resistor
- 2x Tactile push button 6x6mm
- 1x 2.54mm pin header 1x04 --> oled screen connector
- 1x 2.54mm pin header 1x05 --> joycon connector


## Extra stuff
I am ready to create more complex hackpads.
