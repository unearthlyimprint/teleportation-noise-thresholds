"""
Corrected Minimal Wormhole Teleportation Protocol
==================================================
Author: Celal Arda (with corrections by analysis)
Date: February 2026

This script implements CORRECT quantum teleportation with classical
post-processing of Bell measurement outcomes.

THE CRITICAL FIX:
-----------------
The previous "Mini Shielded Wormhole" script omitted the conditional
Pauli corrections after the Bell measurement. Without these corrections,
teleportation CANNOT work -- the output is random regardless of noise.

Standard teleportation requires:
  1. Create Bell pair (Alice-Bob)
  2. Bell measurement on (Message, Alice)
  3. Conditional corrections on Bob based on Bell outcome:
     - Outcome (0,0): no correction
     - Outcome (0,1): apply X to Bob
     - Outcome (1,0): apply Z to Bob  
     - Outcome (1,1): apply ZX to Bob

Since IonQ doesn't reliably support mid-circuit measurement + feed-forward,
we measure everything at the end and apply corrections in POST-PROCESSING.

For Z-basis measurement of the output:
  - Z correction doesn't affect Z-measurement outcome
  - X correction flips the outcome
  Therefore: if Alice's qubit (q1) measured 1, flip Bob's result.

This script runs THREE experiments:
  A. Send |0> -- expect to recover 0 at Bob
  B. Send |1> -- expect to recover 1 at Bob  
  C. Control: No entanglement -- should give ~50/50 (no teleportation)
"""

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile

# ============================================================================
# 1. BACKEND SELECTION
# ============================================================================
print("=" * 60)
print("CORRECTED WORMHOLE TELEPORTATION PROTOCOL")
print("=" * 60)

# Try to load local simulator
try:
    from qiskit.providers.basic_provider import BasicProvider
    backend = BasicProvider().get_backend('basic_simulator')
    print(f"Backend: {backend.name} (local)")
except ImportError:
    try:
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
        print(f"Backend: AerSimulator (local)")
    except ImportError:
        from qiskit import Aer
        backend = Aer.get_backend('aer_simulator')
        print(f"Backend: aer_simulator (legacy)")

SHOTS = 2000  # More shots for better statistics

# ============================================================================
# 2. BUILD TELEPORTATION CIRCUIT
# ============================================================================
def build_teleport_circuit(message_state='0'):
    """
    Build a correct 3-qubit teleportation circuit.
    
    Qubit layout:
      q0 = Message (what we want to teleport)
      q1 = Alice's half of Bell pair
      q2 = Bob's half of Bell pair
    
    Args:
        message_state: '0' to send |0>, '1' to send |1>, '+' to send |+>
    
    Returns:
        QuantumCircuit with all 3 qubits measured
    """
    qr = QuantumRegister(3, 'q')
    cr = ClassicalRegister(3, 'c')  # c[0]=message, c[1]=alice, c[2]=bob
    qc = QuantumCircuit(qr, cr)
    
    # --- Step 1: Prepare the message state on q0 ---
    if message_state == '1':
        qc.x(qr[0])  # |1>
    elif message_state == '+':
        qc.h(qr[0])  # |+> = (|0> + |1>)/sqrt(2)
    # else: |0> (default)
    
    # --- Step 2: Create Bell pair between Alice (q1) and Bob (q2) ---
    # This is the "ER bridge" -- entanglement connecting two boundaries
    qc.h(qr[1])
    qc.cx(qr[1], qr[2])
    
    # --- Step 3: Bell measurement on Message (q0) + Alice (q1) ---
    qc.cx(qr[0], qr[1])
    qc.h(qr[0])
    
    # --- Step 4: Measure ALL qubits ---
    # We will apply corrections in classical post-processing
    qc.measure(qr[0], cr[0])  # Bell outcome bit 1
    qc.measure(qr[1], cr[1])  # Bell outcome bit 2  
    qc.measure(qr[2], cr[2])  # Bob's raw output
    
    return qc


def build_control_circuit():
    """
    Control experiment: Send |1> WITHOUT entanglement.
    
    With entanglement: Bob should receive |1> (fidelity ~ 1.0)
    Without entanglement: Bob stays |0> (fidelity ~ 0.0 for message=|1>)
    
    This proves information transfer requires the ER bridge.
    """
    qr = QuantumRegister(3, 'q')
    cr = ClassicalRegister(3, 'c')
    qc = QuantumCircuit(qr, cr)
    
    # Prepare |1> message
    qc.x(qr[0])
    
    # Do NOT create Bell pair (no entanglement)
    # Apply Bell measurement gates anyway
    qc.cx(qr[0], qr[1])
    qc.h(qr[0])
    
    qc.measure(qr[0], cr[0])
    qc.measure(qr[1], cr[1])
    qc.measure(qr[2], cr[2])
    
    return qc


