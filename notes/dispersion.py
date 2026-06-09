"""
dispersion.py
=============
Dispersion relation for gravity-capillary surface waves on a viscous,
incompressible fluid with a viscoelastic surfactant film and a diffusing
bulk pollutant.

Physical setup
--------------
  rho   : fluid density                          [kg/m³]
  nu    : kinematic viscosity                    [m²/s]
  g     : gravitational acceleration             [m/s²]
  sig0  : clean surface tension                  [N/m]
  sig   : polluted surface tension               [N/m]
  H     : tank depth                             [m]
  k_e   : dilatational elasticity                [N/m]
  D     : bulk diffusivity                       [m²/s]
  kappa : surface-bulk partition slope ∂_{c0}s0  [m]

3×3 linear system  M · [A_p, B_p, Ã]ᵀ = 0
-------------------------------------------
Fourier-transformed in x,y; Ã := (κ/s₀) A_{δc}.

  Eq 0 — tangential / Marangoni stress:
    (-2 cosh(kH) + (1+r²) cosh(aH)) A_p
  + (-2r sinh(kH) + (1+r²) sinh(aH)) B_p
  - E(w)/(ik·ρν) · cosh(bH) · Ã  =  0

  Eq 1 — normal stress / gravity-capillary:
    [P sinh(kH) - Q cosh(aH)] A_p
  + [P·r cosh(kH) - Q sinh(aH)] B_p  =  0     (no Ã term)

  Eq 2 — concentration flux:
    (sinh(kH) - r sinh(aH)) A_p
  + r(cosh(kH) - cosh(aH)) B_p
  + [i(D/κ)·b·sinh(bH) + w·cosh(bH)] / k² · Ã  =  0

Notation:
  a = sqrt(k² + iw/ν),  Re(a) > 0   viscous penetration wavenumber
  b = sqrt(k² + iw/D),  Re(b) > 0   diffusive penetration wavenumber
  r = a/k
  P = 2ρν w/(T₀k) + i(1 + 2ρg/(T₀k²)) - iρw²/(T₀k³)
  Q = 2ρν r w/(T₀k) + i(1 + 2ρg/(T₀k²))

Numerical strategy
------------------
For seismic/capillary frequencies, Re(a·H) can reach O(10²–10³) and
Re(b·H) can reach O(10³–10⁴), causing raw cosh/sinh to overflow.

We compute scaled versions
    cosh_s(z) := cosh(z) · exp(−Re z),   sinh_s(z) := sinh(z) · exp(−Re z)
which are O(1) for all Re(z) ≥ 0, then scale columns 0,1 (A_p, B_p) by
exp(Re(aH)) and column 2 (Ã) by exp(Re(bH)).

The gc-branch dispersion condition is extracted as the 2×2 minor

    Δ(w,k) := M₀₀ M₁₁ − M₀₁ M₁₀                       (*)

of the column-scaled matrix (before row normalisation and pivot).  This
minor is O(1) everywhere and has a clean zero exactly on the
gravity-capillary branch.

Why not the full 3×3 det?
  When the Marangoni coupling is weak (small k_e or small D), col 2 of
  the row-normalised matrix is nearly zero, making det(M₃ₓ₃) ≈ 0 everywhere
  to floating-point — a flat, uninformative landscape.  The minor (*) avoids
  this by bypassing the Ã column entirely.  The Marangoni correction to the
  gc branch is second-order in the coupling strength and can be recovered
  perturbatively if needed.

Root finding
------------
For each k:
  1. Primary:  fresh gc seeds (w_gc, −ε·w_gc), ε ∈ {1e-3, 1e-4, 5e-4, 1e-2},
     using Δ(w,k) = 0 as the residual.
  2. Continuation: previous k's gc root as additional seed (tried after fresh seeds).
  3. A root is accepted only if Re(w)/w_gc ∈ [0.8, 1.2] and Im(w) ≤ 1e-3|Re(w)|.

Notes
-----
The algorithm solves for decaying waves (im(w)>0, real wave vectors). This is a 
deliberate choice, since these modes form the correct basis for the expansion of
the response to rigid shaking.
"""

