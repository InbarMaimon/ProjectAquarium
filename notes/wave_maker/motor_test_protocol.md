## order of assemble:
1. Make a clean surface with room for motor, driver and controller.
2. Put the power supply in an accessible position far from everything else.
3. Put the motor gently with pin up.
4. Put the driver nearby.
5. Connect the PS wires to the driver. Make sure that - (blue) goes to GND and + (brown) goes to VIN. Screw them.
6. Connect the motor wires to the driver. Make sure that OUTA (red) goes to OUTA and OUTB (black) goes to OUTB.
7. Put the Pico nearby, legs up.
8. Wiring:
  GP0  → [brown] → 810-01 PWM pin
  GP1  → [orange] → 810-01 DIR pin
  GP2  → [white] → 810-01 RESET pin  (active LOW: pull low to disable driver)
  GND  → [black] → 810-01 Logic GND
9. Connect Pico to computer.
10. Connect Pico to VS code interface.
11. Download current image of the test files.
12. Verify that everything is there using os.listdir().
13. Connect power.
14. Set duty to 0, enable, set duty to 5%, observe lift.
15. Play.


## order of dissemble:
1. Set duty to 0, observe the magnet falls back to place, disable.
2. Assemble in reverse.
