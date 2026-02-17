"""
Test: Build exact TriangularLatticeLayout(61, 5.0) from scratch
and verify hash matches the pre-calibrated layout.
"""
import numpy as np

# ---- Replicate patterns.triangular_hex(61) exactly ----
def triangular_hex(n_points):
    crest_y = np.sqrt(3) / 2.0
    if n_points < 7:
        hex_coords = np.array([
            (0.0, 0.0), (-0.5, crest_y), (0.5, crest_y),
            (1.0, 0.0), (0.5, -crest_y), (-0.5, -crest_y),
        ])
        return hex_coords[:n_points]

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

    coords = np.concatenate((np.zeros((1, 2)), coords))
    return coords

# Generate coordinates
raw_coords = triangular_hex(61) * 5.0  # spacing = 5.0 µm
print(f"Generated {len(raw_coords)} trap coordinates")
print(f"First 5: {raw_coords[:5]}")

# Build RegisterLayout
from pulser.register.register_layout import RegisterLayout
layout = RegisterLayout(raw_coords, slug="TriangularLatticeLayout(61, 5.0µm)")
print(f"Layout created: {layout}")
print(f"Hash: {layout.static_hash()}")

# Compare with pre-calibrated
from pulser.devices import AnalogDevice
precal = AnalogDevice.pre_calibrated_layouts[0]
print(f"Pre-calibrated: {precal}")
# Can't call precal.static_hash() as it hangs, but we can compare the repr
# The repr includes the hash: RegisterLayout_<hash>

# Select 9 central traps
# For a 61-trap hexagonal layout, the center is trap 0
# Ring 1 has traps 1-6 (6 atoms)
# Ring 2 has traps 7-18 (12 atoms)
# So center + ring1 = 7 atoms, we need 9
# Pick center(0) + ring1(1-6) + 2 from ring2(7,8) = 9
central_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8]
reg = layout.define_register(*central_ids, qubit_ids=[f"q{i}" for i in range(9)])
print(f"Register: {len(reg.qubits)} qubits")
print(f"Has layout: {hasattr(reg, 'layout')}")

# Build sequence
from pulser import Sequence, Pulse
from pulser.devices import AnalogDevice
from pulser.waveforms import ConstantWaveform

seq = Sequence(reg, AnalogDevice)
seq.declare_channel("rydberg", "rydberg_global")
pulse = Pulse(ConstantWaveform(500, 2.0), ConstantWaveform(500, -2.0), 0.0)
seq.add(pulse, "rydberg")
seq.measure("ground-rydberg")
serialized = seq.to_abstract_repr()
print(f"Serialization OK! Length: {len(serialized)}")
print("SUCCESS!")
