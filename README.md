# Rishaan RGB micro hackpad

RGBmicro is a 2 key macropad with a joystick, an OLED Display, and 3 led's. It has a case and uses QMK firmware
<img src="Images/RGBView.png" >

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

<img src="Images/RGBSchematic.png" >

### PCB

<img src="Images/RGBMicropadPCBTraces.png" >

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

| **Qty** | **Component** | **Note** | **Price** |
|:--:|:--:|:--:|:--:|
| 1 | Seeeduino XIAO SAMD21 | Main processor | [~$5.40](https://www.amazon.com/dp/B0B15B869W) |
| 1 | SSD1306 0.91" OLED I2C 128x32 | Displays brightness and color info | [~$6.99](https://www.amazon.com/dp/B01N0KIVUX) |
| 1 | Analog thumbstick joystick module KY-023 | Joystick control | [~$5.99](https://www.amazon.com/dp/B07V7X6LMP) |
| 1 | RGB LED 5mm common cathode | LED that is being controlled | [~$7.99 (100 pack)](https://www.amazon.com/dp/B077XGF3YR) |
| 2 | 10KΩ resistor | Pull up resistors for buttons | [~$7.99 (kit)](https://www.amazon.com/dp/B07YWNHZHS) |
| 1 | 220Ω resistor | Red LED pin | [included in kit](https://www.amazon.com/dp/B07YWNHZHS) |
| 2 | 47Ω resistor | Green and Blue LED pins | [included in kit](https://www.amazon.com/dp/B07YWNHZHS) |
| 2 | Tactile push button 6x6mm | Control modes for joystick control | [~$5.99 (pack)](https://www.amazon.com/s?k=tactile+push+button+6x6mm) |
| 1 | 2.54mm pin header 1x04 | OLED screen connector | [~$5.99 (pack)](https://www.amazon.com/s?k=2.54mm+pin+header+1x04) |
| 1 | 2.54mm pin header 1x05 | Joystick connector | [included in pack](https://www.amazon.com/s?k=2.54mm+pin+header+1x05) |

## Steps to Reproduce

### Parts
Order the parts in the Bill of Materials. These will be soldered on the PCB manually later on (unless specified in JLCPCB)

### PCB Manufacturing
1. Download `PCB/gerbers.zip`
2. Upload to JLCPCB or PCBWay
3. Place the order - remember to pick the least expensive shipping!

### Assembly
1. Solder resistors R1-R5 onto the PCB. Utilize the following resistor values
2. Table to read resistor values:
  <img src="Images/RGBView.png" >
| **R#** | **Value** |
|:--:|:--:|
| R1 | 220Ω |
| R2 | 47Ω |
| R3 | 47Ω |
| R4 | 10KΩ |
| R5 | 10KΩ |
  
3. Solder RGB LED into the D1 slot on the PCB
4. Solder tactile switches SW1 and SW2.
5. Solder 5 pin header into the slot for the Joystick
6. Solder 4 pin header into the slot for the OLED screen
7. Place XIAO SAMD21 on the top left of the board

### Firmware
1. Install CircuitPython on XIAO SAMD21
2. Copy `Firmware/main.py` to CIRCUITPY drive
3. Copy required libraries to CIRCUITPY/lib/ to run the firmware on the PCB:
   a. adafruit_ssd1306
   b. adafruit_bus_device
   c. adafruit_framebuf

### Flashing Instructions (Make sure firmware is on PCB)
1. Download CircuitPython for XIAO SAMD21 from circuitpython.org
2. Double tap reset button on XIAO — drive called XIAO-BOOT appears
3. Drag CircuitPython .uf2 file onto XIAO-BOOT drive
4. Drive reappears as CIRCUITPY
5. Copy main.py to CIRCUITPY root
6. Copy libraries to CIRCUITPY/lib/
7. The board should run automatically when it is powered

### Verify your RGB Micropad works!
1. Plug in via USB (either computer of any electricity source)
2. OLED should show RGB Micropad splash screen
3. Move joystick to change LED color or brightness (depends on the mode you are on)
4. Press SW1 to toggle between modes!
   Mode 1: Color
   Mode 2: Brightness
5. Press SW2 to cycle through preset colors for LED


## Devlog
### Session 1 — Schematic Design
The schematic was designed in Kicad. This included the following components:
1) XIAO SAMD21
2) RGB LED
3) Joystick module
4) OLED screen
5) Two tactile buttons

### Session 2 — PCB Layout
1) Layout of all components (If you are replicating, be creative and change locations of components).
2) Added GND copper pour so I don't have to route GND pins of every component
3) Routed the PCB connections between XIAO board and components
4) Created Silkscreen for astethics including Hack Club logo and component labels.

### Session 3 - Error with pullup resistors
1) Edited schematic by adding 10KΩ pullup resistors for both tacticle switches
2) Used Ohm's law to calculate resistor values for RGB LED pins
   a) Blue and Green pins recieve 47Ω resistors
   b) Red pin recieves 220Ω resistors
   c) This occurs because they have different voltage requirments in order to power the color
3) Update PCB layout to include the resistors.

### Session 4 — Firmware
1) Wrote CircuitPython firmware. This enables the PCB to have the following capabilities:
   a) Implemented color wheel for color mode control
   b) Brightness control from Joystick
   c) Mode navigation button to control both color and brightness with one Joystick
   d) Easily use joystick to change LED characteristics

### Session 5 — Case Design
Designed sandwich mount case in Fusion 360. 
1) Created bottom case with 0.4 mm clearance for PCB on all sides
2) Added 10mm thcik walls all around board and 3.2mm diameter moutning holes
3) Measured placement of components on PCB and created openings
4) Added fillets to strenthen design and make it look good


## Extra stuff

I am ready to create more complex hackpads.
