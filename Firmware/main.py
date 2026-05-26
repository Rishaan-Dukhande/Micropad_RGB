# RGB Micropad Firmware
# Author: Rishaan Dukhande
# Description: Controls an RGB LED via joystick and buttons
#              SW1 = toggle mode (Color / Brightness)
#              SW2 = cycle presets
#              Joystick = control color (color mode) or brightness (brightness mode)
#              OLED = display current color name, RGB values, brightness %

# ─────────────────────────────────────────────
# REQUIRED LIBRARIES (copy to CIRCUITPY/lib/)
# - adafruit_ssd1306
# - adafruit_bus_device
# - adafruit_framebuf
# ─────────────────────────────────────────────

import board
import busio
import time
import math
import analogio
import digitalio
import pwmio
import displayio
import adafruit_ssd1306

# ─────────────────────────────────────────────
# PIN SETUP
# ─────────────────────────────────────────────

# RGB LED (PWM for brightness control)
led_red   = pwmio.PWMOut(board.D2, frequency=1000)
led_green = pwmio.PWMOut(board.D3, frequency=1000)
led_blue  = pwmio.PWMOut(board.D6, frequency=1000)

# Buttons
sw1 = digitalio.DigitalInOut(board.D0)   # Mode toggle
sw1.direction = digitalio.Direction.INPUT
sw1.pull = digitalio.Pull.UP

sw2 = digitalio.DigitalInOut(board.D1)   # Preset cycle
sw2.direction = digitalio.Direction.INPUT
sw2.pull = digitalio.Pull.UP

# Joystick
joy_x  = analogio.AnalogIn(board.A7)
joy_y  = analogio.AnalogIn(board.A8)

joy_sw = digitalio.DigitalInOut(board.A9)  # Joystick button (unused but initialized)
joy_sw.direction = digitalio.Direction.INPUT
joy_sw.pull = digitalio.Pull.UP

# OLED Display (I2C)
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

# Modes
MODE_COLOR      = 0
MODE_BRIGHTNESS = 1
MODE_NAMES      = ["COLOR MODE", "BRIGHTNESS MODE"]

# Color presets (name, R, G, B)
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

JOYSTICK_CENTER   = 32768   # Midpoint of 16-bit ADC
JOYSTICK_DEADZONE = 4000    # Ignore small movements
JOYSTICK_MAX      = 32768   # Max deviation from center

# ─────────────────────────────────────────────
# STATE VARIABLES
# ─────────────────────────────────────────────

mode            = MODE_COLOR
preset_index    = 0
brightness      = 1.0        # 0.0 to 1.0
r, g, b         = 255, 0, 0  # Current RGB values
color_name      = "Red"

sw1_last        = True       # Pull-up: True = not pressed
sw2_last        = True
sw1_debounce    = 0
sw2_debounce    = 0
DEBOUNCE_MS     = 200        # Milliseconds between button reads

# Hue for color wheel (0-360)
hue = 0.0

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def set_led(r_val, g_val, b_val, bright=1.0):
    """Set LED color with brightness scaling. Input 0-255, output PWM 0-65535."""
    scale = int(bright * 257)  # Scale brightness to PWM range
    led_red.duty_cycle   = int(r_val * scale)
    led_green.duty_cycle = int(g_val * scale)
    led_blue.duty_cycle  = int(b_val * scale)

def hsv_to_rgb(h, s=1.0, v=1.0):
    """Convert hue (0-360), saturation, value to R, G, B (0-255)."""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

def hue_to_name(h):
    """Return approximate color name from hue angle."""
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
    """Read joystick X and Y, return values from -1.0 to 1.0."""
    raw_x = joy_x.value - JOYSTICK_CENTER
    raw_y = joy_y.value - JOYSTICK_CENTER
    # Apply deadzone
    if abs(raw_x) < JOYSTICK_DEADZONE: raw_x = 0
    if abs(raw_y) < JOYSTICK_DEADZONE: raw_y = 0
    # Normalize to -1.0 to 1.0
    norm_x = max(-1.0, min(1.0, raw_x / JOYSTICK_MAX))
    norm_y = max(-1.0, min(1.0, raw_y / JOYSTICK_MAX))
    return norm_x, norm_y

