### Administrative
1. Get access to uni. systems with the lab under Sprinzak.
2. Safety and return a validation doc.
3. OTP?
4. Access to printer.
5. Duplicate backdoor key.

### General
1. Learn git and absorb into workflow.

### Aquarium
1. Find for it a permanent place.

### Wave maker
1. On Sunday, talk to the guys at Abiry. 
2. Once we settle on a complete solution, including exact parts, talk to Tomer Brosh again about it.

### Height sensor
1. Decide if we go for a capacitive wire gauge or a laser sensor.
   1. Physical parameters: 
       1. Sub-millimeter height sensitivity,
       2. 10-30mm height range (30mm is our 5Hz mode peak-to-peak distance),
       3. Beam width < ~5mm.
       4. Reflects well from water, sloped.
       5. Mechanical resonances?.
   2. Electronics:
       1. Connectivity: output compatible with wave maker's controller.
       2. Sampling rate above 60Hz.
2. We can color the water to enlarge the relevant measuring systems. Maybe LIDAR
   is an option? 
3. Capacitive gauge making:
    1. Decide length and number of wires.
    2. Derive length of trough.
    3. Design electric connections. Fit terminal strip.
    4. Decide on solution for holders.
    5. Buy: tantalum - Aviv, pipe for trough, stainless steel rod/wire, material for holders, citric acid - Liron, terminal - Liron, power source - Yosi.
    6. Cut trough and holders. Leave path for rod.
    7. Glue holders.
    8. Get smart voltage source.
    9.  Get pure water.
    10. Put ground SS rod and connect to source.
    11. Put wires on holders and connect to terminal.
    12. Connect terminal to source.
    13. Observe result.
    

 
```mermaid
flowchart TD
    START[Start] --> HEIGHT([Height sensor: physical requirements & pricing])
    START[Start] --> WM([wave making theory])

    HEIGHT --> SENS_SEL{Select Sensor Type}
    
    WM --> WM_SD[required stroke depth: ~2-20mm];
    RG1[research goals: inspect strictly capillary waves] --> WM_GF[required frequencies: ~5-30Hz];
    RG2[research goals regarding type of interactions] --> Meas_MD[measurement distance where standing waves vanish: 30cm is more than enough]

    WM --> Meas_MD
    WM_SD --> WM_CM[Choose motor];
    WM_GF --> WM_CM;
    WM_CM --> WM_F[Design system];
    WM_CM --> WM_C[Choose controller]
    WM_F --> WM_G[Get pricing];
    WM_G --> WM_H[Build system];


    SENS_SEL -->|Capacitive| CAP_DESIGN[Design]
    SENS_SEL -->|Laser| LASER([Design])

    CAP_DESIGN --> COMM_DES[Design<br/>connections]
    CAP_DESIGN --> CAP_LEN[Decide wire<br/>length & quantity]
    CAP_DESIGN --> ELEC_DES[fit<br/>terminal strip]
    CAP_DESIGN --> HOLD_SOL[Decide<br/>holder solution]

    WM_C --> COMM_DES[Design<br/>connections]

    CAP_LEN --> TROUGH_DER[Derive<br/>trough length]
    
    TROUGH_DER --> PROCURE[Buy pipe,<br/>SS rod/wire, holder<br/>material, citric acid]
    ELEC_DES --> PROCURE
    HOLD_SOL --> PROCURE
    
    PROCURE --> CUT_PARTS[Cut trough<br/>& holders, leave<br/>rod path]
    
    CUT_PARTS --> GLUE_HOLD[Glue<br/>holders]
    
    GLUE_HOLD --> GET_VSRC[Get smart<br/>voltage source]
    GLUE_HOLD --> GET_H2O[Get<br/>pure water]
    
    GET_VSRC --> GND_ROD[Place ground<br/>SS rod & connect<br/>to source]
    GET_H2O --> GND_ROD
    
    GND_ROD --> WIRE_MOUNT[Mount<br/>wires on holders &<br/>connect to terminal]
    
    WIRE_MOUNT --> TERM_CONN[Connect<br/>terminal to source]
    
    TERM_CONN --> OBSERVE[Observe<br/>result]

    LASER --> COMM_DES
    LASER --> RANGE[Height range: 10-30mm]
    LASER --> SPOT[Spot diameter: 1-5mm]
    LASER --> VIB_RES[Stability in frequency range: 5-30Hz]
    LASER --> TRANS[Reflects well from water?]
    LASER --> SAMP[Verify sampling rate]
```

### Camera
1. Study camera software.
2. Measure width of container.
3. Order/build mount (including weight) + pitch axis + how to measure the pitch.
4. Verify camera screws fine to mount.

### Possible schedule clashes
I think there should be none. The gauge should be non-intrusive, but the assemble is very simple.

22/12
- Elena for OTP and printer access?
- Keys.
- For Aviv: change garbage? Where do we get tantalum?
- Call Yishay/Hanoch.


## daily

### daily note
- what was done
- what is to be done tomorrow

### git
Edit → Add → Commit → Push

This is your project backup workflow. All tracked files, including moved or renamed files, are preserved both locally and on GitHub.

1. Daily / session work
Edit files as needed (code, documentation, data notes).
Add new files or moved files to Git tracking:

    git add <file_or_folder>

or to add everything modified/untracked:

    git add .gitignore README.md docs project_env.sh   // ignore until we have a stable version

2. Commit changes
Commit logically grouped changes with a clear message:

    git commit [--amend] -m "Daily: [changes I've made]"

Commit at the end of each logical task or end-of-day. This keeps your history clean.

3. Push to GitHub
Upload local commits to the online backup:

    git push [--force-with-lease // if --amend was done.]

After this, your local repository and the remote repository are in sync.
GitHub now acts as a full backup of all tracked files and history.

4. Optional: Pull before starting work on another machine
If you work on multiple machines:

git pull

Ensures you have the latest state before editing.

5. Best practices

- Commit small, logical changes rather than massive, vague commits.
- Track only what matters (use .gitignore to skip temporary files, generated data, and .obsidian).
- Do not push large raw data files if they exceed GitHub limits; keep them local or use Git LFS.
Tag stable milestones (optional):

git tag v1.0
git push --tags
