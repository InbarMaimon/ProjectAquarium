event report 22/3/2026

## short circuit
On the 18/3, Wednesday, I approached Tomer Brosh, the electrical engineer of the institute of earth sciences, and we connected the wiring of the motor circuit. Later in the lab I completed the circuit with the Raspberry Pi Pico (powered by my Thinkpad) and ran a short series of tests. mostly moving the coil statically up and down. The motor responded, though not cleanly. No further details.
While dissembling the circuit, I forgot to disconnect the power supply first. I loosened the screws that mount the motor and the power supply on the driver, and pulled out the + wire of the power supply. It touched the heads of the screws that mount the outputs of the motor. There was a short, part of the screw heads got brown, and the wire's terminal stuck to the head. I believe that at this point it disconnected the power and then separated the wire from the screw by applying a modest amount of force. Afterward I conncted the circuit again and it worked.

Measured today: 
resistance between the motor terminals: 1.6-1.7 ohm
diode resistance between the screws when the wires are disconnected is:
    
    
    
    
