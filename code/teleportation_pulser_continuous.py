"""
CFD Wormhole — Pasqal / Pulser Analog Simulation
=================================================
Maps the discrete-gate IonQ wormhole circuit to continuous
Rydberg-atom Hamiltonian evolution on a real Pasqal device.

Physical mapping
-----------------
  Coupling (entanglement)  →  Van der Waals interaction  C₆/R⁶
  CFD decoherence γ        →  Global laser detuning  Δ(γ)
  Scrambling (XX+YY+ZZ)    →  Global Rabi drive  Ω σₓ

Device constraints (AnalogDevice)
----------------------------------
  • 1 channel only: rydberg_global
  • min atom distance:  5 µm
  • max radial distance: 38 µm  (from centre of mass)
  • pulse duration: multiples of 4 ns, ≥ 16 ns
  • max |Δ|: 125.66 rad/µs,  max Ω: 12.57 rad/µs
"""

import numpy as np
from pulser import Sequence, Register, Pulse
from pulser.devices import AnalogDevice
from pulser.waveforms import ConstantWaveform
import matplotlib.pyplot as plt


# ============================================================================
# 1.  REGISTER  —  fits inside 38 µm radial envelope
# ============================================================================

from pulser.register.special_layouts import TriangularLatticeLayout

# ============================================================================
# 1.  REGISTER  —  fits inside 38 µm radial envelope
# ============================================================================

def build_wormhole_register(r_pair: float = 6.0, r_sep: float = 8.0, use_fresnel_layout: bool = False):
    """
    9 atoms: Message (M) + 4 Alice-Bob pairs.
    
    If use_fresnel_layout=True:
        Uses the hardware-enforced TriangularLatticeLayout (spacing=5µm).
        Selects 9 atoms in a compact cluster to ensure blockade connectivity.
        
    Else:
        Custom coordinates (M at origin, pairs along x-axis).
    """
    if use_fresnel_layout:
        # FRESNEL requires a register linked to a RegisterLayout.
        # We must REPLICATE exact coordinates of TriangularLatticeLayout(61, 5.0)
        # to match the device hash. "TriangularLatticeLayout" class hangs in 
        # Python 3.14 so we build it manually.
        from pulser.register.register_layout import RegisterLayout
        
        spacing = 5.0
        n_points = 61
        crest_y = np.sqrt(3) / 2.0
        
        # Logic from pulser.register._patterns.triangular_hex(61)
        layers = int((-3.0 + np.sqrt(9 + 12 * (n_points - 1))) / 6.0)
        points_left = n_points - 1 - (layers**2 + layers) * 3

        start_x = [-1.0, -0.5, 0.5, 1.0, 0.5, -0.5]
        start_y = [0.0, crest_y, crest_y, 0, -crest_y, -crest_y]
        delta_x = [0.5, 1.0, 0.5, -0.5, -1.0, -0.5]
        delta_y = [crest_y, 0.0, -crest_y, -crest_y, 0.0, crest_y]

        coords = np.array([
            (start_x[side] * layer + atom * delta_x[side],
             start_y[side] * layer + atom * delta_y[side])
            for layer in range(1, layers + 1)
            for side in range(6)
            for atom in range(1, layer + 1)
        ], dtype=float)

        if points_left > 0:
            layer = layers + 1
            min_atoms_per_side = points_left // 6
            points_left %= 6
            sides_order = [0, 3, 1, 4, 2, 5]
            coords2 = np.array([
                (start_x[side] * layer + atom * delta_x[side],
                 start_y[side] * layer + atom * delta_y[side])
                for side in range(6)
                for atom in range(1,
                    (min_atoms_per_side + 2 if points_left > sides_order[side]
                     else min_atoms_per_side + 1))
            ], dtype=float)
            coords = np.concatenate((coords, coords2))
            
        # Add center (0,0) at index 0
        coords = np.concatenate((np.zeros((1, 2)), coords))
        coords *= spacing

        # Create Layout with correct slug for hash
        layout = RegisterLayout(coords, slug=f"TriangularLatticeLayout({n_points}, {spacing}µm)")
        
        # Select 9 central atoms: Index 0 (center) + 1-6 (Ring 1) + 7-8 (Start of Ring 2)
        central_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        
        reg = layout.define_register(
            *central_ids,
            qubit_ids=[f"q{i}" for i in range(9)]
        )
        return reg

    # Custom Layout (EMU_FREE / EMU_SV)
    coords = []

    # Message qubit — close to A0
    coords.append([0.0, 0.0])

    for i in range(4):
        x = r_pair + i * r_sep          # horizontal offset
        coords.append([x,  r_pair / 2]) # Aᵢ  (above midline)
        coords.append([x, -r_pair / 2]) # Bᵢ  (below midline)

    arr = np.array(coords)

    # Centre the register so max radial distance stays ≤ 38 µm
    arr -= arr.mean(axis=0)

    return Register.from_coordinates(arr, prefix="q")


