"""
CFD Wormhole — Emulator Comparison
==================================
Runs a 3-point check on three different Pasqal emulators:
  1. EMU_FREE    (Standard approximate emulator)
  2. EMU_SV      (Exact State Vector — "Ground Truth")
  3. EMU_FRESNEL (Realistic Noise Model — "Hardware Simulation")

Points:
  γ = 0.05  (Open)
  γ = 0.20  (Critical)
  γ = 0.40  (Collapsed)

Usage:
    python run_emulator_comparison.py
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from pasqal_cloud import SDK
from wormhole_pulser_continuous import build_wormhole_sequence

GAMMA_POINTS = [0.05, 0.20, 0.40]
RUNS = 200
EMULATORS = ["EMU_FREE", "EMU_SV", "EMU_FRESNEL"]


def get_client() -> SDK:
    project_id = os.environ.get("PASQAL_PROJECT_ID")
    username   = os.environ.get("PASQAL_USERNAME")
    password   = os.environ.get("PASQAL_PASSWORD")

    if not all([project_id, username, password]):
        print("ERROR: Set PASQAL_PROJECT_ID, PASQAL_USERNAME, PASQAL_PASSWORD")
        sys.exit(1)

    print(f"Authenticating...", end=" ")
    sdk = SDK(project_id=project_id, username=username, password=password)
    print("OK\n")
    return sdk


def submit_batch(sdk, gamma, device_type):
    print(f"  γ={gamma:.2f} @ {device_type:<12} ...", end=" ")
    try:
        # Use TriangularLatticeLayout only for FRESNEL devices
        use_fresnel = (device_type == "EMU_FRESNEL" or device_type == "FRESNEL")
        
        seq = build_wormhole_sequence(gamma=gamma, coupling_time=500, use_fresnel_layout=use_fresnel)
        serialized = seq.to_abstract_repr()
        
        batch = sdk.create_batch(
            serialized_sequence=serialized,
            jobs=[{"runs": RUNS}],
            device_type=device_type,
        )
        print(f"Batch {batch.id}")
        return {
            "gamma": gamma,
            "device": device_type,
            "batch_id": batch.id,
            "status": batch.status
        }
    except Exception as e:
        print(f"FAILED: {e}")
        return {
            "gamma": gamma,
            "device": device_type,
            "batch_id": None,
            "status": "ERROR",
            "error": str(e)
        }


def collect_results(sdk, batches):
    results = []
    print("\n--- Polling Results ---")
    
    for item in batches:
        if item["batch_id"] is None:
            results.append(item)
            continue

        gamma = item["gamma"]
        device = item["device"]
        batch_id = item["batch_id"]
        
        print(f"  Polling γ={gamma:.2f} ({device})...", end="", flush=True)
        
        while True:
            batch = sdk.get_batch(batch_id)
            if batch.status not in ("PENDING", "RUNNING"):
                break
            print(".", end="", flush=True)
            time.sleep(2)
            
        print(f" → {batch.status}")
        
        if batch.status == "DONE":
            for job in batch.ordered_jobs:
                counts = job.result if hasattr(job, 'result') else None
                n_shots = sum(counts.values()) if counts else 0
                p0 = counts.get("0"*9, 0) / n_shots if n_shots > 0 else 0
                
                results.append({
                    "gamma": gamma,
                    "device": device,
                    "status": "DONE",
                    "p0": p0,
                    "counts": counts
                })
        else:
            results.append({
                "gamma": gamma,
                "device": device,
                "status": batch.status
            })
            
    return results


if __name__ == "__main__":
    sdk = get_client()

    print("=" * 60)
    print("  Emulator Comparison: FREE vs. SV vs. FRESNEL")
    print(f"  Points: {GAMMA_POINTS}")
    print("=" * 60)

    # Submit all
    all_batches = []
    for gamma in GAMMA_POINTS:
        for emu in EMULATORS:
            # Skip invalid combinations if known (e.g. project constraints)
            # But based on dashboard, all should overlap if permissions are right
            try:
                b = submit_batch(sdk, gamma, emu)
                all_batches.append(b)
            except Exception as e:
                print(f"  Skipping {emu}: {e}")

    # Collect
    results = collect_results(sdk, all_batches)

    # Save
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(out_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"emulator_comparison_{timestamp}.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print Comparison Table
    print("\n" + "=" * 60)
    print(f"  {'γ':<6} | {'EMU_FREE P₀':<12} | {'EMU_SV P₀':<12} | {'EMU_FRESNEL P₀':<14}")
    print("-" * 60)
    
    # Organize data for table
    table_data = {g: {} for g in GAMMA_POINTS}
    for r in results:
        g = r.get("gamma")
        d = r.get("device")
        p0 = r.get("p0", -1)
        if g in table_data:
            table_data[g][d] = p0

    for g in GAMMA_POINTS:
        p_free = table_data[g].get("EMU_FREE", -1)
        p_sv   = table_data[g].get("EMU_SV", -1)
        p_fres = table_data[g].get("EMU_FRESNEL", -1)
        
        def fmt(val): return f"{val:.1%}" if val >= 0 else "N/A"
        
        print(f"  {g:<6.2f} | {fmt(p_free):<12} | {fmt(p_sv):<12} | {fmt(p_fres):<14}")
    print("=" * 60)
