"""
Trotter-Depth Sweep: Noisy Prediction (Corrected)
===================================================
Density-matrix simulation of the 3-qubit wormhole with
depolarizing noise calibrated to IonQ Forte-1.

Matches the proven circuit from tier1v3_trotter_sweep.py exactly:
  1. H(Alice) → CX(Alice,Bob) → Rz(π, Alice) → Rz(-π, Bob)   [Bell pair]
  2. H(Msg) → SWAP(Msg, Alice)                                  [message inject]
  3. N×[RXX + RYY + RZZ](Alice, Bob)                            [Trotter bridge]
  4. H(Bob) → Measure(Bob) → Classical correction if Msg=1

CX count: 1 (Bell) + 3 (SWAP) + 6·N (bridge) = 4 + 6N

Usage:
    python trotter_noisy_corrected.py

No cloud access needed. Runs in seconds.
"""

import numpy as np
import os

# ============================================================================
# GATE PRIMITIVES (3-qubit density matrix)
# ============================================================================

I2 = np.eye(2, dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)
H_gate = np.array([[1,1],[1,-1]], dtype=complex) / np.sqrt(2)

def Rz(theta):
    return np.array([[np.exp(-1j*theta/2), 0],
                     [0, np.exp(1j*theta/2)]], dtype=complex)

def Rx(theta):
    return np.array([[np.cos(theta/2), -1j*np.sin(theta/2)],
                     [-1j*np.sin(theta/2), np.cos(theta/2)]], dtype=complex)

def tensor(*ms):
    r = ms[0]
    for m in ms[1:]:
        r = np.kron(r, m)
    return r

def gate_on(gate, q, n=3):
    ops = [I2]*n
    ops[q] = gate
    return tensor(*ops)

def cnot(c, t, n=3):
    dim = 2**n
    U = np.zeros((dim, dim), dtype=complex)
    for i in range(dim):
        bits = list(format(i, f'0{n}b'))
        if bits[c] == '0':
            U[i,i] = 1
        else:
            j_bits = bits.copy()
            j_bits[t] = '1' if bits[t] == '0' else '0'
            j = int(''.join(j_bits), 2)
            U[j,i] = 1
    return U

def swap(q1, q2, n=3):
    return cnot(q1,q2,n) @ cnot(q2,q1,n) @ cnot(q1,q2,n)

# ============================================================================
# NOISE CHANNELS
# ============================================================================

def depolarize_2q(rho, epsilon, n_qubits=3):
    """Global 2-qubit depolarizing: rho → (1-ε)*rho + ε*I/d"""
    if epsilon <= 0: return rho
    d = 2**n_qubits
    return (1 - epsilon) * rho + epsilon * np.eye(d, dtype=complex) / d

def depolarize_1q(rho, epsilon, n_qubits=3):
    if epsilon <= 0: return rho
    d = 2**n_qubits
    return (1 - epsilon) * rho + epsilon * np.eye(d, dtype=complex) / d


# ============================================================================
# WORMHOLE CIRCUIT (matches tier1v3 exactly)
# ============================================================================

