"""
CFD Wormhole — Native Pasqal Cloud Submission
===============================================
Uses the pasqal-cloud SDK directly (no Azure wrapper) to submit
wormhole sequences to Pasqal's cloud emulators (EMU_FREE / EMU_MPS).

Credentials
-----------
Set the following environment variables before running:
    export PASQAL_PROJECT_ID="your-project-id"
    export PASQAL_USERNAME="your-email@example.com"
    export PASQAL_PASSWORD="your-password"

Usage
-----
    source ../pasqal_env/bin/activate
    python run_wormhole_pasqal.py
"""

import os
import sys
import time
import json

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from pasqal_cloud import SDK
from pasqal_cloud.device import EmulatorType, DeviceTypeName
from wormhole_pulser_continuous import build_wormhole_sequence


# ============================================================================
# 1. AUTHENTICATION
# ============================================================================

def get_client() -> SDK:
    """Create an authenticated Pasqal Cloud SDK client."""

    project_id = os.environ.get("PASQAL_PROJECT_ID")
    username   = os.environ.get("PASQAL_USERNAME")
    password   = os.environ.get("PASQAL_PASSWORD")

    if not project_id:
        print("ERROR: PASQAL_PROJECT_ID not set.")
        print("  export PASQAL_PROJECT_ID='your-project-id'")
        sys.exit(1)
    if not username or not password:
        print("ERROR: PASQAL_USERNAME and PASQAL_PASSWORD not set.")
        print("  export PASQAL_USERNAME='your-email@example.com'")
        print("  export PASQAL_PASSWORD='your-password'")
        sys.exit(1)

    print(f"Authenticating with Pasqal Cloud (project: {project_id[:8]}...)...")
    sdk = SDK(
        project_id=project_id,
        username=username,
        password=password,
    )
    print("Authenticated successfully.\n")
    return sdk


# ============================================================================
# 2. BATCH SUBMISSION
# ============================================================================

def submit_gamma_sweep(
    sdk: SDK,
    gamma_values: list[float] | None = None,
    runs: int = 100,
    device_type: str = "EMU_FREE",
):
    """
    Submit one batch per gamma value to a Pasqal emulator.

    Parameters
    ----------
    sdk : SDK
        Authenticated Pasqal Cloud client.
    gamma_values : list[float]
        CFD decoherence values to sweep.
    runs : int
        Number of samples (shots) per job.
    device_type : str
        Which emulator to target. Options:
        - "EMU_FREE"  (Explorer plan, free)
        - "EMU_MPS"   (replaces deprecated EMU_TN)
        - "FRESNEL"   (QPU hardware)

    Returns
    -------
    list[dict]
        Per-gamma batch metadata for tracking.
    """
    if gamma_values is None:
        gamma_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.535, 0.7, 0.8, 1.0]

    batches = []

    for gamma in gamma_values:
        print(f"γ = {gamma:.3f}  →  building sequence...", end="  ")
        seq = build_wormhole_sequence(gamma=gamma, coupling_time=500)
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
            })
        except Exception as e:
            print(f"FAILED: {e}")
            batches.append({
                "gamma": gamma,
                "batch_id": None,
                "status": "SUBMIT_ERROR",
                "error": str(e),
            })

    return batches


# ============================================================================
# 3. RESULT COLLECTION
# ============================================================================

def collect_results(sdk: SDK, batches: list[dict], poll_interval: int = 5):
    """
    Poll each batch until completion and collect measurement counts.
    """
    results = []

    for item in batches:
        if item["batch_id"] is None:
            results.append(item)
            continue

        gamma    = item["gamma"]
        batch_id = item["batch_id"]
        print(f"\nPolling γ={gamma:.3f} (batch {batch_id})...", end="")

        while True:
            batch = sdk.get_batch(batch_id)
            if batch.status not in ("PENDING", "RUNNING"):
                break
            print(".", end="", flush=True)
            time.sleep(poll_interval)

        print(f"  → {batch.status}")

        if batch.status == "DONE":
            for job in batch.ordered_jobs:
                if job.status == "DONE" and hasattr(job, 'result') and job.result:
                    results.append({
                        "gamma": gamma,
                        "batch_id": batch_id,
                        "job_id": job.id,
                        "status": "DONE",
                        "counts": job.result,
                    })
                else:
                    # Try fetching results via SDK
                    try:
                        job_result = sdk._client.get_job_results(job.id)
                        counts = job_result.counter if job_result else None
                        results.append({
                            "gamma": gamma,
                            "batch_id": batch_id,
                            "job_id": job.id,
                            "status": job.status,
                            "counts": counts,
                        })
                    except Exception as e:
                        results.append({
                            "gamma": gamma,
                            "batch_id": batch_id,
                            "job_id": job.id,
                            "status": job.status,
                            "error": str(e),
                        })
        else:
            results.append({
                "gamma": gamma,
                "batch_id": batch_id,
                "status": batch.status,
            })

    return results


# ============================================================================
# 4. SAVE
# ============================================================================

def save_results(results: list[dict], output_dir: str = "../results"):
    """Save results to a timestamped JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"pasqal_emu_tn_{timestamp}.json")

    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {filename}")
    return filename


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Authenticate
    sdk = get_client()

    # Submit jobs
    print("=" * 60)
    print("  CFD Wormhole Stability — Pasqal Cloud Sweep")
    print("=" * 60)

    batches = submit_gamma_sweep(sdk, runs=100)

    # Collect results
    results = collect_results(sdk, batches)

    # Save
    save_results(results)

    # Quick summary
    print("\n--- Summary ---")
    for r in results:
        gamma = r.get("gamma", "?")
        status = r.get("status", "?")
        counts = r.get("counts")
        n_states = len(counts) if counts else 0
        print(f"  γ={gamma:.3f}  status={status}  distinct_states={n_states}")