# os
import os
import sys
import yaml
from os.path import join as join_path

# Computations
import numpy as np
import scipy as sp
import sympy as smp
from numpy.linalg import det, slogdet
from scipy.optimize import fsolve

# Science
import CoolProp.CoolProp as CP

# Plotting
import matplotlib.pyplot as plt
import seaborn as sns

# Data handling
import pandas as pd
from pathlib import Path
import logging

import warnings
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Default physical parameters (SI)
# ---------------------------------------------------------------------------
pi = np.pi
g0 = sp.constants.g     # At sea level
p0 = sp.constants.atm   # At sea level
T_room = 290            # ~ Israeli winter temperature in Kelvin
seasurface_density = CP.PropsSI('D', 'T', T_room, 'P', p0, 'Water')
viscosity = CP.PropsSI('VISCOSITY', 'T', T_room, 'P', p0, 'Water')  # Pa.s
kinematic_viscosity = viscosity / seasurface_density
seawater_surface_tension = 0.074  # N/m, estimate for seawater, +-0.001


DEFAULT_PARAMS = dict(
    rho   = seasurface_density,   # kg/m³
    nu    = kinematic_viscosity,     # m²/s
    g     = sp.constants.g,     # m/s², At sea level
    sig0    = seawater_surface_tension,    # N/m
    delsig = 0.005,
    H     = 0.20,     # m       
    k_e   = 2e-2,     # N/m
    D     = 1e-9,     # m²/s
    kappa = 1e-4,     # m, D, kappa should be typical for sea surfactants
)
DEFAULT_PARAMS['sig'] = DEFAULT_PARAMS['sig0'] - DEFAULT_PARAMS['delsig']

# other constants
EXP_CUTOFF = 36     # machine precision

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sqrt_rp(z):
    """Complex square root with Re > 0 branch (scalar)."""
    s = np.sqrt(complex(z))
    return -s if s.real < 0 else s


def _w_gc(k, rho, g, sig, H):
    """Inviscid gravity-capillary angular frequency."""
    return float(np.sqrt((g*k + sig*k**3/rho) * np.tanh(k*H)))

def _gc_root(roots):
    """Pick the forward-propagating gc branch: Re(ω) > 0, Im(ω) < 0."""
    for w in roots:
        if np.isfinite(w) and w.real > 0 and w.imag <= 0:
            return w
    return None


