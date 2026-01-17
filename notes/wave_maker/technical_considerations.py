import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell
def _():
    from os.path import join as join_path
    from IPython.display import display, HTML
    return HTML, display, join_path


@app.cell
def _():
    # paths
    path_figures = "figures"
    return (path_figures,)


@app.cell
def _(mo):
    mo.md(r"""
    # technical considerations
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### general knowledge

    typical 3D printer plastic mass density = 1e3 kg/m^3
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## physical requirements
    """)
    return


@app.cell
def _(HTML, display, join_path, path_figures):
    src_pv = join_path(path_figures, "wavemaker_peak_velocity.png")
    caption_pv = "wavemaker peak vertical velocity."

    display(HTML(f"""
    <figure id="fig:peak_velocity">
      <img src="{src_pv}" width="600">
      <figcaption><b>Figure 1.</b> {caption_pv}</figcaption>
    </figure>
    """))
    return


@app.cell
def _(HTML, display, join_path, path_figures):
    src_pa = join_path(path_figures, "wavemaker_peak_accelaration.png")
    caption_pa = "wavemaker peak vertical velocity."

    display(HTML(f"""
    <figure id="fig:peak_accelaration">
      <img src="{src_pa}" width="600">
      <figcaption><b>Figure 1.</b> {caption_pa}</figcaption>
    </figure>
    """))
    return


@app.cell
def _(mo):
    mo.md(r"""
    - Able to move at <=30Hz
    - Sustains required speeds (see <a href="#fig:peak_velocity">figure 1</a>)
    - Sustains required forces. The accelaration $a$ is given in
    <a href="#fig:peak_accelaration">figure 2</a> and the force is $m_{eff} \cdot a$.
    $m_{eff}$ should be less than $2kg$:
        - $m_{wedge} = W*L*H/2 \cdot \rho_{wedge} \approx 3.5e-5 m^3 \cdot 1e3 kg/m^3 = 35g$
        - $m_{}$
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Aquarium “Wiper” Wedge System (≤30 Hz)

    ## 1. Geometry & Mass (Inverted 30° Tip Wedge)

    | Parameter | Value | Notes / Error |
    |-----------|-------|---------------|
    | Wedge height (tip to base) | 2–6 cm | Tip meets water first |
    | Wedge width (y-axis) | 30 cm | Along platform |
    | Wedge length (x-axis, motion perpendicular) | 2–5 cm | Just enough to maintain shape |
    | Wedge mass | 0.18–0.25 kg | Plastic, ρ≈1000–1200 kg/m³ |
    | Rods + actuator piston + frame | 0.5–1 kg | Verify |
    | **Total moving mass** | 2 kg | Estimated by me |
    | Added mass (hydrodynamic) | 0.1–0.3 kg | Verify |

    **Total effective mass:** 2.1–2.3 kg

    ---

    ## 2. Kinematics (Sinusoidal Motion)

    $$
    x(t) = A \sin(\omega t),\quad v(t) = \omega A \cos(\omega t),\quad a(t) = \omega^2 A \sin(\omega t)
    $$

    | Parameter | Value | Notes |
    |-----------|-------|------|
    | Frequency | 1–30 Hz | Hard limit |
    | Stroke amplitude | ≤2 mm (30 Hz), ≤4 mm (10 Hz) |  |
    | Peak velocity | ≤0.34 m/s [high edge], ≤0.7 m/s [low edge] | From velocity plot |
    | Peak acceleration | ≤64 m/s² (≈6.5 g) | At 30 Hz |

    ---

    ## 3. Forces, Velocity & Power

    | Frequency | a_peak (m/s²) | F_peak (N) | v_peak (m/s) | P_peak (W) | Design Force (with drag margin ±20%) | T_peak (N·m) | Error ±50% |
    |-----------|---------------|------------|--------------|------------|---------------|-------------|-------------|
    | 15 Hz | 15.9 | 35 | 0.17 | 6 | ~42 N | 0.35 | 0.18–0.53 |
    | 30 Hz | 63.9 | 141 | 0.34 | 48 | ~170 N | 1.41 | 0.7–2.1 |

    - Hydrodynamic drag included in design force margin (~20%)
    - Peak force dominated by structural mass, added mass small due to sharp inverted tip
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Ordering
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Considerations overview

    - Make sure the motor can supply the physical requirements.
    - Verify that you get a driver, or that you know what driver to order in
    parallel.
    - Order/find a respective mounting bracket?
    - Estimate resonances, make sure they are not in the 1-50Hz range. This includes:
      - Mount bending/other resonances,
      - R-to-L system resonances, if relevant,
      - Wedge resonances.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### stepper option

    - disc
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### contacts

    #### Ilan&Gavish

    אלון    052-3254255 בעלים

    אור     052-3143300 הנדסה מכנית
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Height sensor

    ### Technical considerations
    1. Physical parameters:
        1. Sub-millimeter height sensitivity.
        2. 5-30mm height range (30mm is our 5Hz mode peak-to-peak distance).
        3. Beam width < ~5mm.
        4. Reflects well from water, sloped.
        5. Mechanical resonances?
    2. Electronics:
        1. Connectivity: output compatible with wave maker's controller.
        2. Sampling rate above 60Hz.

    ### Alternatives to capacitive gauge:
    1. LiDAR: Read paper. See if easy to construct.
    2. Triangulation:
       1. Verify that the product befits our slope measurement requirements.
       2. Show Aviv the quote from Yaron.
    3. Ultrasonic: wait for response from HTW and Baumer.
    4. Confocal: answer from TronSight.
    5. Slope measurement systems:
       1. Polarimetric slope sensing (PSS),
       2. Scanning laser slope gauge (SLSG).
    """)
    return


if __name__ == "__main__":
    app.run()