# ============================================================================
# 2.  SEQUENCE BUILDER
# ============================================================================

def build_wormhole_sequence(gamma: float, coupling_time: int = 500, use_fresnel_layout: bool = False):
    """
    Build a Pulser ``Sequence`` compatible with **AnalogDevice**.

    Parameters
    ----------
    gamma : float
        CFD decoherence parameter (0 → vacuum, ≥ 0.535 → collapse).
        Mapped linearly to global detuning Δ.
    coupling_time : int
        Duration of the Hamiltonian evolution pulse in **ns**.
        Must be a multiple of 4 and ≥ 16.
    use_fresnel_layout : bool
        If True, uses TriangularLatticeLayout for FRESNEL compatibility.
    """
    # --- enforce clock-period constraint ---
    coupling_time = max(16, int(round(coupling_time / 4)) * 4)

    reg = build_wormhole_register(use_fresnel_layout=use_fresnel_layout)
    seq = Sequence(reg, AnalogDevice)

    # Single global channel (the only one AnalogDevice exposes)
    seq.declare_channel("rydberg", "rydberg_global")

    # --- Rabi amplitude  (drive the "scrambling") ---
    omega = 2.0          # rad/µs  (well below 12.57 limit)

    # --- Detuning encodes the CFD field ---
    delta_max = 40.0     # rad/µs  (well below 125.6 limit)
    delta = -gamma * delta_max   # negative Δ → suppresses Rydberg excitation

    amp_wf = ConstantWaveform(coupling_time, omega)
    det_wf = ConstantWaveform(coupling_time, delta)

    pulse = Pulse(amplitude=amp_wf, detuning=det_wf, phase=0.0)
    seq.add(pulse, "rydberg")

    # --- Measurement (MANDATORY for remote backends) ---
    # The EMU-TN / QPU backend requires an explicit measurement declaration.
    # The local QutipEmulator can sample without it, but to_abstract_repr()
    # will omit the measurement field, causing a "field required" rejection.
    seq.measure("ground-rydberg")

    return seq


# ============================================================================
# 3.  LOCAL SIMULATION  (QuTiP emulator, for validation)
# ============================================================================

def run_simulation(gamma_values=None):
    """Run a local sweep and print mean Rydberg density per γ."""
    from pulser_simulation import QutipEmulator

    if gamma_values is None:
        gamma_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.535, 0.8]

    print("\n--- CFD Wormhole · Analog Simulation (AnalogDevice) ---")
    print(f"{'γ':<8} | {'⟨n⟩  (mean Rydberg density)':<35}")
    print("-" * 50)

    results = {}

    for g in gamma_values:
        seq = build_wormhole_sequence(gamma=g, coupling_time=500)

        sim = QutipEmulator.from_sequence(seq)
        res = sim.run()

        # Mean Rydberg density as traversability proxy
        sampling = res.sample_final_state(N_samples=1000)
        avg_exc = sum(
            bs.count("1") / len(bs) * n for bs, n in sampling.items()
        ) / 1000

        results[g] = avg_exc
        print(f"{g:<8.3f} | {avg_exc:.4f}")

    return results


if __name__ == "__main__":
    run_simulation()
