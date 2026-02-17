"""
CFD Wormhole — Fine γ Sweep Near Critical Point
=================================================
Submits batches with finer resolution around the phase transition
(γ = 0.15 to 0.60, step 0.025) to resolve the critical region.

Submits in waves of 8 to respect the Explorer plan's 10-job limit.

Usage:
    source ../pasqal_env/bin/activate
    python run_fine_sweep.py
"""

import os
import sys
import time
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from pasqal_cloud import SDK
from wormhole_pulser_continuous import build_wormhole_sequence

WAVE_SIZE = 8       # Max concurrent batches (Explorer limit = 10)
POLL_INTERVAL = 3   # Seconds between status checks


def get_client() -> SDK:
    project_id = os.environ.get("PASQAL_PROJECT_ID")
    username   = os.environ.get("PASQAL_USERNAME")
    password   = os.environ.get("PASQAL_PASSWORD")

    if not all([project_id, username, password]):
        print("ERROR: Set PASQAL_PROJECT_ID, PASQAL_USERNAME, PASQAL_PASSWORD")
        sys.exit(1)

    sdk = SDK(project_id=project_id, username=username, password=password)
    print("Authenticated.\n")
    return sdk


def submit_wave(sdk, gamma_slice, runs, device_type):
    """Submit a wave of batches and return their metadata."""
    wave_batches = []
    for gamma in gamma_slice:
        print(f"  γ = {gamma:.3f}  →  ", end="")
        seq = build_wormhole_sequence(gamma=gamma, coupling_time=500)
        serialized = seq.to_abstract_repr()

        try:
            batch = sdk.create_batch(
                serialized_sequence=serialized,
                jobs=[{"runs": runs}],
                device_type=device_type,
            )
            print(f"batch {batch.id}")
            wave_batches.append({"gamma": gamma, "batch_id": batch.id, "status": batch.status})
        except Exception as e:
            print(f"FAILED: {e}")
            wave_batches.append({"gamma": gamma, "batch_id": None, "status": "SUBMIT_ERROR", "error": str(e)})

    return wave_batches


def wait_for_wave(sdk, wave_batches):
    """Poll all batches in a wave until they complete. Returns results."""
    results = []
    for item in wave_batches:
        if item["batch_id"] is None:
            results.append(item)
            continue

        gamma    = item["gamma"]
        batch_id = item["batch_id"]
        print(f"  Polling γ={gamma:.3f}...", end="", flush=True)

        while True:
            batch = sdk.get_batch(batch_id)
            if batch.status not in ("PENDING", "RUNNING"):
                break
            print(".", end="", flush=True)
            time.sleep(POLL_INTERVAL)

        print(f" → {batch.status}")

        if batch.status == "DONE":
            for job in batch.ordered_jobs:
                results.append({
                    "gamma": gamma,
                    "batch_id": batch_id,
                    "job_id": job.id,
                    "status": job.status,
                    "counts": job.result if hasattr(job, 'result') else None,
                })
        else:
            results.append({"gamma": gamma, "batch_id": batch_id, "status": batch.status})

    return results


if __name__ == "__main__":
    sdk = get_client()

    # Fine sweep: 0.15 to 0.60 in steps of 0.025  (19 points)
    gamma_values = list(np.arange(0.15, 0.625, 0.025))
    gamma_values = [round(g, 3) for g in gamma_values]
    runs = 200          # More shots for better statistics
    device_type = "EMU_FREE"  # Only emulator available on Explorer plan

    print("=" * 60)
    print("  Fine γ Sweep — Critical Region (0.15–0.60)")
    print(f"  {len(gamma_values)} points × {runs} runs on {device_type}")
    print(f"  Submitting in waves of {WAVE_SIZE}")
    print("=" * 60)

    # Split into waves
    all_results = []
    n_waves = (len(gamma_values) + WAVE_SIZE - 1) // WAVE_SIZE

    for w in range(n_waves):
        start = w * WAVE_SIZE
        end   = min(start + WAVE_SIZE, len(gamma_values))
        gamma_slice = gamma_values[start:end]

        print(f"\n--- Wave {w+1}/{n_waves} ({len(gamma_slice)} batches) ---")
        wave_batches = submit_wave(sdk, gamma_slice, runs, device_type)

        print(f"\n  Waiting for wave {w+1} to complete...")
        wave_results = wait_for_wave(sdk, wave_batches)
        all_results.extend(wave_results)

        if w < n_waves - 1:
            print(f"  Wave {w+1} done. Pausing 5s before next wave...")
            time.sleep(5)

    # Save
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"pasqal_fine_sweep_{timestamp}.json")
    with open(filename, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nResults saved to: {filename}")

    # Summary
    print("\n--- Summary ---")
    for r in all_results:
        gamma = r.get("gamma", "?")
        status = r.get("status", "?")
        counts = r.get("counts")
        n = len(counts) if counts else 0
        gp = counts.get("0" * 9, 0) / sum(counts.values()) * 100 if counts and sum(counts.values()) > 0 else 0
        print(f"  γ={gamma:.3f}  status={status}  states={n}  P₀={gp:.0f}%")
