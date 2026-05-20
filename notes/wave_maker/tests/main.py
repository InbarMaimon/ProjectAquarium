"""
moticont_hold.py
----------------
Raspberry Pi Pico 2W  →  Moticont 810-01 driver  →  GVCM-015-025-01

Wiring:
  GP0  → [brown] → 810-01 PWM pin
  GP1  → [orange] → 810-01 DIR pin
  GP2  → [white] → 810-01 RESET pin  (active LOW: pull low to disable driver)
  GND  → [black] → 810-01 Logic GND

PWM frequency : 20 kHz  (inaudible, well within driver 50 kHz max)
Control       : USB serial (115200 baud) — connect with any terminal
                e.g.  screen /dev/ttyACM0 115200
                      PuTTY, Thonny REPL, etc.

Serial commands (case-insensitive):
  enable          - release RESET, driver becomes active
  disable         - assert RESET, driver disabled (coil de-energised)
  duty <0-100>    - set PWM duty cycle as a percentage  e.g. "duty 35"
  dir <0|1>       - set direction  (0 = OUTB→OUTA, 1 = OUTA→OUTB)
  status          - print current duty, direction, and enable state

Notes:
  - This is open-loop. Start with a LOW duty cycle (~10-20%) and increase
    slowly until the coil holds position against gravity. Exceeding the
    motor's continuous current rating will cause overheating.
  - GVCM-051-025-01 continuous force is modest; don't run at 100% duty
    for extended periods without checking motor temperature.
  - The RESET pin is active-LOW on the 810-01. Driving GP2 HIGH releases
    the driver; driving it LOW disables it.
"""

import sys
import select
from tests_vc import handle_line

# ---------------------------------------------------------------------------
# Boot banner
# ---------------------------------------------------------------------------
print("=" * 50)
print("  Moticont GVCM-015-025-01 / 810-01 hold controller")
print("  Pico 2W  |  20 kHz PWM  |  GP0=PWM  GP1=DIR  GP2=RESET")
print("  Driver is DISABLED on boot. Send 'enable' to start.")
print("  Type 'status' for current settings.")
print("=" * 50)

# ---------------------------------------------------------------------------
# Main loop — non-blocking USB serial read
# ---------------------------------------------------------------------------
buf = ""

while True:
    # Poll stdin without blocking (works on Pico USB serial)
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        ch = sys.stdin.read(1)
        if ch in ("\r", "\n"):
            if buf:
                handle_line(buf)
                buf = ""
            else:
                continue
        elif ch == "\x08":   # backspace
            buf = buf[:-1]
        else:
            buf += ch