def simulate_wormhole(n_trotter=1, cx_noise=0.0, sq_noise=0.0, total_coupling=0.785):
    """
    Qubits: 0=Alice, 1=Bob, 2=Msg
    (matches tier1v3: alice=A[0], bob=B[0], msg=msg[0])
    """
    alice, bob, msg = 0, 1, 2
    dim = 8
    n_cx = 0

    psi = np.zeros(dim, dtype=complex)
    psi[0] = 1.0   # |000>
    rho = np.outer(psi, psi.conj())

    def apply_u(rho, U):
        return U @ rho @ U.conj().T

    # --- Stage 1: ER bridge (Bell pair) ---
    rho = apply_u(rho, gate_on(H_gate, alice))
    rho = depolarize_1q(rho, sq_noise)

    rho = apply_u(rho, cnot(alice, bob))
    rho = depolarize_2q(rho, cx_noise)
    n_cx += 1

    rho = apply_u(rho, gate_on(Rz(np.pi), alice))
    rho = depolarize_1q(rho, sq_noise)
    rho = apply_u(rho, gate_on(Rz(-np.pi), bob))
    rho = depolarize_1q(rho, sq_noise)

    # --- Stage 2: Message injection (H + SWAP) ---
    rho = apply_u(rho, gate_on(H_gate, msg))
    rho = depolarize_1q(rho, sq_noise)

    # SWAP = 3 CNOTs
    rho = apply_u(rho, cnot(msg, alice))
    rho = depolarize_2q(rho, cx_noise)
    n_cx += 1
    rho = apply_u(rho, cnot(alice, msg))
    rho = depolarize_2q(rho, cx_noise)
    n_cx += 1
    rho = apply_u(rho, cnot(msg, alice))
    rho = depolarize_2q(rho, cx_noise)
    n_cx += 1

    # --- Stage 3: No CFD noise (γ=0 for this experiment) ---

    # --- Stage 4: Bridge (Trotter-decomposed Heisenberg) ---
    step_coupling = total_coupling / n_trotter

    for _ in range(n_trotter):
        # RXX(step_coupling) on alice-bob: H-H-CX-Rz-CX-H-H
        rho = apply_u(rho, gate_on(H_gate, alice))
        rho = apply_u(rho, gate_on(H_gate, bob))
        rho = apply_u(rho, cnot(alice, bob))
        rho = depolarize_2q(rho, cx_noise)
        n_cx += 1
        rho = apply_u(rho, gate_on(Rz(2*step_coupling), bob))
        rho = apply_u(rho, cnot(alice, bob))
        rho = depolarize_2q(rho, cx_noise)
        n_cx += 1
        rho = apply_u(rho, gate_on(H_gate, alice))
        rho = apply_u(rho, gate_on(H_gate, bob))

        # Single-qubit noise for the H/Rz gates
        rho = depolarize_1q(rho, sq_noise * 4)

        # RYY(step_coupling) on alice-bob: Rx-Rx-CX-Rz-CX-Rx†-Rx†
        rho = apply_u(rho, gate_on(Rx(np.pi/2), alice))
        rho = apply_u(rho, gate_on(Rx(np.pi/2), bob))
        rho = apply_u(rho, cnot(alice, bob))
        rho = depolarize_2q(rho, cx_noise)
        n_cx += 1
        rho = apply_u(rho, gate_on(Rz(2*step_coupling), bob))
        rho = apply_u(rho, cnot(alice, bob))
        rho = depolarize_2q(rho, cx_noise)
        n_cx += 1
        rho = apply_u(rho, gate_on(Rx(-np.pi/2), alice))
        rho = apply_u(rho, gate_on(Rx(-np.pi/2), bob))

        rho = depolarize_1q(rho, sq_noise * 4)

        # RZZ(step_coupling) on alice-bob: CX-Rz-CX
        rho = apply_u(rho, cnot(alice, bob))
        rho = depolarize_2q(rho, cx_noise)
        n_cx += 1
        rho = apply_u(rho, gate_on(Rz(2*step_coupling), bob))
        rho = apply_u(rho, cnot(alice, bob))
        rho = depolarize_2q(rho, cx_noise)
        n_cx += 1

    # --- Stage 5: Measurement ---
    rho = apply_u(rho, gate_on(H_gate, bob))
    rho = depolarize_1q(rho, sq_noise)

    # Compute probabilities: |a b m> where a=alice(0), b=bob(1), m=msg(2)
    probs = np.real(np.diag(rho))
    probs = np.maximum(probs, 0)
    probs /= probs.sum()

    # The Qiskit circuit only measures Bob (qubit 1) after H(Bob).
    # No classical correction is applied.
    # F = 2 * P(Bob=0) - 1
    # P(Bob=0) = sum of probs where bit 1 = '0'
    p_bob0 = 0
    for i in range(8):
        bits = format(i, '03b')  # a=alice(0), b=bob(1), m=msg(2)
        if bits[1] == '0':
            p_bob0 += probs[i]

    fidelity = max(0, 2 * p_bob0 - 1)
    return fidelity, n_cx


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    trotter_steps = [1, 2, 3, 5, 8]

    noise_configs = {
        'noiseless':         {'cx': 0.000,  'sq': 0.0000},
        'forte_optimistic':  {'cx': 0.003,  'sq': 0.0003},
        'forte_typical':     {'cx': 0.005,  'sq': 0.0005},
        'forte_pessimistic': {'cx': 0.008,  'sq': 0.0008},
    }

    print("=" * 70)
    print("  Trotter-Depth Sweep: Noisy Prediction (Corrected)")
    print("  Matches tier1v3_trotter_sweep.py circuit exactly")
    print("=" * 70)

    all_results = {}

    for config_name, noise in noise_configs.items():
        print(f"\n--- {config_name} (CX={noise['cx']}, SQ={noise['sq']}) ---")
        all_results[config_name] = []

        for steps in trotter_steps:
            F, n_cx = simulate_wormhole(
                n_trotter=steps,
                cx_noise=noise['cx'],
                sq_noise=noise['sq']
            )
            all_results[config_name].append({
                'steps': steps, 'n_cx': n_cx, 'fidelity': F
            })
            print(f"  Steps={steps:>2}, CX={n_cx:>2}, F={F:.4f}")

    # Comparison table
    print(f"\n{'=' * 70}")
    print(f"  COMPARISON TABLE: Predicted Fidelity vs Depth")
    print(f"{'=' * 70}")
    print(f"  {'Steps':>5} {'CX':>4} | {'Noiseless':>10} | {'Optimistic':>10} | "
          f"{'Typical':>10} | {'Pessimistic':>11}")
    print(f"  {'-' * 65}")
    for i, steps in enumerate(trotter_steps):
        n_cx = all_results['noiseless'][i]['n_cx']
        vals = [f"{all_results[c][i]['fidelity']:.4f}" for c in noise_configs]
        print(f"  {steps:>5} {n_cx:>4} | {vals[0]:>10} | {vals[1]:>10} | "
              f"{vals[2]:>10} | {vals[3]:>11}")

    # Key analysis
    print(f"\n{'=' * 70}")
    print(f"  KEY ANALYSIS")
    print(f"{'=' * 70}")

    for config_name in ['forte_optimistic', 'forte_typical', 'forte_pessimistic']:
        r = all_results[config_name]
        f1 = r[0]['fidelity']   # Steps=1
        f8 = r[-1]['fidelity']  # Steps=8
        cx1 = r[0]['n_cx']
        cx8 = r[-1]['n_cx']
        if f1 > 0 and f8 > 0:
            eps = 1 - (f8 / f1) ** (1.0 / (cx8 - cx1))
            drop = f1 - f8
            print(f"\n  {config_name}:")
            print(f"    F(10 CX) = {f1:.4f}  →  F(52 CX) = {f8:.4f}")
            print(f"    Total drop: ΔF = {drop:.4f}")
            print(f"    Effective ε per CX: {eps:.5f}")
            print(f"    Above classical bound (2/3): {'✓' if f8 > 0.667 else '✗'}")

    # Resolve at 200 shots?
    print(f"\n{'=' * 70}")
    print(f"  SHOT COUNT FEASIBILITY (can 200 shots resolve the differences?)")
    print(f"{'=' * 70}")
    typical = all_results['forte_typical']
    for i in range(len(trotter_steps)-1):
        F1, F2 = typical[i]['fidelity'], typical[i+1]['fidelity']
        dF = abs(F1 - F2)
        for n_shots in [200, 500]:
            p1, p2 = (F1+1)/2, (F2+1)/2
            s1 = 2*np.sqrt(max(p1*(1-p1), 0)/n_shots)
            s2 = 2*np.sqrt(max(p2*(1-p2), 0)/n_shots)
            sig = dF / np.sqrt(s1**2 + s2**2) if (s1**2+s2**2) > 0 else 0
            if n_shots == 200:
                print(f"  Steps {typical[i]['steps']:>1}→{typical[i+1]['steps']:>1}: "
                      f"ΔF={dF:.4f}, 200 shots: {sig:.1f}σ, 500 shots: {sig*np.sqrt(2.5):.1f}σ")

    # Figure
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = {
            'noiseless': '#2196F3',
            'forte_optimistic': '#4CAF50',
            'forte_typical': '#FF9800',
            'forte_pessimistic': '#F44336',
        }
        labels = {
            'noiseless': 'Noiseless (F=1.0)',
            'forte_optimistic': 'Forte optimistic (ε=0.3%)',
            'forte_typical': 'Forte typical (ε=0.5%)',
            'forte_pessimistic': 'Forte pessimistic (ε=0.8%)',
        }

        for name in noise_configs:
            cx_counts = [r['n_cx'] for r in all_results[name]]
            fids = [r['fidelity'] for r in all_results[name]]
            ax.plot(cx_counts, fids, 'o-', color=colors[name], label=labels[name],
                   markersize=8, linewidth=2)

        # Add existing hardware data point (F=0.988 at ~10 CX from 3-qubit experiment)
        ax.plot(10, 0.988, 's', color='black', markersize=12, zorder=5,
               label='Forte-1 measured (F=0.988)')
        ax.errorbar(10, 0.988, yerr=0.003, color='black', capsize=5, zorder=5)

        ax.set_xlabel('Number of CNOT Gates', fontsize=13)
        ax.set_ylabel('Teleportation Fidelity F', fontsize=13)
        ax.set_title('Predicted Fidelity vs Circuit Depth\n'
                     '(3-qubit wormhole, Trotter decomposition)', fontsize=14)
        ax.legend(fontsize=10, loc='lower left')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.05, 1.05)
        ax.axhline(y=2/3, color='gray', linestyle=':', alpha=0.5)
        ax.text(50, 0.69, 'Classical bound', fontsize=9, color='gray')

        outdir = os.path.join(os.path.dirname(__file__), '..', 'proj_progress')
        figpath = os.path.join(outdir, 'figure_trotter_prediction.png')
        plt.tight_layout()
        plt.savefig(figpath, dpi=200, bbox_inches='tight')
        print(f"\n  Figure saved to: {figpath}")

    except ImportError:
        print("  (matplotlib not available — skipping figure)")

    print(f"\n{'=' * 70}")
    print("  WHAT TO EXPECT ON HARDWARE")
    print(f"{'=' * 70}")
    print("""
  If hardware matches the 'forte_typical' curve → standard noise model.
  If hardware shows a SHARPER drop at some CX count → CFD threshold.

  Your existing data point (F=0.988 at 10 CX) should sit near the
  optimistic/typical curves at Steps=1.

  The sweep from 10 → 52 CX gates will reveal the shape of the curve.
""")
