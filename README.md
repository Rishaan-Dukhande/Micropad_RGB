# Rishaan RGB micro hackpad

RGBmicro is a 2 key macropad with a joystick, an OLED Display, and 3 led's. It has a case and uses QMK firmware

![RGBmicro 3D View](path/to/your/image.png)
<img src="RGBView.png" width="450" height="500">

## Features:

* Portable Acrylic case with openings for connection?
* Seeeduino XIAO SAMD21 controller
* RGB LED's for bright color display,
* 2 buttons to cycle through red, green, and blue colors, an analog joystick to control brightness
* Small OLED screen that displays the current RGB value in real time.

## How it works

The RGB micro serves as an rgb controller. It can switch between the red, green, and blue pins that make an RGB color. The joystick allows a change of brightness for the selected LED. The range of these values is 0-255, the same as the range for each color in LED's. The OLED screen shows the rgb values of each color so that the user of the RGB micro knows what color they have generated.

## PCB

Here's my PCB! Kicad was used to create both the schematic and layout of the pcb.

### Schematic

![Schematic](path/to/your/schematic.png)

### PCB

![PCB](path/to/your/pcb.png)

The 1x4 connector on the top is for connecting the Oled Screen (SSD1306 0.91" OLED I2C 128x32) The 1x5 connector on the bottom center of the pcb is for connecting a joystick. brightness control.

## Sizes

* Board size: 58mm x 70mm
* 2 layer PCB
* Designed in KiCad 9.0

## Firmware

Written in CircuitPython. The main.py file controls:

* Joystick analog input -> PWM brightness control
* Button 1 -> cycle forward through R, G, B colors
* Button 2 -> cycle backward through R, G, B colors
* OLED display -> shows current R, G, B values in real time

## BOM:

Here is everything used in the RGBmicro hackpad

| **Qty** | **Component** | **Note** | 
|:--:|:--:|:--:|
| 1 | Seeeduino XIAO SAMD21 | Main processor |
| 1 | SSD1306 0.91" OLED I2C 128x32 | Displays brightness and color info |
| 1 | Analog thumbstick joystick module | Joystick control |
| 1 | RGB LED 5mm common cathode | LED that is being controlled |
| 2 | 10KΩ resistor | pull up resistors for buttons |
| 1 | 220Ω resistor | Red LED pin |
| 2 | 47Ω resistor | Green and Blue LED pins |
| 2 | Tactile push button 6x6mm | control modes for joystick control |
| 1 | 2.54mm pin header 1x04 | OLED screen connector |
| 1 | 2.54mm pin header 1x05 | Joystick connector |

## Extra stuff

I am ready to create more complex hackpads.
