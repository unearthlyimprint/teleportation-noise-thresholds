"""
CFD Wormhole — FRESNEL QPU Hardware Validation
================================================
3-point check on Pasqal's FRESNEL quantum processor.

Runs only 3 gamma values to validate emulator results on real hardware:
  γ = 0.05  (Open wormhole)
  γ = 0.20  (Critical / transition)
  γ = 0.40  (Collapsed)

⚠ FRESNEL uses REAL QPU time — this will incur costs!

Credentials
-----------
Set these environment variables (use the FRESNEL-enabled project ID):
    export PASQAL_PROJECT_ID="your-fresnel-project-id"
    export PASQAL_USERNAME="your-email"
    export PASQAL_PASSWORD="your-password"

Usage
-----
    source ../pasqal_env/bin/activate
    python run_fresnel_validation.py
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from pasqal_cloud import SDK
from wormhole_pulser_continuous import build_wormhole_sequence


# ============================================================================
# CONFIGURATION
# ============================================================================

# 3-point validation: Open, Critical, Collapsed
GAMMA_POINTS = [0.05, 0.20, 0.40]

# Higher shot count for hardware — statistical significance matters
RUNS = 500

# Target: FRESNEL QPU
DEVICE_TYPE = "FRESNEL"

# Fallback for testing: set to "EMU_FREE" to dry-run the script
# DEVICE_TYPE = "EMU_FREE"


# ============================================================================
# COST ESTIMATE
# ============================================================================

def print_cost_estimate():
    """
    Rough cost estimate for FRESNEL QPU runs.

    Pasqal pricing (as of 2025-2026, Explorer/Standard plans):
    - EMU_FREE:   Free
    - EMU_MPS:    ~€0.01/shot  (varies by qubit count)
    - FRESNEL:    ~€0.05–0.10/shot (varies by sequence duration)

    These are approximate — actual pricing depends on your contract.
    """
    n_points = len(GAMMA_POINTS)
    n_qubits = 9
    shots = RUNS

    # Conservative estimate: €0.10/shot for FRESNEL
    cost_per_shot_low  = 0.05
    cost_per_shot_high = 0.10

    total_shots = n_points * shots
    cost_low  = total_shots * cost_per_shot_low
    cost_high = total_shots * cost_per_shot_high

    print("=" * 60)
    print("  FRESNEL QPU — Cost Estimate")
    print("=" * 60)
    print(f"  Points:     {n_points}")
    print(f"  Shots/pt:   {shots}")
    print(f"  Total shots: {total_shots}")
    print(f"  Qubits:     {n_qubits}")
    print(f"")
    print(f"  Estimated cost: €{cost_low:.2f} – €{cost_high:.2f}")
    print(f"")
    print(f"  (Based on ~€0.05–0.10/shot for FRESNEL)")
    print(f"  Actual cost may vary by contract/plan.")
    print("=" * 60)

    return total_shots, cost_low, cost_high


# ============================================================================
# AUTHENTICATION
# ============================================================================

def get_client() -> SDK:
    project_id = os.environ.get("PASQAL_PROJECT_ID")
    username   = os.environ.get("PASQAL_USERNAME")
    password   = os.environ.get("PASQAL_PASSWORD")

    if not all([project_id, username, password]):
        print("ERROR: Set PASQAL_PROJECT_ID, PASQAL_USERNAME, PASQAL_PASSWORD")
        print("  NOTE: Use the FRESNEL-enabled project ID!")
        sys.exit(1)

    print(f"Authenticating (project: {project_id[:8]}...)...", end=" ")
    sdk = SDK(project_id=project_id, username=username, password=password)
    print("OK\n")
    return sdk


# ============================================================================
# SUBMISSION
# ============================================================================

def submit_hardware(sdk, gamma_values, runs, device_type):
    batches = []
    for gamma in gamma_values:
        print(f"  γ = {gamma:.3f}  →  building...", end="  ")
        
        # Use TriangularLatticeLayout for FRESNEL
        use_fresnel = (device_type == "FRESNEL")
        seq = build_wormhole_sequence(gamma=gamma, coupling_time=500, use_fresnel_layout=use_fresnel)
        
        serialized = seq.to_abstract_repr()

        print(f"submitting to {device_type}...", end="  ")
        try:
            batch = sdk.create_batch(
                serialized_sequence=serialized,
                jobs=[{"runs": runs}],
                device_type=device_type,
            )
            print(f"batch {batch.id}")
            batches.append({
                "gamma": gamma,
                "batch_id": batch.id,
                "status": batch.status,
                "device": device_type,
            })
        except Exception as e:
            print(f"FAILED: {e}")
            batches.append({
                "gamma": gamma,
                "batch_id": None,
                "status": "SUBMIT_ERROR",
                "device": device_type,
                "error": str(e),
            })

    return batches


# ============================================================================
# POLLING  (QPU can take minutes to hours depending on queue)
# ============================================================================

def collect_results(sdk, batches, poll_interval=15):
    """
    Poll batches. FRESNEL QPU jobs may queue for a while.
    Default poll interval: 15s (vs 3s for emulators).
    """
    results = []

    for item in batches:
        if item["batch_id"] is None:
            results.append(item)
            continue

        gamma    = item["gamma"]
        batch_id = item["batch_id"]
        elapsed  = 0
        print(f"\n  Polling γ={gamma:.3f} ({item['device']})...", end="", flush=True)

        while True:
            batch = sdk.get_batch(batch_id)
            if batch.status not in ("PENDING", "RUNNING"):
                break
            print(".", end="", flush=True)
            time.sleep(poll_interval)
            elapsed += poll_interval

            # Progress update every 2 minutes
            if elapsed % 120 == 0 and elapsed > 0:
                print(f" [{elapsed//60}min]", end="", flush=True)

        print(f"  → {batch.status} ({elapsed}s)")

        if batch.status == "DONE":
            for job in batch.ordered_jobs:
                counts = job.result if hasattr(job, 'result') and job.result else None
                results.append({
                    "gamma": gamma,
                    "batch_id": batch_id,
                    "job_id": job.id,
                    "status": job.status,
                    "device": item["device"],
                    "counts": counts,
                    "shots": sum(counts.values()) if counts else 0,
                })
        else:
            results.append({
                "gamma": gamma,
                "batch_id": batch_id,
                "status": batch.status,
                "device": item["device"],
            })

    return results


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Cost estimate first
    total_shots, cost_low, cost_high = print_cost_estimate()

    # User confirmation
    print(f"\n⚠  You are about to submit {total_shots} shots to {DEVICE_TYPE}.")
    if DEVICE_TYPE == "FRESNEL":
        print(f"   This will use real QPU time (est. €{cost_low:.2f}–€{cost_high:.2f}).")

    confirm = input("\n  Continue? [y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Aborted.")
        sys.exit(0)

    # Authenticate
    sdk = get_client()

    # Submit
    print("=" * 60)
    print(f"  FRESNEL Validation — 3-Point Check")
    print(f"  γ = {GAMMA_POINTS}")
    print("=" * 60)

    batches = submit_hardware(sdk, GAMMA_POINTS, RUNS, DEVICE_TYPE)

    # Collect
    print("\n--- Waiting for results ---")
    print("  (FRESNEL jobs may queue — this could take several minutes)")
    results = collect_results(sdk, batches)

    # Save
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"fresnel_validation_{timestamp}.json")
    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {filename}")

    # Summary
    print("\n" + "=" * 60)
    print("  FRESNEL Validation Summary")
    print("=" * 60)
    for r in results:
        gamma  = r.get("gamma", "?")
        status = r.get("status", "?")
        counts = r.get("counts")
        device = r.get("device", "?")
        shots  = r.get("shots", 0)

        if counts:
            n_qubits = len(next(iter(counts)))
            ground   = counts.get("0" * n_qubits, 0)
            p0       = ground / shots * 100 if shots > 0 else 0
            n_states = len(counts)
            print(f"  γ={gamma:.3f}  [{device}]  {status}  "
                  f"shots={shots}  P₀={p0:.1f}%  states={n_states}")
        else:
            print(f"  γ={gamma:.3f}  [{device}]  {status}")

    # Compare with emulator
    print("\n--- Emulator vs Hardware Comparison ---")
    emu_ref = {0.05: 0.12, 0.20: 0.72, 0.40: 0.93}  # approx P₀ from EMU_FREE
    for r in results:
        if r.get("counts"):
            gamma = r["gamma"]
            counts = r["counts"]
            shots = r["shots"]
            n_q = len(next(iter(counts)))
            hw_p0 = counts.get("0" * n_q, 0) / shots if shots > 0 else 0
            emu_p0 = emu_ref.get(gamma, "N/A")
            if isinstance(emu_p0, float):
                delta = hw_p0 - emu_p0
                print(f"  γ={gamma:.3f}:  EMU_FREE P₀={emu_p0:.1%}  |  "
                      f"FRESNEL P₀={hw_p0:.1%}  |  Δ={delta:+.1%}")
            else:
                print(f"  γ={gamma:.3f}:  FRESNEL P₀={hw_p0:.1%}")
