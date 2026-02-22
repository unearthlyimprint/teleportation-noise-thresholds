"""
Analyze FRESNEL_CAN1 QPU Results
=================================
Loads the fetched FRESNEL_CAN1 raw counts, extracts the 9 core
wormhole qubits, and compares with EMU_FREE reference values.

Usage:
    source ../pasqal_env/bin/activate
    python analyze_fresnel_can1.py
"""

import os
import sys
import json
import glob
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from wormhole_pulser_continuous import extract_core_counts


# ============================================================================
# EMU_FREE Reference (9-qubit noiseless simulation)
# ============================================================================
EMU_FREE_REF = {
    0.05: {"p0": 0.08, "rho": 0.201},
    0.20: {"p0": 0.72, "rho": 0.034},
    0.40: {"p0": 0.93, "rho": 0.009},
}

# γ values in submission order (from run_fresnel_validation.py GAMMA_POINTS)
GAMMA_POINTS = [0.05, 0.20, 0.40]


def load_latest_results():
    """Find the most recent fresnel_can1_*.json (with raw counts)."""
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    files = sorted(glob.glob(os.path.join(results_dir, 'fresnel_can1_2*.json')))
    if not files:
        print("ERROR: No fresnel_can1_*.json files found in results/")
        sys.exit(1)
    latest = files[-1]
    print(f"Loading: {os.path.basename(latest)}")
    with open(latest) as f:
        return json.load(f), latest


def analyze():
    results, filepath = load_latest_results()

    # Sort by creation time (earliest first) to match gamma order
    results.sort(key=lambda r: r.get("created_at", ""))

    print("\n" + "=" * 80)
    print("  FRESNEL_CAN1 QPU Results — Core Qubit Analysis")
    print("=" * 80)

    # ── Full 22-qubit stats ──
    print(f"\n{'─' * 80}")
    print(f"  Full Register Stats (22 qubits)")
    print(f"{'─' * 80}")
    for i, r in enumerate(results):
        gamma = GAMMA_POINTS[i] if i < len(GAMMA_POINTS) else "?"
        print(f"  γ={gamma}  shots={r['total_shots']}  "
              f"P₀(22q)={r['p_ground']:.4f}  "
              f"⟨n⟩(22q)={r['mean_rho']:.4f}  "
              f"states={r['unique_states']}")

    # ── Core-qubit extraction ──
    # The core qubits are q0–q8 (the 9 wormhole qubits),
    # q9–q21 are spectators used for layout filling.
    # We need to extract bits corresponding to these positions.
    all_qubit_ids = [f"q{i}" for i in range(22)]
    core_ids = [f"q{i}" for i in range(9)]

    print(f"\n{'─' * 80}")
    print(f"  Core Qubit Stats (9 wormhole qubits extracted)")
    print(f"{'─' * 80}")

    core_results = []
    for i, r in enumerate(results):
        gamma = GAMMA_POINTS[i] if i < len(GAMMA_POINTS) else None
        raw_counts = r.get("raw_counts")

        if not raw_counts:
            print(f"  γ={gamma}  NO RAW COUNTS (summary-only file)")
            continue

        # Extract core qubit counts
        core_counts = extract_core_counts(raw_counts, core_ids, all_qubit_ids)
        core_shots = sum(core_counts.values())
        ground_9 = "0" * 9
        p0_core = core_counts.get(ground_9, 0) / core_shots if core_shots > 0 else 0
        rho_core = sum(
            bs.count("1") / 9 * n for bs, n in core_counts.items()
        ) / core_shots if core_shots > 0 else 0
        n_core_states = len(core_counts)

        print(f"  γ={gamma:.2f}  shots={core_shots}  "
              f"P₀(9q)={p0_core:.4f}  "
              f"⟨n⟩(9q)={rho_core:.4f}  "
              f"states={n_core_states}")

        core_results.append({
            "gamma": gamma,
            "p0_core": p0_core,
            "rho_core": rho_core,
            "core_shots": core_shots,
            "core_states": n_core_states,
            "core_counts": core_counts,
            "p0_full": r["p_ground"],
            "rho_full": r["mean_rho"],
        })

    # ── Comparison with EMU_FREE ──
    if core_results:
        print(f"\n{'=' * 80}")
        print(f"  Comparison: EMU_FREE (9q ideal) vs FRESNEL_CAN1 QPU (9 core / 22 total)")
        print(f"{'=' * 80}")
        print(f"  {'γ':<6} | {'EMU_FREE P₀':<13} | {'QPU P₀(9q)':<13} | {'Δ P₀':<10} | "
              f"{'EMU_FREE ⟨n⟩':<14} | {'QPU ⟨n⟩(9q)':<14}")
        print(f"  {'─' * 76}")

        for cr in core_results:
            gamma = cr["gamma"]
            ref = EMU_FREE_REF.get(gamma, {})
            emu_p0 = ref.get("p0")
            emu_rho = ref.get("rho")

            if emu_p0 is not None:
                delta_p0 = cr["p0_core"] - emu_p0
                print(f"  {gamma:<6.2f} | {emu_p0:<13.1%} | {cr['p0_core']:<13.4f} | "
                      f"{delta_p0:<+10.4f} | {emu_rho:<14.4f} | {cr['rho_core']:<14.4f}")

        # ── Physics interpretation ──
        print(f"\n{'─' * 80}")
        print(f"  Physics Interpretation")
        print(f"{'─' * 80}")

        for cr in core_results:
            gamma = cr["gamma"]
            ref = EMU_FREE_REF.get(gamma, {})
            emu_rho = ref.get("rho", 0)

            if gamma == 0.05:
                regime = "HIGH decoherence (near-collapse)"
            elif gamma == 0.20:
                regime = "MODERATE decoherence"
            else:
                regime = "LOW decoherence (near-vacuum)"

            print(f"\n  γ = {gamma:.2f} — {regime}")
            print(f"    QPU  P₀ = {cr['p0_core']:.4f}, ⟨n⟩ = {cr['rho_core']:.4f}")
            print(f"    EMU  P₀ = {ref.get('p0', '?')},  ⟨n⟩ = {emu_rho}")
            if emu_rho > 0:
                noise_ratio = cr['rho_core'] / emu_rho
                print(f"    Noise ratio (QPU/EMU): {noise_ratio:.2f}x")

        # ── Save enriched results ──
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
        outfile = os.path.join(output_dir, "fresnel_can1_core_analysis.json")
        save_data = []
        for cr in core_results:
            entry = {k: v for k, v in cr.items() if k != "core_counts"}
            ref = EMU_FREE_REF.get(cr["gamma"], {})
            entry["emu_free_p0"] = ref.get("p0")
            entry["emu_free_rho"] = ref.get("rho")
            entry["delta_p0"] = cr["p0_core"] - ref.get("p0", 0)
            if ref.get("rho", 0) > 0:
                entry["noise_ratio"] = cr["rho_core"] / ref["rho"]
            save_data.append(entry)

        with open(outfile, "w") as f:
            json.dump(save_data, f, indent=2)
        print(f"\n  ✅ Core analysis saved to: {outfile}")

    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    analyze()
