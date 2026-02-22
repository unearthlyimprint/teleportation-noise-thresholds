"""
Fetch FRESNEL_CAN1 Results from Pasqal Cloud
=============================================
Lists all FRESNEL_CAN1 batches in the project and downloads
results for any that have completed successfully.

Usage:
    source ../pasqal_env/bin/activate
    python fetch_fresnel_results.py
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from pasqal_cloud import SDK
from pasqal_cloud.utils.filters import BatchFilters, PaginationParams
from pasqal_cloud.utils.constants import BatchStatus


# ============================================================================
# AUTHENTICATION
# ============================================================================

def get_client() -> SDK:
    project_id = os.environ.get("PASQAL_PROJECT_ID")
    username   = os.environ.get("PASQAL_USERNAME")
    password   = os.environ.get("PASQAL_PASSWORD")

    if not all([project_id, username, password]):
        print("ERROR: Set PASQAL_PROJECT_ID, PASQAL_USERNAME, PASQAL_PASSWORD")
        sys.exit(1)

    print(f"Authenticating (project: {project_id[:8]}...)...", end=" ")
    sdk = SDK(project_id=project_id, username=username, password=password)
    print("OK\n")
    return sdk


# ============================================================================
# MAIN
# ============================================================================

def main():
    sdk = get_client()

    # ── 1. List ALL FRESNEL_CAN1 batches (any status) ──
    print("=" * 70)
    print("  Fetching ALL FRESNEL_CAN1 batches from Pasqal Cloud")
    print("=" * 70)

    all_batches = []
    offset = 0
    while True:
        resp = sdk.get_batches(
            filters=BatchFilters(device_type="FRESNEL_CAN1"),
            pagination_params=PaginationParams(offset=offset, limit=100),
        )
        all_batches.extend(resp.results)
        if len(all_batches) >= resp.total or len(resp.results) == 0:
            break
        offset += len(resp.results)

    print(f"\n  Total FRESNEL_CAN1 batches found: {len(all_batches)}")
    if not all_batches:
        print("  No FRESNEL_CAN1 batches found in project.")
        # Also try without device filter to see what's there
        print("\n  Checking ALL batches in project...")
        resp = sdk.get_batches(
            pagination_params=PaginationParams(offset=0, limit=100),
        )
        print(f"  Total batches in project: {resp.total}")
        for b in resp.results:
            print(f"    {b.id}  device={b.device_type}  status={b.status}  "
                  f"created={b.created_at}")
        return

    # ── 2. Display status of each batch ──
    print(f"\n{'─' * 70}")
    print(f"  {'Batch ID':<40} {'Status':<12} {'Device':<16} {'Created'}")
    print(f"{'─' * 70}")
    done_batches = []
    for b in all_batches:
        print(f"  {b.id:<40} {b.status:<12} {b.device_type:<16} {b.created_at}")
        if b.status == "DONE":
            done_batches.append(b)

    print(f"\n  DONE batches: {len(done_batches)} / {len(all_batches)}")

    if not done_batches:
        print("\n  No completed batches to fetch results from.")
        # Show pending/running
        pending = [b for b in all_batches if b.status in ("PENDING", "RUNNING")]
        if pending:
            print(f"  Still pending/running: {len(pending)}")
            for b in pending:
                print(f"    {b.id}  status={b.status}  created={b.created_at}")
        return

    # ── 3. Fetch results for each DONE batch ──
    print(f"\n{'=' * 70}")
    print(f"  Downloading results for {len(done_batches)} completed batch(es)")
    print(f"{'=' * 70}")

    all_results = []
    for batch in done_batches:
        print(f"\n  Batch {batch.id}:")
        print(f"    Status:  {batch.status}")
        print(f"    Created: {batch.created_at}")
        print(f"    Updated: {batch.updated_at}")

        # Fetch full batch with jobs
        full_batch = sdk.get_batch(batch.id)
        jobs = full_batch.ordered_jobs
        print(f"    Jobs:    {len(jobs)}")

        for i, job in enumerate(jobs):
            raw_counts = job.result if hasattr(job, 'result') and job.result else None
            shots = sum(raw_counts.values()) if raw_counts else 0
            n_qubits = len(next(iter(raw_counts))) if raw_counts else 0
            unique_states = len(raw_counts) if raw_counts else 0

            print(f"    Job {i+1}/{len(jobs)}: id={job.id}  status={job.status}  "
                  f"shots={shots}  qubits={n_qubits}  states={unique_states}")

            result_entry = {
                "batch_id": batch.id,
                "job_id": job.id,
                "job_index": i,
                "status": job.status,
                "device_type": batch.device_type,
                "created_at": batch.created_at,
                "updated_at": batch.updated_at,
                "total_shots": shots,
                "n_qubits": n_qubits,
                "unique_states": unique_states,
                "raw_counts": raw_counts,
            }

            # If we have result data, compute some basic stats
            if raw_counts and shots > 0:
                # Ground-state probability (all zeros)
                ground_state = "0" * n_qubits
                p_ground = raw_counts.get(ground_state, 0) / shots

                # Mean excitation density
                rho = sum(
                    bs.count("1") / n_qubits * count
                    for bs, count in raw_counts.items()
                ) / shots

                result_entry["p_ground"] = p_ground
                result_entry["mean_rho"] = rho

                print(f"      P(ground) = {p_ground:.4f}  "
                      f"⟨n⟩ = {rho:.4f}")

            all_results.append(result_entry)

    # ── 4. Save results ──
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"fresnel_can1_{timestamp}.json")

    # Save full results (with raw counts)
    with open(filename, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  ✅ Full results saved to: {filename}")

    # Also save a compact summary (without raw counts)
    summary_file = os.path.join(output_dir, f"fresnel_can1_summary_{timestamp}.json")
    summary = [{k: v for k, v in r.items() if k != "raw_counts"} for r in all_results]
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  📋 Summary saved to:     {summary_file}")

    # ── 5. Print overall summary ──
    total_shots = sum(r.get("total_shots", 0) for r in all_results)
    print(f"\n{'=' * 70}")
    print(f"  FRESNEL_CAN1 Results Summary")
    print(f"{'=' * 70}")
    print(f"  Total batches:  {len(done_batches)}")
    print(f"  Total jobs:     {len(all_results)}")
    print(f"  Total shots:    {total_shots}")
    print()
    for r in all_results:
        if r.get("p_ground") is not None:
            print(f"  Job {r['job_id'][:8]}...  "
                  f"shots={r['total_shots']}  "
                  f"qubits={r['n_qubits']}  "
                  f"P₀={r['p_ground']:.4f}  "
                  f"⟨n⟩={r['mean_rho']:.4f}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
