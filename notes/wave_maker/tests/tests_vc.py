import sys
import select
import time
import math
from machine import Pin, PWM

# ---------------------------------------------------------------------------
# Pin assignments
# ---------------------------------------------------------------------------
PIN_PWM   = 0   # GP0 → 810-01 PWM input
PIN_DIR   = 1   # GP1 → 810-01 DIR input
PIN_RESET = 2   # GP2 → 810-01 RESET input (HIGH = run, LOW = disabled)

# ---------------------------------------------------------------------------
# PWM configuration
# ---------------------------------------------------------------------------
PWM_FREQ_HZ = 20_000   # 20 kHz — inaudible, within driver spec

# ---------------------------------------------------------------------------
# Default motion parameters  (edit these as a starting point)
# ---------------------------------------------------------------------------
DEFAULT_DUTY_PERCENT = 0    # Start at 0%; increase via serial once enabled
DEFAULT_DIRECTION    = 1    # 1 = OUTA→OUTB; pushes outward

# ---------------------------------------------------------------------------
# Hardware initialisation
# ---------------------------------------------------------------------------
pwm = PWM(Pin(PIN_PWM))
pwm.freq(PWM_FREQ_HZ)

dir_pin   = Pin(PIN_DIR,   Pin.OUT)
reset_pin = Pin(PIN_RESET, Pin.OUT)

# Helpers
def _duty_u16(percent: float) -> int:
    """Convert 0–100 % to 0–65535 for machine.PWM.duty_u16()."""
    return int(max(0.0, min(100.0, percent)) / 100.0 * 65535)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
state = {
    "enabled": False,
    "duty":    DEFAULT_DUTY_PERCENT,
    "dir":     DEFAULT_DIRECTION,
}

def _apply_state():
    """Push current state to hardware."""
    dir_pin.value(state["dir"])
    pwm.duty_u16(_duty_u16(state["duty"]) if state["enabled"] else 0)
    # RESET pin: HIGH = driver active, LOW = driver disabled
    reset_pin.value(1 if state["enabled"] else 0)

# Start safe: driver in reset, zero PWM
_apply_state()

# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------
def cmd_enable(_args):
    state["enabled"] = True
    _apply_state()
    return f"Driver ENABLED  |  duty={state['duty']:.1f}%  dir={state['dir']}"

def cmd_disable(_args):
    state["enabled"] = False
    _apply_state()
    return "Driver DISABLED  (coil de-energised, RESET asserted)"

def cmd_duty(args):
    if not args:
        return "ERROR: usage:  duty <0-100>"
    try:
        val = float(args[0])
    except ValueError:
        return "ERROR: duty value must be a number 0–100"
    if not (0 <= val <= 100):
        return "ERROR: duty must be between 0 and 100"
    state["duty"] = val
    if state["enabled"]:
        pwm.duty_u16(_duty_u16(val))
    return f"Duty set to {val:.1f}%  {'(applied)' if state['enabled'] else '(staged — enable driver to apply)'}"

def cmd_sine(args):
    """sine [center_%] [amplitude_%] [period_ms]
    Oscillates duty cycle as:  center + amplitude * sin(t)
    Defaults: center=4  amplitude=1  period=2000ms
    Send any serial character to stop.
    """

    try:
        center    = float(args[0]) if len(args) > 0 else 4.0
        amplitude = float(args[1]) if len(args) > 1 else 1.0
        period_ms = float(args[2]) if len(args) > 2 else 2000.0
    except ValueError:
        return "ERROR: usage:  sine [center_%] [amplitude_%] [period_ms]"
 
    if not state["enabled"]:
        return "ERROR: driver not enabled — send 'enable' first"
 
    max_duty = center + amplitude
    if max_duty > 25:
        return f"ERROR: center+amplitude={max_duty:.1f}% exceeds 25% continuous limit at 24V"
 
    print(f"Sine running: center={center}%  amplitude={amplitude}%  period={period_ms}ms")
    print("Send any key to stop.")
 
    step_ms   = 1                           # update every 1ms → 1kHz
    steps     = int(period_ms / step_ms)    # steps per full cycle
    i         = 0
 
    while True:
        # Check for keypress to stop
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.read(1)               # consume the character
            break
        angle    = 2 * math.pi * (i % steps) / steps
        duty_pct = center + amplitude * math.sin(angle)
        pwm.duty_u16(_duty_u16(duty_pct))
        time.sleep(step_ms / 1000)
        i += 1
 
    # Restore previous duty on exit
    pwm.duty_u16(_duty_u16(state["duty"]))
    return f"Sine stopped. Duty restored to {state['duty']:.1f}%"

def cmd_dir(args):
    if not args or args[0] not in ("0", "1"):
        return "ERROR: usage:  dir <0|1>"
    state["dir"] = int(args[0])
    if state["enabled"]:
        dir_pin.value(state["dir"])
    return f"Direction set to {state['dir']}  {'(applied)' if state['enabled'] else '(staged — enable driver to apply)'}"

def cmd_status(_args):
    lines = [
        "--- Status ---",
        f"  Enabled  : {state['enabled']}",
        f"  Duty     : {state['duty']:.1f}%",
        f"  Direction: {state['dir']}  (0=OUTB→OUTA  1=OUTA→OUTB)",
        f"  PWM freq : {PWM_FREQ_HZ} Hz",
    ]
    return "\n".join(lines)

COMMANDS = {
    "enable":  cmd_enable,
    "disable": cmd_disable,
    "duty":    cmd_duty,
    "sine":    cmd_sine,
    "dir":     cmd_dir,
    "status":  cmd_status,
}

def handle_line(line: str):
    parts = line.strip().lower().split()
    if not parts:
        return
    verb, args = parts[0], parts[1:]
    if verb in COMMANDS:
        response = COMMANDS[verb](args)
    else:
        response = (
            "Unknown command. Available: enable | disable | duty <0-100> "
            "| dir <0|1> | status"
        )
    print(response)