def update_oled(color_name, r, g, b, brightness, mode):
    """Refresh OLED display with current state."""
    oled.fill(0)
    # Line 1: Mode
    oled.text(MODE_NAMES[mode], 0, 0, 1)
    # Line 2: Color name
    oled.text("Color: " + color_name, 0, 10, 1)
    # Line 3: RGB values
    oled.text("R:{} G:{} B:{}".format(r, g, b), 0, 20, 1)
    # Brightness % on far right of line 3 (small)
    bright_str = "{}%".format(int(brightness * 100))
    oled.text(bright_str, 100, 20, 1)
    oled.show()

def millis():
    """Return current time in milliseconds."""
    return int(time.monotonic() * 1000)

# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────

oled.fill(0)
oled.text("RGB Micropad", 10, 5, 1)
oled.text("by Rishaan D.", 10, 18, 1)
oled.show()
time.sleep(2)

set_led(r, g, b, brightness)
update_oled(color_name, r, g, b, brightness, mode)

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────

while True:
    now = millis()

    # ── BUTTON SW1 — Toggle Mode ──────────────
    sw1_val = sw1.value
    if not sw1_val and sw1_last and (now - sw1_debounce) > DEBOUNCE_MS:
        mode = MODE_BRIGHTNESS if mode == MODE_COLOR else MODE_COLOR
        sw1_debounce = now
    sw1_last = sw1_val

    # ── BUTTON SW2 — Cycle Presets ────────────
    sw2_val = sw2.value
    if not sw2_val and sw2_last and (now - sw2_debounce) > DEBOUNCE_MS:
        preset_index = (preset_index + 1) % len(PRESETS)
        color_name, r, g, b = PRESETS[preset_index]
        # Recalculate hue from preset so color wheel stays in sync
        hue = (PRESETS[preset_index][0] == "Red"    and 0)   or \
              (PRESETS[preset_index][0] == "Green"  and 120) or \
              (PRESETS[preset_index][0] == "Blue"   and 240) or \
              (PRESETS[preset_index][0] == "Yellow" and 60)  or \
              (PRESETS[preset_index][0] == "Cyan"   and 180) or \
              (PRESETS[preset_index][0] == "Purple" and 270) or \
              (PRESETS[preset_index][0] == "White"  and 0)   or \
              (PRESETS[preset_index][0] == "Orange" and 30)  or 0
        set_led(r, g, b, brightness)
        sw2_debounce = now
    sw2_last = sw2_val

    # ── JOYSTICK ──────────────────────────────
    joy_norm_x, joy_norm_y = read_joystick()

    if mode == MODE_COLOR:
        # Map joystick position to hue angle on color wheel
        # Only move hue if joystick is outside deadzone
        if abs(joy_norm_x) > 0 or abs(joy_norm_y) > 0:
            # Calculate angle from joystick position
            angle = math.atan2(joy_norm_y, joy_norm_x)  # -pi to pi
            hue = (math.degrees(angle) + 360) % 360      # Convert to 0-360
            r, g, b = hsv_to_rgb(hue)
            color_name = hue_to_name(hue)
            set_led(r, g, b, brightness)

    elif mode == MODE_BRIGHTNESS:
        # Only Y axis controls brightness
        if abs(joy_norm_y) > 0:
            brightness += joy_norm_y * 0.02   # Small step per loop
            brightness = max(0.0, min(1.0, brightness))  # Clamp 0-1
            set_led(r, g, b, brightness)

    # ── UPDATE OLED every loop ────────────────
    update_oled(color_name, r, g, b, brightness, mode)

    time.sleep(0.05)  # 50ms loop = 20 updates per second