def setup_logging(session_dir, debug_mode=False):
    log_path = session_dir / "session.log"
    logging.basicConfig(
        level=(logging.DEBUG if debug_mode else logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger("transfer")

# ---------------------------------------------------------------------------
# Dispersion relation, finite depth
# ---------------------------------------------------------------------------
def E_modulus(omega, k, params):
    """Effective complex dilatational modulus E(omega).  Convention: dt -> -i*omega.
    p['E_model']:
      'gibbs'    -> E = k_e                       (real; insoluble elastic limit)
      'two_step' -> diffusional (LvdT, step 1) x [elastic + structural Maxwell (step 2)]
      'custom'   -> p['E_func'](omega, k, p)
    """
    model = params.get('E_model', 'gibbs')

    if model == 'gibbs':
        return params['k_e'] + 0j

    if model == 'custom':
        return params['E_func'](omega, k, params)

    raise ValueError(f"unknown E_model {model!r}")


def det_dispersion(w, k, params):
    """
    Dispersion relation determinant for viscous capillary-gravity waves
    with soluble surfactant, computed up to a global complex prefactor.
    Based on the analysis in seismic_transfer_function.lyx file.
 
    Two overall factors of e^{-kH} have been divided out.
    All remaining exponentials are decaying.
 
    Parameters
    ----------
    omega : complex  - angular frequency
    k     : float    - wavenumber magnitude
    H     : float    - fluid depth
    rho   : float    - fluid density
    nu    : float    - kinematic viscosity
    g     : float    - gravitational acceleration
    sig   : float    - equilibrium surface tension
    D     : float    - bulk diffusivity
    kappa : float    - surface/bulk partition length
    k_e   : float    - Gibbs elasticity (= d sigma / d ln Gamma)
    k_v   : float    - surfactant internal viscosity
    """
    w = complex(w)
    rho = params['rho'];  nu = params['nu'];      sig = params['sig'];
    g   = params['g'];    H = params['H']
    D = params['D'];      kappa = params['kappa']
    k_e = params['k_e'];  k_v = params['k_v']

    # Eigenvalues (with convention partial_t -> -i omega)
    a = _sqrt_rp(k**2 - 1j * w / nu)
    b = _sqrt_rp(k**2 - 1j * w / D)
 
    # Physical frequency/rate scales
    r = a / k
    gamma_d = D * b / kappa         # diffusive frequency
    gamma_c = sig * k / (rho * nu)   # capillary-viscous decay rate
    w_cp_sq = sig * k**3 / rho       # capillary frequency squared
    w0_sq = g * k + w_cp_sq        # gravity-capillary frequency squared
    
    # Decaying exponentials (all <= 1 in magnitude)
    e_2k = np.exp(-2 * H * k)      if np.real(2 * H * k)          < EXP_CUTOFF else 0.0
    e_ak = np.exp(-H * (a + k)) if np.real(H * (a + k))   < EXP_CUTOFF else 0.0
    e_2a = np.exp(-2 * H * a)   if np.real(2 * H * a)     < EXP_CUTOFF else 0.0
    e_2ak = np.exp(-2 * H * (a + k)) if np.real(2 * H * (a + k)) < EXP_CUTOFF else 0.0

    # Nice shorthands
    rsq = r**2
    w_sq = w**2

    # ------------------------------------------------------------------
    # TxN (tangential stress x normal stress) cross product
    # ------------------------------------------------------------------
    # Bracket appearing in 4 of the 5 terms:
    # B_pm(s) = (r^2+1)*w^2 + s*(r^2-1)*w0^2  (s = +1 or -1)
    B_minus = (rsq + 1) * w_sq - (rsq - 1) * w0_sq    # s = -1
    B_plus  = (rsq + 1) * w_sq + (rsq - 1) * w0_sq    # s = +1
 
    TxN_0   =  0.5 * (r - 1) * (B_minus / w_cp_sq + 2j * (r - 1)**2 * w / gamma_c)
    TxN_2k  =  0.5 * (r + 1) * (B_plus  / w_cp_sq + 2j * (r + 1)**2 * w / gamma_c)
    TxN_ak  = -4 * r * (1j * (rsq + 3) * w / gamma_c + w_sq / w_cp_sq)
    TxN_2a  =  0.5 * (r + 1) * (B_minus / w_cp_sq + 2j * (r + 1)**2 * w / gamma_c)
    TxN_2ak =  0.5 * (r - 1) * (B_plus  / w_cp_sq + 2j * (r - 1)**2 * w / gamma_c)
 
    TxN = (
        TxN_0
        + TxN_2k  * e_2k
        + TxN_ak  * e_ak
        + TxN_2a  * e_2a
        + TxN_2ak * e_2ak
    )

    # Explicit inviscid limit
    if (k_e == 0):      # Assume nonsense in case that k_e == 0 and k_v != 0.
        return TxN
    
    # Internal viscosity
    gamma_l = np.inf if k_v == 0 else k_e / k_v
    visc    = 1 - 1j * w / gamma_l 

    # Marangoni wavenumber (frequency-dependent)
    E_tilde = k_e / (rho * nu * D)
 
    # Coupling prefactors (concentration column of rows 1 and 3) 
    e_2b = np.exp(-2 * H * b) if np.real(2 * H * b) < EXP_CUTOFF else 0.0
 
    surf_stress = (E_tilde / k) * (1 + e_2b)
    surf_flux   = 2 * (gamma_d * (1 - e_2b) - 1j * w * (1 + e_2b)) / (D * k**2)
 
    # ------------------------------------------------------------------
    # NxF (normal stress x flux) cross product
    # Overall structure: 1/omega_cp^2 * [...]
    # ------------------------------------------------------------------ 
    NxF_0   =  (r - 1) * (r * w_sq - (r - 1) * w0_sq)
    NxF_2k  =  (r + 1) * (r * w_sq + (r + 1) * w0_sq)
    NxF_ak  = -8 * r * w0_sq
    NxF_2a  = -(r + 1) * (r * w_sq - (r + 1) * w0_sq)
    NxF_2ak = -(r - 1) * (r * w_sq + (r - 1) * w0_sq)
 
    NxF = (1 / w_cp_sq) * (
        NxF_0
        + NxF_2k  * e_2k
        + NxF_ak  * e_ak
        + NxF_2a  * e_2a
        + NxF_2ak * e_2ak
    )
 
    # ------------------------------------------------------------------
    # Full determinant
    # Result from the seismic_transfer_function file was multiplied by -1 for 
    # convenience.
    # ------------------------------------------------------------------
    return surf_stress * visc * NxF + surf_flux * TxN


# ---------------------------------------------------------------------------
# Dispersion relation, deep water
# ---------------------------------------------------------------------------
def det_dispersion_deep(w, k, params):
    """
    Deep-container (H -> infinity) limit of det_dispersion for viscous
    capillary-gravity waves with soluble surfactant. All exponential terms
    in the full expression have decayed; only the exponent-free terms remain.

    Shares zeros as det_dispersion in the H -> infinity limit, differs by a
    (w, k)-dependent prefactor.

    Parameters
    ----------
    w     : complex  - angular frequency
    k     : float    - wavenumber magnitude
    params: dict     - keys rho, nu, g, sig, D, kappa, k_e
    """
    w = complex(w)
    rho = params['rho'];  nu = params['nu'];     sig = params['sig']
    g   = params['g']
    D   = params['D'];    kappa = params['kappa']
    k_e = params['k_e'];  k_v = params['k_v']

    # Eigenvalues (convention partial_t -> -i omega)
    a = _sqrt_rp(k**2 - 1j * w / nu)
    b = _sqrt_rp(k**2 - 1j * w / D)

    # Physical frequency/rate scales
    r        = a / k
    gamma_d  = D * b / kappa            # surface-bulk diffusive exchange rate
    gamma_nu = nu * k**2                # bulk vorticity decay rate
    w0_sq    = g * k + sig * k**3 / rho  # gravity-capillary frequency squared

    rsq  = r**2;    w_sq = w**2

    # ------------------------------------------------------------------
    # T x N cross product: clean-water bracket (only exponent-free term)
    # ------------------------------------------------------------------
    TxN = (rsq + 1) * w_sq + 2j * (r - 1)**2 * gamma_nu * w - (rsq - 1) * w0_sq

    # Explicit clean-surface (no surfactant) limit
    if k_e == 0:
        return TxN

    # ------------------------------------------------------------------
    # N x F cross product: elastic-surfactant bracket (only exponent-free term)
    # ------------------------------------------------------------------
    NxF = r * w_sq - (r - 1) * w0_sq

    # Coupling prefactors (deep-limit reductions of surf_stress, surf_flux)
    # Ma(w) = (gamma_e/gamma_d) -- Marangoni number;
    # computed as k_e * k * kappa / (rho*nu*D*b).
    Ma   = k_e * k * kappa / (rho * nu * D * b)
    gamma_l = np.inf if k_v == 0 else k_e / k_v
    visc    = 1 - 1j * w / gamma_l
    diff = 1 - 1j * w / gamma_d         # diffusive surface-bulk exchange factor
    # print(f"ke = {k_e}\nMa * NxF = {Ma * NxF}\ndiff * TxN = {diff * TxN}\n")
    return Ma * visc * NxF + diff * TxN


def inviscid_guess(k, params):
    """
    Inviscid gravity-capillary frequency: w0^2 = (g*k + sig*k^3/rho) * tanh(k*H).
    Returns (w0, -w0) as starting guesses for the two propagating branches.
    """
    g = params['g']; sig = params['sig']; H = params['H']; nu = params['nu']
    rho = params['rho']
    w0_sq = (g * k + sig * k**3 / rho) * np.tanh(k * H)
    w0 = np.sqrt(w0_sq)
    gamma = 2 * nu * k**2  # leading-order viscous damping
    return [w0 - 1j * gamma, -w0 - 1j * gamma]

 
def find_roots_newton(k, params, guesses=None, tol=1e-12, max_iter=200, mode=None):
    """
    Find roots of det_dispersion(w, k, params) = 0 using Newton's method.
 
    Parameters
    ----------
    k       : float - wavenumber
    params  : dict  - physical parameters
    guesses : list of complex, optional - initial guesses for omega.
              If None, uses inviscid_guess.
    tol     : float - convergence tolerance (relative)
    max_iter: int   - maximum iterations
 
    Returns
    -------
    roots : list of complex - converged roots

    """
    if mode == 'deep':
        det = det_dispersion_deep
    else:
        det = det_dispersion

    if guesses is None:
        guesses = inviscid_guess(k, params)

    cutoff = 1e-14
    dl = 1e-8       # finite difference step (relative)
    roots = []
    f = None
    ftag = None

    for w0 in guesses:
        w = complex(w0)
        for it in range(max_iter):
            f = det(w, k, params)
            if abs(f) < 1e-300:
                break
            # Numerical derivative
            dw = max(abs(w) * dl, cutoff)
            ftag = (det(w + dw, k, params) - f) / dw
            w_new = w - f / ftag
            if abs(w_new - w) < tol * max(abs(w_new), cutoff):
                w = w_new
                # print(f"iter = {it}, abs(w_new - w) = {abs(w_new - w)}")
                break
            w = w_new
        roots.append(w)
        # print(f"w = {w}\ndet = {f}\n")
 
    return roots
 
 
def find_roots_contour(k, params, center, radius_re, radius_im, N_quad=256):
    """
    Find all roots of det_dispersion inside an elliptical contour
    using the argument principle (Delves-Lyness method).
 
    Parameters
    ----------
    k         : float   - wavenumber
    params    : dict    - physical parameters
    center    : complex - center of search ellipse
    radius_re : float   - real half-width
    radius_im : float   - imaginary half-width
    N_quad    : int     - number of quadrature points on contour
 
    Returns
    -------
    roots : list of complex - roots found inside the contour,
            polished with Newton's method
    """
    # Parameterize ellipse: w(t) = center + radius_re*cos(t) + i*radius_im*sin(t)
    t = np.linspace(0, 2 * np.pi, N_quad, endpoint=False)
    dt = 2 * np.pi / N_quad
 
    z = center + radius_re * np.cos(t) + 1j * radius_im * np.sin(t)
    dz = -radius_re * np.sin(t) + 1j * radius_im * np.cos(t)
 
    # Evaluate f and f' on contour
    f_vals = np.array([det_dispersion(zi, k, params) for zi in z])
 
    # Numerical derivative of det_dispersion w.r.t. omega
    eps = 1e-8
    fp_vals = np.array([
        (det_dispersion(zi + eps * max(abs(zi), 1e-10), k, params) - fi)
        / (eps * max(abs(zi), 1e-10))
        for zi, fi in zip(z, f_vals)
    ])
 
    # Argument principle integrals: s_n = (1/2pi i) * oint w^n * f'/f dw
    integrand_base = fp_vals / f_vals * dz * dt
 
    s0 = np.sum(integrand_base) / (2j * np.pi)            # number of roots
    s1 = np.sum(z * integrand_base) / (2j * np.pi)        # sum of roots
    s2 = np.sum(z**2 * integrand_base) / (2j * np.pi)     # sum of roots squared
 
    n_roots = int(np.round(s0.real))
 
    if n_roots == 0:
        return []
 
    if n_roots == 1:
        guesses = [s1 / s0]
    elif n_roots == 2:
        # Roots are solutions of x^2 - (s1/s0)*x + (s1^2 - s2)/(2*s0) = 0
        # Using Newton sums: p1 = s1/s0, p2 = ((s1/s0)^2 - s2/s0) / 2
        mean = s1 / s0
        # s2/s0 = w1^2 + w2^2, s1/s0 = w1 + w2
        # w1*w2 = ((w1+w2)^2 - (w1^2+w2^2)) / 2 = ((s1/s0)^2 - s2/s0) / 2
        prod = ((s1 / s0)**2 - s2 / s0) / 2
        disc = mean**2 - 4 * prod
        sq = np.sqrt(disc)
        guesses = [(mean + sq) / 2, (mean - sq) / 2]
    else:
        # For more roots, use Newton sums to build companion matrix
        # or just use evenly-spaced guesses inside the contour
        guesses = [s1 / s0]  # at least get the centroid
        angles = np.linspace(0, 2 * np.pi, n_roots, endpoint=False)
        r_guess = 0.5  # fraction of radius
        for ang in angles:
            guesses.append(center + r_guess * radius_re * np.cos(ang)
                          + 1j * r_guess * radius_im * np.sin(ang))
 
    # Polish with Newton
    return find_roots_newton(k, params, guesses=guesses)
 
 
def dispersion_curve(k_array, params, tol=1e-12, continuate=True, method='newton', mode=None):
    """
    Compute the dispersion relation w(k) for an array of wavenumbers.
 
    Parameters
    ----------
    k_array : array of float - wavenumbers
    params  : dict - physical parameters
    method  : str  - 'newton' or 'contour'
 
    Returns
    -------
    roots : array of shape (len(k_array), n_branches) - complex frequencies
    """
    # print(f"mode = {mode}")

    all_roots = []
    prev_roots = None
 
    for i, k in enumerate(k_array):
        if method == 'newton':
            if prev_roots is not None:
                guesses = prev_roots  # continuation from previous k
            else:
                guesses = inviscid_guess(k, params)
            roots = find_roots_newton(k, params, guesses=guesses, tol=tol, mode=mode)
        elif method == 'contour':
            w0 = np.sqrt((params['g'] * k + params['sig'] * k**3 / params['rho'])
                         * np.tanh(k * params['H']))
            gamma = 2 * params['nu'] * k**2
            roots = find_roots_contour(k, params,
                                       center=-1j * gamma,
                                       radius_re=2 * w0 + 1,
                                       radius_im=5 * gamma + 1)
        else:
            raise ValueError(f"Unknown method: {method}")
 
        all_roots.append(roots)
        
        if continuate:
            prev_roots = roots
 
    return all_roots

# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------

def run_sanity_checks(params=None):
    """
    Check 1 — inviscid limit:
      k_e = 0, ν → 0 : Re(ω)/ω_gc should equal 1 to ≲ 1 ppm.

    Check 2 — viscous damping scaling:
      With the −iω convention, decaying waves have Im(ω) < 0, so the
      damping rate is −Im(ω).  In the deep-water limit (Lamb 1932) this
      should scale as 2ν k².  The full viscous finite-depth system gives
      a slightly different coefficient, but the k² trend should be clear.

    Check 3 — surface tension limit:
      For large k, the dispersion should approach the capillary wave
      limit ω ~ sqrt(sig/rho) · k^(3/2).
    """
    if params is None:
        params = DEFAULT_PARAMS

    rho = params['rho']
    g = params['g']
    sig = params['sig']
    H = params['H']
    k_test = np.array([1e0, 2e0, 5e0, 2e1, 5e1, 1e2, 2e2, 1e3])

    print("=" * 64)
    print("Check 1: inviscid limit  (k_e=, ν=1e-10)")
    p = dict(params, k_e=0.0, nu=1e-10)
    all_roots = dispersion_curve(k_test, p, continuate=False)
    w_gc = np.array([_w_gc(k, rho, g, sig, H) for k in k_test])
    print(f"  {'k':>8}  {'ω_gc':>12}  {'Re(ω)':>12}  {'Re(ω)/ω_gc':>12}")
    for k, wgc, roots in zip(k_test, w_gc, all_roots):
        w = _gc_root(roots)
        if w is not None:
            tag = "  ✓" if abs(w.real / wgc - 1) < 1e-5 else "  ✗"
            print(f"  {k:8.1f}  {wgc:12.5f}  {w.real:12.5f}  {w.real/wgc:12.7f}{tag}")
        else:
            print(f"  {k:8.1f}  {wgc:12.5f}  {'no root':>12}  {'':>12}  ✗")

    print()
    print("Check 2: viscous damping  (k_e=0, default ν)")
    p = dict(params, k_e=0.0)
    all_roots = dispersion_curve(k_test, p, continuate=False)
    print(f"  {'k':>8}  {'−Im(ω)':>14}  {'2νk²':>14}  {'ratio':>8}")
    for k, roots in zip(k_test, all_roots):
        w = _gc_root(roots)
        if w is not None:
            lamb  = 2.0 * p['nu'] * k**2
            ratio = -w.imag / lamb
            print(f"  {k:8.1f}  {-w.imag:14.6e}  {lamb:14.6e}  {ratio:8.3f}")
        else:
            print(f"  {k:8.1f}  {'no root':>14}")

    print()
    print("Check 3: capillary limit  (large k, g→0, deep water H=10)")
    p = dict(params, k_e=0.0, g=0.0, H=10.0)
    k_cap = np.array([50., 100., 200., 500.])
    all_roots = dispersion_curve(k_cap, p, continuate=False)
    w_cap = np.sqrt(sig / rho) * k_cap**1.5
    print(f"  {'k':>8}  {'ω_cap':>12}  {'Re(ω)':>12}  {'Re(ω)/ω_cap':>12}")
    for k, wc, roots in zip(k_cap, w_cap, all_roots):
        w = _gc_root(roots)
        if w is not None:
            tag = "  ✓" if abs(w.real / wc - 1) < 0.01 else "  ✗"
            print(f"  {k:8.1f}  {wc:12.5f}  {w.real:12.5f}  {w.real/wc:12.7f}{tag}")
        else:
            print(f"  {k:8.1f}  {wc:12.5f}  {'no root':>12}  {'':>12}  ✗")

    print("=" * 64)
    
# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
# Plotting
sns.set_theme()
plt.rcParams['text.usetex'] = True

# Logging
np.set_printoptions(threshold=np.iinfo(np.intp).max)  # Show all elements
np.set_printoptions(linewidth=80)    # Optional: avoid line breaks

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == '__main__':

    run_sanity_checks(DEFAULT_PARAMS)
    print()

    # k_values = np.linspace(2.0, 150.0, 80)
    # print("Solving dispersion relation ...")
    # omegas = find_omegas(k_values, params=DEFAULT_PARAMS, verbose=False)

    # n_found = sum(1 for r in omegas if np.isfinite(r[0]))
    # print(f"Roots found: {n_found}/{len(k_values)}\n")

    # print(f"  {'k [m⁻¹]':>10}  {'Re(ω) [rad/s]':>16}  {'Im(ω) [rad/s]':>16}  {'Re/ω_gc':>10}")
    # rho,g,sig,H = DEFAULT_PARAMS['rho'],DEFAULT_PARAMS['g'],DEFAULT_PARAMS['sig'],DEFAULT_PARAMS['H']
    # for k, roots in zip(k_values[::10], omegas[::10]):
    #     wgc = _w_gc(k,rho,g,sig,H)
    #     if np.isfinite(roots[0]):
    #         print(f"  {k:10.3f}  {roots[0].real:16.5f}  {roots[0].imag:16.7f}  {roots[0].real/wgc:10.6f}")
    #     else:
    #         print(f"  {k:10.3f}  {'no root':>16}")

    # plot_dispersion(k_values, omegas, params=DEFAULT_PARAMS,
    #                 save_path='/mnt/user-data/outputs/dispersion_relation.png')
