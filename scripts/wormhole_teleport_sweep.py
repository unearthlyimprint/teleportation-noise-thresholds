"""
Corrected Wormhole Traversability Protocol
==========================================
Author: Celal Arda
Date: February 2026
Framework: Coherence Field Dynamics (CFD)

PURPOSE:
  Test whether quantum information traverses an entanglement bridge
  (wormhole analog) under controlled decoherence.

THE CRITICAL CORRECTION:
  Standard quantum teleportation requires classical post-processing
  of Bell measurement outcomes. The previous implementation omitted
  this step, producing random output regardless of noise level.
  
  Correction rules (for Z-basis measurement at Bob):
    Bell(q0,q1) = 00: Bob is correct as-is
    Bell(q0,q1) = 01: flip Bob (X correction)  
    Bell(q0,q1) = 10: Bob is correct (Z doesn't affect Z-measurement)
    Bell(q0,q1) = 11: flip Bob (X correction, Z irrelevant)
  Summary: if q1=1, flip Bob's outcome.

EXPERIMENTS:
  Part 1: Noiseless baseline (F should be 1.0)
  Part 2: Decoherence sweep γ ∈ [0, 1] connecting to CFD theory
  Part 3: Hardware-ready circuit (prints circuit for Azure deployment)
  
BENCHMARK:
  Classical teleportation bound: F_classical = 2/3 ≈ 0.667
  If F > 0.667: quantum channel is operational (wormhole traversable)
  If F ≈ 0.5: total decoherence (wormhole collapsed)
"""

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile

# ============================================================================
# BACKEND
# ============================================================================
try:
    from qiskit.providers.basic_provider import BasicProvider
    backend = BasicProvider().get_backend('basic_simulator')
except ImportError:
    try:
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
    except ImportError:
        from qiskit import Aer
        backend = Aer.get_backend('aer_simulator')

print(f"Backend: {backend.name}")

SHOTS = 4000

# ============================================================================
# CIRCUIT BUILDER
# ============================================================================
def build_teleport_circuit(message='0', decoherence_gamma=0.0):
    """
    Build a 3-qubit teleportation circuit with optional phase damping.
    
    q0 = Message qubit
    q1 = Alice (half of Bell pair / boundary A)
    q2 = Bob   (half of Bell pair / boundary B)
    
    Phase damping is applied via Rz rotations that simulate
    dephasing: Rz(gamma * pi * random_phase) on each qubit
    after the Bell pair creation. This models the CFD decoherence
    parameter gamma.
    
    Args:
        message: '0' or '1'
        decoherence_gamma: float in [0, 1], CFD noise parameter
    """
    qr = QuantumRegister(3, 'q')
    cr = ClassicalRegister(3, 'c')
    qc = QuantumCircuit(qr, cr)
    
    # 1. Prepare message
    if message == '1':
        qc.x(qr[0])
    
    # 2. Create Bell pair (ER bridge)
    qc.h(qr[1])
    qc.cx(qr[1], qr[2])
    
    # 3. Apply CFD decoherence (phase damping model)
    # Random Z-rotations scaled by gamma simulate dephasing
    if decoherence_gamma > 0:
        rng = np.random.default_rng()
        for q in range(3):
            angle = decoherence_gamma * np.pi * rng.uniform(-1, 1)
            qc.rz(angle, qr[q])
    
    # 4. Bell measurement (message + Alice)
    qc.cx(qr[0], qr[1])
    qc.h(qr[0])
    
    # 5. Measure everything
    qc.measure(qr[0], cr[0])
    qc.measure(qr[1], cr[1])
    qc.measure(qr[2], cr[2])
    
    return qc


# ============================================================================
# POST-PROCESSING
# ============================================================================
def compute_fidelity(counts, expected_bob):
    """
    Apply classical teleportation corrections and compute fidelity.
    
    Qiskit bitstring ordering: 'c[2] c[1] c[0]' (MSB first)
      c[0] = q0 (message Bell bit)
      c[1] = q1 (Alice Bell bit)  
      c[2] = q2 (Bob output)
    
    Correction rule: if c[1]=1, flip c[2].
    Then check if corrected c[2] matches expected_bob.
    """
    total = sum(counts.values())
    correct = 0
    
    for bitstring, count in counts.items():
        bits = bitstring.replace(' ', '')
        bob_raw = int(bits[0])    # c[2]
        alice = int(bits[1])      # c[1]
        
        # Apply X correction if Alice measured 1
        bob_corrected = (1 - bob_raw) if alice == 1 else bob_raw
        
        if bob_corrected == expected_bob:
            correct += count
    
    return correct / total


# ============================================================================
# PART 1: NOISELESS BASELINE
# ============================================================================
print("\n" + "=" * 60)
print("PART 1: NOISELESS BASELINE")
print("=" * 60)

for msg in ['0', '1']:
    qc = build_teleport_circuit(message=msg, decoherence_gamma=0.0)
    qc_t = transpile(qc, backend)
    job = backend.run(qc_t, shots=SHOTS)
    counts = job.result().get_counts()
    f = compute_fidelity(counts, int(msg))
    print(f"  Send |{msg}> : F = {f:.4f}  (raw counts: {counts})")

