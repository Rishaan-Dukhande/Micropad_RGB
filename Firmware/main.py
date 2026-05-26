# ─────────────────────────────────────────────────────────────────────────────
# RGB Micropad Firmware
# Author:      Rishaan Dukhande
# Description: Controls an RGB LED via joystick and buttons
#
# CONTROLS:
#   SW1 (D0)        → Toggle between COLOR mode and BRIGHTNESS mode
#   SW2 (D1)        → Cycle through color presets
#   Joystick SW     → Toggle saturation mode on/off
#   Joystick X/Y    → COLOR mode:      navigate color wheel (hue)
#                     BRIGHTNESS mode: Y axis controls brightness
#                     SAT mode:        Y axis controls saturation
#
# OLED DISPLAY:
#   Line 1 → Current mode name
#   Line 2 → Current color name
#   Line 3 → RGB values + brightness % (or saturation % in sat mode)
#
# REQUIRED LIBRARIES (copy to CIRCUITPY/lib/ folder on your XIAO):
#   - adafruit_ssd1306
#   - adafruit_bus_device
#   - adafruit_framebuf
# ─────────────────────────────────────────────────────────────────────────────

import board        # Gives us access to pin names like board.D0, board.SDA
import busio        # Handles I2C communication for the OLED
import time         # For delays and timestamps
import math         # For atan2 (angle calculation for color wheel)
import analogio     # For reading analog joystick values (0-65535)
import digitalio    # For reading digital button states (True/False)
import pwmio        # For PWM output to control LED brightness
import adafruit_ssd1306  # OLED display library from Adafruit


# ─────────────────────────────────────────────────────────────────────────────
# PIN SETUP
# ─────────────────────────────────────────────────────────────────────────────

# RGB LED pins — PWM allows us to control brightness by varying duty cycle
# frequency=1000 means the pin switches on/off 1000 times per second
# This is fast enough that the eye perceives it as a steady dimmed light (PWM)
led_red   = pwmio.PWMOut(board.D2, frequency=1000)  # Red channel   → PA10
led_green = pwmio.PWMOut(board.D3, frequency=1000)  # Green channel → PA11
led_blue  = pwmio.PWMOut(board.D6, frequency=1000)  # Blue channel  → PB08

# SW1 — Mode toggle button (Color ↔ Brightness)
# Pull.UP means the pin is held HIGH (True) by default
# When button is pressed, it connects to GND → reads False
sw1 = digitalio.DigitalInOut(board.D0)
sw1.direction = digitalio.Direction.INPUT
sw1.pull = digitalio.Pull.UP

# SW2 — Preset cycle button
sw2 = digitalio.DigitalInOut(board.D1)
sw2.direction = digitalio.Direction.INPUT
sw2.pull = digitalio.Pull.UP

# Joystick analog axes — read voltage as 0 to 65535
# Center position reads approximately 32768
joy_x = analogio.AnalogIn(board.A7)   # Left/Right → PB09
joy_y = analogio.AnalogIn(board.A8)   # Up/Down    → PA07

# Joystick SW button — pressing the joystick stick down
joy_sw = digitalio.DigitalInOut(board.A9)
joy_sw.direction = digitalio.Direction.INPUT
joy_sw.pull = digitalio.Pull.UP

# OLED Display — communicates via I2C protocol using SDA and SCL pins
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)  # 128px wide, 32px tall


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS — values that never change during the program
# ─────────────────────────────────────────────────────────────────────────────

# Mode identifiers — stored as integers so we can compare with ==
MODE_COLOR      = 0   # Joystick controls hue on color wheel
MODE_BRIGHTNESS = 1   # Joystick Y controls brightness
MODE_NAMES      = ["COLOR MODE", "BRIGHTNESS MODE"]

# Color presets — list of tuples (name, R, G, B)
# Tuples are used here because presets should NEVER be modified at runtime
# (tuples are immutable in Python — trying to change them causes an error)
PRESETS = [
    ("Red",     255,   0,   0),
    ("Green",     0, 255,   0),
    ("Blue",      0,   0, 255),
    ("Yellow",  255, 255,   0),
    ("Cyan",      0, 255, 255),
    ("Purple",  128,   0, 128),
    ("White",   255, 255, 255),
    ("Orange",  255, 128,   0),
]

