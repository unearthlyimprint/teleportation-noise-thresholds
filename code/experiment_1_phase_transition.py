import os
import warnings
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from azure.quantum.qiskit import AzureQuantumProvider
from azure.identity import DeviceCodeCredential

warnings.filterwarnings("ignore")

# ============================================================================
# 1. SETUP AZURE
# ============================================================================

# Load credentials from environment variables
tenant_id = os.environ.get("AZURE_TENANT_ID")
resource_id = os.environ.get("AZURE_RESOURCE_ID")

print("1. Authenticating...")
credential = DeviceCodeCredential(tenant_id=tenant_id)
provider = AzureQuantumProvider(resource_id=resource_id, location="eastus", credential=credential)
backend = provider.get_backend("ionq.simulator")
print(f"2. Connected to backend: {backend.name}")

# ============================================================================
# 2. MANUAL GATES (FIXED)
# ============================================================================

def apply_rxx(qc, theta, q1, q2):
    """Hamiltonian simulation of e^(-i * theta * XX)"""
    qc.h(q1)
    qc.h(q2)
    qc.cx(q1, q2)
    qc.rz(2 * theta, q2) # FIX: Added factor of 2
    qc.cx(q1, q2)
    qc.h(q1)
    qc.h(q2)

def apply_ryy(qc, theta, q1, q2):
    """Hamiltonian simulation of e^(-i * theta * YY)"""
    qc.rx(np.pi/2, q1)
    qc.rx(np.pi/2, q2)
    qc.cx(q1, q2)
    qc.rz(2 * theta, q2) # FIX: Added factor of 2
    qc.cx(q1, q2)
    qc.rx(-np.pi/2, q1)
    qc.rx(-np.pi/2, q2)

def apply_rzz(qc, theta, q1, q2):
    """Hamiltonian simulation of e^(-i * theta * ZZ)"""
    qc.cx(q1, q2)
    qc.rz(2 * theta, q2) # FIX: Added factor of 2
    qc.cx(q1, q2)

# ============================================================================
# 3. BUILDER
# ============================================================================

def build_wormhole_geometry(gamma, coupling=0.785):
    reg_A = QuantumRegister(4, 'A')
    reg_B = QuantumRegister(4, 'B')
    reg_msg = QuantumRegister(1, 'msg')
    creg = ClassicalRegister(1, 'c')
    qc = QuantumCircuit(reg_A, reg_B, reg_msg, creg)

    # 1. ENTANGLEMENT (Throat)
    for i in range(4):
        qc.h(reg_A[i])
        qc.cx(reg_A[i], reg_B[i])
        qc.rz(np.pi/(i+1), reg_A[i])
        qc.rz(-np.pi/(i+1), reg_B[i])

    # 2. MESSAGE INJECTION
    qc.h(reg_msg[0])
    qc.swap(reg_msg[0], reg_A[0])

    # 3. CHAOTIC NOISE (CFD Layer)
    if gamma > 0:
        # Uncorrelated noise pattern to break symmetry
        noise_pattern = [1.0, -0.8, 0.5, -1.2]
        for i in range(4):
            angle = gamma * np.pi * noise_pattern[i]
            qc.rz(angle, reg_A[i])
            qc.rz(-angle * 1.5, reg_B[i])

    # 4. BRIDGE (Scrambling)
    for i in range(4):
        apply_rxx(qc, coupling, reg_A[i], reg_B[i])
        apply_ryy(qc, coupling, reg_A[i], reg_B[i])
        apply_rzz(qc, coupling, reg_A[i], reg_B[i])

    # 5. VERIFICATION
    qc.h(reg_B[0])
    qc.measure(reg_B[0], creg[0])

    return qc

# ============================================================================
# 4. RUN PROOF
# ============================================================================

experiments = [
    {"label": "BASELINE (Vacuum)", "gamma": 0.0},
    {"label": "CRITICAL (CFD Limit)", "gamma": 0.535}
]

# FIX: Update Coupling to match the factor-of-2 logic (Pi/4 is now correct input)
# If we used 1.57 before with 1x multiplier, we use 0.785 with 2x multiplier.
# It results in the same physical rotation of Pi/2.
CORRECTED_COUPLING = 0.785

print("\n3. Running Final Proof (Corrected Hamiltonian)...")

for exp in experiments:
    print(f"\n--- Condition: {exp['label']} (γ={exp['gamma']}) ---")

    qc = build_wormhole_geometry(gamma=exp['gamma'], coupling=CORRECTED_COUPLING)

    try:
        # Using 100 shots
        job = backend.run(qc, shots=100)
        res = job.result()

        if res.success:
            counts = res.get_counts()

            # Count the Zeros
            success_count = counts.get('0', 0)

            # Strict Fidelity Calculation
            fidelity = (success_count / 100 - 0.5) * 2
            if fidelity < 0: fidelity = 0

            print(f"   -> Counts: {counts}")
            print(f"   -> Fidelity: {fidelity:.4f}")

            if fidelity > 0.85:
                print("   ✅ STATUS: TRAVERSABLE")
            elif fidelity < 0.2:
                print("   ⛔ STATUS: COLLAPSED")
            else:
                print("   ⚠️ STATUS: NOISY")

    except Exception as e:
        print(f"   Error: {e}")
