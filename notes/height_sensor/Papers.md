## A novel wave height sensor (Champan & Monaldo, 1993)
### 1.1 Questions

1. Accuracy of measurement, with respect to their reported sensitivity of $0.02 μ F ↔ 0.5 c m$ (small capacitance error corresponding to what is for us quite a large height error).
2. What is the circuit? Do we close it as usual from two sides of the wire? Is it a simple RC with square input or something more elaborate?
3. What exactly is the lower thickness limit of the oxide? How does leakage affect the capacitance, in a way that is not already reflected in the calibration curve? What is the optimal balance of minimizing leakage vs. maximizing capacitance in our system? How can we observe leakage from the standard capacitance measurement?
4. Self healing - shouldn’t happen exactly at the voltage of anodization? I’d think lower voltages will heal only a relatively deep crack. I saw $80V$ for anodization and $5V$ for healing.
5. On the other hand, why do we need a bias at all for valving? Isn’t it enough to input a positive bias for charging, with ground voltage for discharge?
6. How crucial will it be to know the exact salinity/chemistry of the water for calibration of the gauge? I think what we actually measure is the dielectricity of the excess water, and this I presume can depend strongly on its chemistry.
    
    \[The static dielectric constant (relative permittivity) of seawater is lower than pure water (around 80) and varies with temperature and salinity, but a common value used for open ocean conditions (around 20°C, 35 ppt salinity) is approximately 70-78\]
    
7. How important is it that the relationship between capacitance and local water height be linear? Isn’t a good (monotonic...) calibration curve enough?
8. Do we need fast charging for any reason but to save time?
9. What kinds of problems, noise sources etc. appear during simple measurements?
10. Verify no cross talks. In the paper they claim none down to $2 c m$ apart.

### 1.2 Idea

We want a non-intrusive way to measure wave height. The idea is to measure capacitance of a thin wire partly submerged in the water. If meniscus formed is small, the change in the wire capacitance (at the order of $μ F$ ) tracks the changes in the water height. Applying a DC offset signal keeps an anodizing process on, which self-heals damages to the oxide.

The wire is made of tantalum covered with its oxide ( $T a_2 O_5$ , made by submerging in citric acid), which is a good insulator.

The wire is connected to a circuit that feeds it with a square signal. Decay rate of the charge on the wire reports its capacitance. If the dielectric coating is uniform, the capacitance will change linearly with the height of the water.

### 1.3 Specifications

| parameter              | size                                        | comment                                  |
| ---------------------- | ------------------------------------------- | ---------------------------------------- |
| tantalum wire diameter | $0.635 m m$                                 | the thinner the higher detection quality |
| corr. tensile strength | $70 k g m m ^{- 2}$ per $22 k g$ long. load | should taut the wire without tearing it  |

### 1.4 Manufacture process

1. Clean thoroughly in trichloroethane.
2. Rinse. Use gloves!
3. Put in citric acid under $0.5 m A c m ^{-2}$ (per total tantalum wire surface) DC up to $80 V$ , wherefrom the voltage is held constant, for __ minutes. **Smaller formation voltage generates thinner oxide layer.** Anodizing configuration:
    
    1. A trough long enough to hold the required wire including edge locking, with wire support glued to the bottom near both ends and terminal strips at the ends.
    2. A ground $6 m m$ stainless steel wire at the bottom of the trough.
    3. Rinsed tantalum wires strung near the top of the trough through the supports and terminals.
    4. $0.01\%$ citric acid solution that was stirred for several hours and then equilibrated over 24 hours.
    
    At constant voltage, perfect insulation will give 0 current. Hence minimal current (before excess defects develop) corresponds to best isolation. May try to replace electrolyte solution with cleaner one if leakage is above $0.005 m A c m ^{-2}$ (again proportional to total wire interface).
    
4. Rinse.
5. Cut the wire at the support positions.
6. Dry.
7. Observe metallic purple color. Hue indicates thickness, as the color is the result of thin film interference. [Observe effect of bending.]
    
    Remark 1. In the paper, they got $3.2 μ F m ^{-1}$ , I think per wire.
    

### 1.5 Circuit

The wire takes as an input a square waveform, that is, an alternating charge and discharge of the capacitor.

### 1.6 Digitization

Make sure that the digitization is good enough to measure the full scale height to voltage from the circuit.

### 1.7 Operation

1. Soak in target water for $30 m i n$ to relax initial drift processes, associated with crystallization of the oxide. \[Maybe I want to test that.\]

* As per their fig. 7, at $25 c m$ water depth and with a $3 c m$ diameter electronics tube at the bottom, the trend is already robustly linear at still water.

* Deviation from linear trend should be of the order of $± 0.05 μ F$ for capacitance of $∼ 0.1 - 10 μ F$. They report an error of 0.5 c m for static depth in the range $25 - 300 c m$ . We need something more sensitive.

* Frequency response should drop down $∼ 3 d B$ at $16 H z$, so we do not expect to measure very small ripples.  

* We should recalibrate the system once every two weeks or so to see that the capacitance-to-height slope didn’t change significantly.

* Notice not to allow resonance between capillaries and wires.