# Joystick calibration values
JOYSTICK_CENTER   = 32768  # Midpoint of 16-bit ADC range (0-65535)
JOYSTICK_DEADZONE = 4000   # Ignore movements smaller than this — prevents
                           # LED flickering when joystick is resting at center
JOYSTICK_MAX      = 32768  # Maximum deviation from center in either direction

# Debounce timing — minimum milliseconds between valid button presses
# Prevents electrical contact bouncing from registering as multiple presses
DEBOUNCE_MS = 200


# ─────────────────────────────────────────────────────────────────────────────
# STATE VARIABLES — the program's memory between loop iterations
# ─────────────────────────────────────────────────────────────────────────────

# Current operating mode (COLOR or BRIGHTNESS)
mode = MODE_COLOR

# Current position in the presets list (0 = Red, 1 = Green, etc.)
preset_index = 0

# Current brightness level: 0.0 = off, 1.0 = full brightness
brightness = 1.0

# Current saturation level: 0.0 = grey/white, 1.0 = fully vivid color
saturation = 1.0

# Whether saturation mode is active (toggled by joystick SW button)
sat_mode = False

# Current RGB values (0-255 each)
r, g, b = 255, 0, 0

# Current color name shown on OLED
color_name = "Red"

# Current hue angle on color wheel (0.0 to 360.0 degrees)
hue = 0.0

# ── Button state tracking variables ──────────────────────────────────────────
# Each button needs TWO tracking variables:
#   _last      → what the button was doing LAST loop (True = not pressed)
#   _debounce  → timestamp of the last accepted press (in milliseconds)
#
# How they work together to detect exactly ONE press:
#   not _val   → button IS pressed right now
#   _last      → button was NOT pressed last loop (catches only first loop of press)
#   time check → enough time passed since last press (handles electrical bouncing)

sw1_last       = True   # SW1 was not pressed at startup
sw2_last       = True   # SW2 was not pressed at startup
joy_sw_last    = True   # Joystick button was not pressed at startup

sw1_debounce      = 0   # Timestamp of last accepted SW1 press (0 = never pressed)
sw2_debounce      = 0   # Timestamp of last accepted SW2 press
joy_sw_debounce   = 0   # Timestamp of last accepted joystick button press


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def set_led(r_val, g_val, b_val, bright=1.0):
    """
    Set LED color with brightness scaling.
    Input:  r_val, g_val, b_val = 0 to 255
            bright = 0.0 to 1.0
    Output: PWM duty cycle 0 to 65535

    Formula: duty_cycle = color_value * brightness * 257
    Why 257? Because 255 * 257 = 65535 (the max PWM value)
    """
    scale = int(bright * 257)
    led_red.duty_cycle   = int(r_val * scale)
    led_green.duty_cycle = int(g_val * scale)
    led_blue.duty_cycle  = int(b_val * scale)


def hsv_to_rgb(h, s=1.0, v=1.0):
    """
    Convert HSV color to RGB values.

    H (Hue)        = 0 to 360 degrees — position on color wheel
    S (Saturation) = 0.0 to 1.0 — 0 is grey/white, 1 is fully vivid
    V (Value)      = 0.0 to 1.0 — brightness (we handle this separately)

    Returns: (R, G, B) each 0 to 255

    The math divides the color wheel into 6 sectors of 60 degrees each:
      0-60    Red to Yellow
      60-120  Yellow to Green
      120-180 Green to Cyan
      180-240 Cyan to Blue
      240-300 Blue to Magenta
      300-360 Magenta to Red
    """
    h = h % 360          # Keep hue in 0-360 range using modulus
    c = v * s            # Chroma (color intensity)
    x = c * (1 - abs((h / 60) % 2 - 1))  # Secondary color component
    m = v - c            # Base brightness offset

    # Determine RGB based on which 60 degree sector hue falls in
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x

    # Scale from 0-1 to 0-255 and add base offset
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def hue_to_name(h):
    """
    Return approximate color name for a given hue angle.
    These are ranges, not exact values — every angle in between
    is a valid color, just shown with the nearest English name.

    Example: hue=23 is Orange, hue=47 is Yellow, hue=200 is Cyan
    """
    h = h % 360
    if   h < 15  or h >= 345: return "Red"
    elif h < 45:               return "Orange"
    elif h < 75:               return "Yellow"
    elif h < 150:              return "Green"
    elif h < 195:              return "Cyan"
    elif h < 255:              return "Blue"
    elif h < 285:              return "Purple"
    elif h < 345:              return "Pink"
    return "Red"