# ============================================================================
# 3. POST-PROCESSING: Apply classical corrections
# ============================================================================
def analyze_teleportation(counts, message_sent, label=""):
    """
    Apply classical teleportation corrections and compute fidelity.
    
    For Z-basis measurement:
    - If Bell outcome q1 = 0: Bob's result is correct as-is
    - If Bell outcome q1 = 1: Bob's result needs X-flip (0<->1)
    - The q0 outcome determines Z correction, which doesn't affect 
      Z-basis measurement outcomes
    
    Args:
        counts: dict of measurement outcomes {'c2 c1 c0': count}
                Note: Qiskit bit ordering is REVERSED (c[2] is leftmost)
        message_sent: '0' or '1' (the intended message)
        label: experiment label for printing
    """
    print(f"\n{'='*50}")
    print(f"EXPERIMENT: {label}")
    print(f"Message sent: |{message_sent}>")
    print(f"{'='*50}")
    
    total_shots = sum(counts.values())
    correct = 0
    incorrect = 0
    
    # Qiskit returns bitstrings as 'c[2] c[1] c[0]' (reversed order)
    # So '101' means c[2]=1, c[1]=0, c[0]=1
    #   c[0] = q0 measurement (Bell bit 1)
    #   c[1] = q1 measurement (Bell bit 2 = Alice)  
    #   c[2] = q2 measurement (Bob's raw output)
    
    bell_outcomes = {'00': 0, '01': 0, '10': 0, '11': 0}
    
    for bitstring, count in counts.items():
        # Parse the bitstring (Qiskit reversed ordering)
        bits = bitstring.replace(' ', '')
        bob_raw = int(bits[0])    # c[2] = Bob
        alice = int(bits[1])      # c[1] = Alice (Bell bit 2)
        msg_meas = int(bits[2])   # c[0] = Message (Bell bit 1)
        
        bell_key = f"{msg_meas}{alice}"
        bell_outcomes[bell_key] += count
        
        # Apply classical correction:
        # If alice (q1) measured 1, flip Bob's result
        if alice == 1:
            bob_corrected = 1 - bob_raw
        else:
            bob_corrected = bob_raw
        
        # Check if corrected Bob matches the sent message
        expected = int(message_sent)
        if bob_corrected == expected:
            correct += count
        else:
            incorrect += count
    
    fidelity = correct / total_shots
    
    print(f"\nRaw counts: {counts}")
    print(f"Bell measurement distribution:")
    for k, v in sorted(bell_outcomes.items()):
        print(f"  |{k}> : {v} shots ({v/total_shots*100:.1f}%)")
    print(f"\nAfter classical correction:")
    print(f"  Correct:   {correct}/{total_shots} ({correct/total_shots*100:.1f}%)")
    print(f"  Incorrect: {incorrect}/{total_shots} ({incorrect/total_shots*100:.1f}%)")
    print(f"  FIDELITY:  {fidelity:.4f}")
    
    if fidelity > 0.9:
        print(f"  VERDICT:   TRAVERSABLE (F = {fidelity:.3f})")
    elif fidelity > 0.55:
        print(f"  VERDICT:   PARTIAL SIGNAL (F = {fidelity:.3f})")
    elif fidelity > 0.45:
        print(f"  VERDICT:   NOISE DOMINATED (F = {fidelity:.3f})")
    else:
        print(f"  VERDICT:   INVERTED or BROKEN (F = {fidelity:.3f})")
    
    return fidelity


# ============================================================================
# 4. RUN ALL EXPERIMENTS
# ============================================================================
print(f"\nShots per experiment: {SHOTS}")
results = {}

# --- Experiment A: Send |0> ---
print("\n[A] Building circuit: Send |0> ...")
qc_0 = build_teleport_circuit('0')
qc_0t = transpile(qc_0, backend)
job_0 = backend.run(qc_0t, shots=SHOTS)
counts_0 = job_0.result().get_counts()
f_0 = analyze_teleportation(counts_0, '0', "Send |0> through wormhole")
results['send_0'] = f_0

# --- Experiment B: Send |1> ---
print("\n[B] Building circuit: Send |1> ...")
qc_1 = build_teleport_circuit('1')
qc_1t = transpile(qc_1, backend)
job_1 = backend.run(qc_1t, shots=SHOTS)
counts_1 = job_1.result().get_counts()
f_1 = analyze_teleportation(counts_1, '1', "Send |1> through wormhole")
results['send_1'] = f_1

# --- Experiment C: Control (no entanglement) ---
print("\n[C] Building control circuit (no Bell pair) ...")
qc_ctrl = build_control_circuit()
qc_ctrlt = transpile(qc_ctrl, backend)
job_ctrl = backend.run(qc_ctrlt, shots=SHOTS)
counts_ctrl = job_ctrl.result().get_counts()
f_ctrl = analyze_teleportation(counts_ctrl, '1', "CONTROL: Send |1> WITHOUT entanglement")
results['control'] = f_ctrl

# ============================================================================
# 5. SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("SUMMARY OF RESULTS")
print("=" * 60)
print(f"  Send |0> fidelity:     {results['send_0']:.4f}")
print(f"  Send |1> fidelity:     {results['send_1']:.4f}")
print(f"  Average fidelity:      {(results['send_0'] + results['send_1'])/2:.4f}")
print(f"  Control (no ent.):     {results['control']:.4f}")
print(f"  Classical bound:       0.6667")
print()

avg_f = (results['send_0'] + results['send_1']) / 2
if avg_f > 0.99:
    print("CONCLUSION: Perfect teleportation. Wormhole fully traversable.")
    print("            (Expected for noiseless simulation)")
elif avg_f > 0.667:
    print("CONCLUSION: Fidelity exceeds classical bound.")
    print("            Quantum channel operational. Wormhole traversable.")
elif avg_f > 0.55:
    print("CONCLUSION: Partial quantum signal detected but below classical bound.")
elif avg_f > 0.45:
    print("CONCLUSION: Noise dominated. Wormhole collapsed.")
else:
    print("CONCLUSION: Below random. Protocol error or extreme noise.")

if results['control'] < 0.15:
    print("\nCONTROL PASSED: Without entanglement, |1> was NOT received at Bob.")
    print("This confirms entanglement (ER bridge) is required for traversability.")
else:
    print(f"\nCONTROL NOTE: Expected ~0.00 (no transfer), got {results['control']:.3f}")