print("  Expected: F = 1.0000 for noiseless teleportation")


# ============================================================================
# PART 2: DECOHERENCE SWEEP (CFD gamma parameter)
# ============================================================================
print("\n" + "=" * 60)
print("PART 2: DECOHERENCE SWEEP (gamma = 0.0 to 1.0)")
print("=" * 60)
print(f"  Classical bound: F = 0.6667")
print(f"  CFD critical threshold: gamma_c ~ 0.535")
print(f"  Shots per point: {SHOTS}")
print()

# Note: This models decoherence statistically by averaging over
# many random Rz angles for each gamma. Each "shot" gets the SAME
# random angles (set per circuit), so we run multiple circuits per gamma.
NUM_CIRCUITS_PER_GAMMA = 20  # Average over 20 random noise instances

gamma_values = np.linspace(0, 1.0, 21)
results_sweep = []

print(f"  {'gamma':>6s}  {'F(|0>)':>8s}  {'F(|1>)':>8s}  {'F_avg':>8s}  {'Status'}")
print(f"  {'-'*6}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*20}")

for gamma in gamma_values:
    fidelities_0 = []
    fidelities_1 = []
    
    for _ in range(NUM_CIRCUITS_PER_GAMMA):
        # Send |0>
        qc0 = build_teleport_circuit('0', gamma)
        qc0_t = transpile(qc0, backend)
        job0 = backend.run(qc0_t, shots=SHOTS // NUM_CIRCUITS_PER_GAMMA)
        c0 = job0.result().get_counts()
        fidelities_0.append(compute_fidelity(c0, 0))
        
        # Send |1>
        qc1 = build_teleport_circuit('1', gamma)
        qc1_t = transpile(qc1, backend)
        job1 = backend.run(qc1_t, shots=SHOTS // NUM_CIRCUITS_PER_GAMMA)
        c1 = job1.result().get_counts()
        fidelities_1.append(compute_fidelity(c1, 1))
    
    f0_avg = np.mean(fidelities_0)
    f1_avg = np.mean(fidelities_1)
    f_avg = (f0_avg + f1_avg) / 2
    
    if f_avg > 0.99:
        status = "TRAVERSABLE"
    elif f_avg > 0.667:
        status = "QUANTUM CHANNEL"
    elif f_avg > 0.55:
        status = "PARTIAL SIGNAL"
    elif f_avg > 0.45:
        status = "COLLAPSED"
    else:
        status = "BELOW RANDOM"
    
    results_sweep.append((gamma, f0_avg, f1_avg, f_avg))
    print(f"  {gamma:6.3f}  {f0_avg:8.4f}  {f1_avg:8.4f}  {f_avg:8.4f}  {status}")


# ============================================================================
# PART 3: SUMMARY AND HARDWARE INSTRUCTIONS
# ============================================================================
print("\n" + "=" * 60)
print("PART 3: SUMMARY")
print("=" * 60)

# Find where fidelity drops below classical bound
crossed = False
for gamma, f0, f1, favg in results_sweep:
    if favg < 0.667 and not crossed:
        print(f"\n  Quantum advantage lost at gamma ~ {gamma:.3f}")
        crossed = True

print(f"\n  Results array (for plotting):")
print(f"  gamma = {[round(r[0], 3) for r in results_sweep]}")
print(f"  F_avg = {[round(r[3], 4) for r in results_sweep]}")

print(f"""
  INTERPRETATION:
  ---------------
  On a noiseless simulator, teleportation gives F = 1.0 at all gamma.
  This is because the BasicSimulator applies gates exactly -- the Rz 
  rotations in the decoherence model are deterministic per circuit.
  
  The proper test of CFD predictions requires EITHER:
    (a) A density-matrix simulator with genuine phase damping channels
    (b) Real quantum hardware where intrinsic noise provides gamma > 0
  
  FOR HARDWARE (IonQ Forte-1):
  ----------------------------
  Use the circuit from build_teleport_circuit(message, gamma=0.0)
  with NO artificial decoherence. The hardware's intrinsic noise IS 
  the decoherence. Compare the measured fidelity against:
    F = 1.000  (noiseless simulation)
    F = 0.667  (classical bound)
    F = 0.500  (complete collapse)
  
  If hardware F > 0.667: wormhole traversable on this device.
  If hardware F < 0.667: device noise exceeds traversability threshold.
""")


# ============================================================================
# PART 4: GENERATE HARDWARE-READY CIRCUIT (for copy to Azure script)
# ============================================================================
print("=" * 60)
print("HARDWARE-READY CIRCUITS (gate counts)")
print("=" * 60)

for msg in ['0', '1']:
    qc = build_teleport_circuit(msg, 0.0)
    qc_t = transpile(qc, basis_gates=['cx', 'id', 'rz', 'ry', 'rx', 'h', 'measure'])
    gate_counts = qc_t.count_ops()
    depth = qc_t.depth()
    print(f"\n  Send |{msg}>:")
    print(f"    Gates: {dict(gate_counts)}")
    print(f"    Depth: {depth}")
    print(f"    Qubits: {qc_t.num_qubits}")