def read_joystick():
    """
    Read joystick X and Y axes and return normalized values.

    Raw ADC value: 0 to 65535
    After subtracting center (32768): -32768 to +32767
    After deadzone + normalization:   -1.0 to +1.0

    Deadzone: ignore tiny movements near center to prevent
    the LED from flickering when joystick is resting still.
    """
    # Read raw values and subtract center to get deviation from center
    raw_x = joy_x.value - JOYSTICK_CENTER
    raw_y = joy_y.value - JOYSTICK_CENTER

    # Apply deadzone — set to 0 if movement is too small to matter
    if abs(raw_x) < JOYSTICK_DEADZONE: raw_x = 0
    if abs(raw_y) < JOYSTICK_DEADZONE: raw_y = 0

    # Normalize to -1.0 to +1.0 and clamp to valid range
    norm_x = max(-1.0, min(1.0, raw_x / JOYSTICK_MAX))
    norm_y = max(-1.0, min(1.0, raw_y / JOYSTICK_MAX))

    return norm_x, norm_y


def update_oled(color_name, r, g, b, brightness, saturation, mode, sat_mode):
    """
    Refresh OLED display with current state.
    Display is 128x32 pixels — fits exactly 3 lines of text at size 1.

    oled.fill(0)             → clear screen to black (0=black, 1=white)
    oled.text(str, x, y, 1) → draw white text at pixel position x, y
    oled.show()              → push buffer to physical screen
    """
    oled.fill(0)  # Clear screen before redrawing everything

    # Line 1 (y=0): Show current mode, or SAT MODE if saturation active
    if sat_mode:
        oled.text("SAT MODE", 0, 0, 1)
    else:
        oled.text(MODE_NAMES[mode], 0, 0, 1)

    # Line 2 (y=10): Current color name
    oled.text("Color: " + color_name, 0, 10, 1)

    # Line 3 (y=20): RGB values on left side
    oled.text("R:{} G:{} B:{}".format(r, g, b), 0, 20, 1)

    # Right side of line 3: saturation % in sat mode, brightness % otherwise
    if sat_mode:
        oled.text("S:{}%".format(int(saturation * 100)), 95, 20, 1)
    else:
        oled.text("{}%".format(int(brightness * 100)), 100, 20, 1)

    oled.show()  # Push all drawn content to the physical OLED screen


def millis():
    """
    Return current time in milliseconds since program started.
    Used for debounce timing — same concept as millis() in Arduino C++.
    time.monotonic() returns seconds as a float, multiply by 1000 for ms.
    """
    return int(time.monotonic() * 1000)


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP SEQUENCE
# ─────────────────────────────────────────────────────────────────────────────

# Show splash screen for 2 seconds so user knows board is powered on
oled.fill(0)
oled.text("RGB Micropad", 10, 5, 1)
oled.text("by Rishaan D.", 10, 18, 1)
oled.show()
time.sleep(2)

# Set initial LED color (Red at full brightness and saturation)
set_led(r, g, b, brightness)

# Draw initial OLED state
update_oled(color_name, r, g, b, brightness, saturation, mode, sat_mode)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP — runs forever, approximately 20 times per second (50ms per loop)
# ─────────────────────────────────────────────────────────────────────────────

