import os
import warnings
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
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
# 2. MANUAL GATES (Bare Metal)
# ============================================================================

def apply_rxx(qc, theta, q1, q2):
    qc.h(q1)
    qc.h(q2)
    qc.cx(q1, q2)
    qc.rz(2 * theta, q2)
    qc.cx(q1, q2)
    qc.h(q1)
    qc.h(q2)

def apply_ryy(qc, theta, q1, q2):
    qc.rx(np.pi/2, q1)
    qc.rx(np.pi/2, q2)
    qc.cx(q1, q2)
    qc.rz(2 * theta, q2)
    qc.cx(q1, q2)
    qc.rx(-np.pi/2, q1)
    qc.rx(-np.pi/2, q2)

def apply_rzz(qc, theta, q1, q2):
    qc.cx(q1, q2)
    qc.rz(2 * theta, q2)
    qc.cx(q1, q2)

# ============================================================================
# 3. SHIELDED WORMHOLE BUILDER
# ============================================================================

def build_shielded_wormhole(gamma=0.535, apply_shield=False):
    reg_A = QuantumRegister(4, 'A')
    reg_B = QuantumRegister(4, 'B')
    reg_msg = QuantumRegister(1, 'msg')
    creg = ClassicalRegister(1, 'c')
    qc = QuantumCircuit(reg_A, reg_B, reg_msg, creg)

    # 1. ENTANGLEMENT
    for i in range(4):
        qc.h(reg_A[i])
        qc.cx(reg_A[i], reg_B[i])
        qc.rz(np.pi/(i+1), reg_A[i])
        qc.rz(-np.pi/(i+1), reg_B[i])

    # 2. MESSAGE INJECTION
    qc.h(reg_msg[0])
    qc.swap(reg_msg[0], reg_A[0])

    # 3. THE NOISE ATTACK (Critical Level)
    noise_pattern = [1.0, -0.8, 0.5, -1.2]
    gamma_angle = gamma * np.pi

    for i in range(4):
        angle = gamma_angle * noise_pattern[i]
        qc.rz(angle, reg_A[i])
        qc.rz(-angle * 1.5, reg_B[i])

    # 3.5. THE SHIELD (Active Correction)
    # We apply this immediately BEFORE the bridge to neutralize the field.
    if apply_shield:
        for i in range(4):
            angle = gamma_angle * noise_pattern[i]
            # Inverse of A's noise
            qc.rz(-angle, reg_A[i])
            # Inverse of B's noise
            qc.rz(angle * 1.5, reg_B[i])

    # 4. THE BRIDGE
    coupling = 0.785 # (Pi/4 with 2x multiplier = Pi/2)
    for i in range(4):
        apply_rxx(qc, coupling, reg_A[i], reg_B[i])
        apply_ryy(qc, coupling, reg_A[i], reg_B[i])
        apply_rzz(qc, coupling, reg_A[i], reg_B[i])

    # 5. VERIFICATION
    qc.h(reg_B[0])
    qc.measure(reg_B[0], creg[0])

    return qc

# ============================================================================
# 4. RUN EXPERIMENT
# ============================================================================

test_cases = [
    {"label": "UNPROTECTED (Damaged)", "shield": False},
    {"label": "PROTECTED (Active Shield)", "shield": True}
]

print("\n3. Running Phase 3: Active Shielding Protocol...")

for test in test_cases:
    print(f"\n--- Condition: {test['label']} ---")

    qc = build_shielded_wormhole(gamma=0.535, apply_shield=test['shield'])

    try:
        job = backend.run(qc, shots=100)
        res = job.result()

        if res.success:
            counts = res.get_counts()

            # Fidelity
            total = sum(counts.values())
            success_count = counts.get('0', 0)

            prob_success = success_count / 100
            fidelity = (prob_success - 0.5) * 2
            if fidelity < 0: fidelity = 0

            print(f"   -> Counts: {counts}")
            print(f"   -> Fidelity: {fidelity:.4f}")

            if fidelity > 0.8:
                print("   ✅ STATUS: OPERATIONAL (Shields Holding)")
            elif fidelity < 0.2:
                print("   ⛔ STATUS: CRITICAL FAILURE")

    except Exception as e:
        print(f"   Error: {e}")

print("\nExperiment Complete.")