while True:

    # Get current timestamp at start of each loop
    # Used for all debounce time calculations this iteration
    now = millis()

    # ── BUTTON SW1 — Toggle Mode (Color vs Brightness) ───────────────────────
    sw1_val = sw1.value  # True = not pressed, False = pressed (pull-up logic)

    if (not sw1_val               # Button IS pressed right now
    and sw1_last                  # Button was NOT pressed last loop
    and (now - sw1_debounce) > DEBOUNCE_MS):  # 200ms passed since last press

        # Ternary operator: toggle between modes
        # "Set mode to BRIGHTNESS if currently COLOR, otherwise set to COLOR"
        mode = MODE_BRIGHTNESS if mode == MODE_COLOR else MODE_COLOR
        sw1_debounce = now        # Reset debounce timer

    sw1_last = sw1_val            # Save state for next loop comparison


    # ── BUTTON SW2 — Cycle Color Presets ─────────────────────────────────────
    sw2_val = sw2.value

    if (not sw2_val
    and sw2_last
    and (now - sw2_debounce) > DEBOUNCE_MS):

        # Advance preset index, wrap to 0 using modulus when end is reached
        # Example: (7 + 1) % 8 = 0 → wraps from last preset back to first
        preset_index = (preset_index + 1) % len(PRESETS)

        # Unpack tuple into 4 variables: name, R, G, B
        color_name, r, g, b = PRESETS[preset_index]

        # Update LED immediately with new preset color
        set_led(r, g, b, brightness)
        sw2_debounce = now

    sw2_last = sw2_val


    # ── JOYSTICK BUTTON — Toggle Saturation Mode ──────────────────────────────
    joy_sw_val = joy_sw.value

    if (not joy_sw_val            # Joystick button IS pressed right now
    and joy_sw_last               # Was NOT pressed last loop
    and (now - joy_sw_debounce) > DEBOUNCE_MS):

        # Toggle saturation mode: False becomes True, True becomes False
        sat_mode = not sat_mode
        joy_sw_debounce = now

    joy_sw_last = joy_sw_val


    # ── READ JOYSTICK AXES ────────────────────────────────────────────────────
    joy_norm_x, joy_norm_y = read_joystick()  # Returns -1.0 to +1.0


    # ── COLOR MODE ────────────────────────────────────────────────────────────
    if mode == MODE_COLOR:

        if sat_mode:
            # SATURATION SUB-MODE: Y axis controls saturation only
            # Push joystick up = more vivid, down = more grey/white
            if abs(joy_norm_y) > 0:
                saturation += joy_norm_y * 0.02           # Small step per loop
                saturation = max(0.0, min(1.0, saturation))  # Clamp 0.0-1.0
                r, g, b = hsv_to_rgb(hue, saturation)     # Recalculate RGB
                set_led(r, g, b, brightness)

        else:
            # NORMAL COLOR MODE: joystick angle maps directly to hue
            # math.atan2(y, x) calculates the angle of the joystick vector
            # Result is in radians (-pi to pi), convert to degrees (0-360)
            if abs(joy_norm_x) > 0 or abs(joy_norm_y) > 0:
                angle = math.atan2(joy_norm_y, joy_norm_x) # Radians -pi to pi
                hue = (math.degrees(angle) + 360) % 360    # Convert to 0-360
                r, g, b = hsv_to_rgb(hue, saturation)      # RGB from hue+sat
                color_name = hue_to_name(hue)              # Name for display
                set_led(r, g, b, brightness)


    # ── BRIGHTNESS MODE ───────────────────────────────────────────────────────
    elif mode == MODE_BRIGHTNESS:

        # Y axis only: push up = brighter, push down = dimmer
        if abs(joy_norm_y) > 0:
            brightness += joy_norm_y * 0.02               # Small step per loop
            brightness = max(0.0, min(1.0, brightness))   # Clamp 0.0-1.0
            set_led(r, g, b, brightness)


    # ── UPDATE OLED DISPLAY ───────────────────────────────────────────────────
    # Refresh every loop so display always shows current state
    update_oled(color_name, r, g, b, brightness, saturation, mode, sat_mode)


    # ── LOOP TIMING ───────────────────────────────────────────────────────────
    # 50ms delay = 20 loops per second
    # Fast enough to feel responsive, slow enough to save power
    time.sleep(0.05)
