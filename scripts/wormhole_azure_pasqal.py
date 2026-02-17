import os
import json
import time
import numpy as np
from azure.quantum import Workspace
from azure.quantum.target.pasqal import Pasqal
from azure.identity import DeviceCodeCredential

# Import our sequence builder
try:
    from wormhole_pulser_continuous import build_wormhole_sequence
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../code'))
    from wormhole_pulser_continuous import build_wormhole_sequence

# ============================================================================
# 1. SETUP AZURE WORKSPACE
# ============================================================================

# Default values — override via environment variables or .env file
DEFAULTS = {
    "AZURE_LOCATION": "eastus",
}


def get_workspace():
    """Authenticate and return an Azure Quantum Workspace handle."""

    tenant_id = os.environ.get("AZURE_TENANT_ID")
    resource_id = os.environ.get("AZURE_RESOURCE_ID")
    location = os.environ.get("AZURE_LOCATION", DEFAULTS["AZURE_LOCATION"])

    # We check for missing vars in __main__, but good to check here too if called as lib
    if not tenant_id or not resource_id:
        raise EnvironmentError(
            "AZURE_TENANT_ID and AZURE_RESOURCE_ID must be set as environment "
            "variables. Example:\n"
            "  export AZURE_TENANT_ID='5b322a00-...'\n"
            "  export AZURE_RESOURCE_ID='/subscriptions/fe4d586e-...'"
        )

    print(f"Authenticating to Azure (Location: {location})...")
    credential = DeviceCodeCredential(tenant_id=tenant_id)

    workspace = Workspace(
        resource_id=resource_id,
        location=location,
        credential=credential,
    )
    return workspace


# ============================================================================
# 2. JOB SUBMISSION
# ============================================================================

def submit_experiment(workspace, gamma_values=None, shots=100):
    """Build and submit one job per gamma value to the Pasqal emulator."""

    if gamma_values is None:
        gamma_values = [0.0, 0.535]

    target = Pasqal(workspace, name="pasqal.sim.emu-tn")
    print(f"Connected to target: {target.name}")

    jobs = []

    for gamma in gamma_values:
        print(f"\n--- Preparing job for gamma = {gamma} ---")

        # Build the Pulser sequence and serialize to the JSON format
        # that the Azure Pasqal target expects.
        seq = build_wormhole_sequence(gamma=gamma, coupling_time=500)
        json_str = seq.to_abstract_repr()
        
        # --- DEBUG: Modify JSON for Backend Compatibility ---
        # The Azure backend often rejects the 'device' field if it conflicts 
        # with its own device definition, or if the schema validation is strict.
        # We try removing it.
        data = json.loads(json_str)
        if 'device' in data:
            del data['device']

        # --- FIX: Inject 'z' coordinate if missing ---
        # Some Pasqal backend validators strictly require 3D coordinates.
        if 'register' in data and isinstance(data['register'], list):
            for atom in data['register']:
                if 'z' not in atom:
                    atom['z'] = 0.0
        
        # Save exact JSON being submitted for debugging
        debug_filename = f"debug_sequence_g{gamma}.json"
        with open(debug_filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        serialized = json.dumps(data) # Correctly serialize to string

        print(f"Submitting job (gamma={gamma}, shots={shots})...")
        try:
            job = target.submit(
                input_data=serialized,
                name=f"wormhole_cfd_g{gamma}",
                shots=shots,
            )
            print(f"Job ID: {job.id}")
            jobs.append({"gamma": gamma, "job": job})
        except Exception as e:
            print(f"Failed to submit (gamma={gamma}): {e}")

    return jobs


# ============================================================================
# 3. RESULT RETRIEVAL
# ============================================================================

def wait_and_save_results(jobs, output_dir="."):
    """Poll submitted jobs, collect results, and write them to a JSON file."""

    print("\n--- Waiting for results ---")
    results_data = []

    for item in jobs:
        gamma = item["gamma"]
        job = item["job"]

        print(f"Waiting for job {job.id} (gamma={gamma})...")
        try:
            job.wait_until_completed(timeout_secs=300)

            status = job.details.status
            if status == "Succeeded":
                result = job.get_results()
                # result is typically a dict of bitstring counts:
                # {'00101': 12, '11010': 38, ...}
                print(f"  -> Success! Unique bitstrings: {len(result)}")

                results_data.append({
                    "gamma": gamma,
                    "job_id": job.id,
                    "counts": result,
                    "status": "Succeeded",
                })
            else:
                print(f"  -> Job ended with status: {status}")
                # --- Diagnostics: print ALL available error info ---
                details = job.details
                for attr in ("error_data", "error", "failure_info"):
                    val = getattr(details, attr, None)
                    if val:
                        print(f"     {attr}: {val}")
                # Try dict-style access on error_data
                err = getattr(details, "error_data", None)
                if err and hasattr(err, "__dict__"):
                    print(f"     error_data fields: {vars(err)}")
                results_data.append({
                    "gamma": gamma,
                    "job_id": job.id,
                    "counts": None,
                    "status": str(status),
                    "error": str(getattr(details, "error_data", "")),
                })

        except Exception as e:
            print(f"  -> Error retrieving result for job {job.id}: {e}")

    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"pasqal_emu_results_{timestamp}.json")

    with open(filename, "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"\nResults saved to {filename}")
    return results_data


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    missing = [v for v in ("AZURE_TENANT_ID", "AZURE_RESOURCE_ID")
               if not os.environ.get(v)]
    if missing:
        print(f"WARNING: Missing environment variables: {', '.join(missing)}")
        print("Set them before running, e.g.:")
        print("  export AZURE_TENANT_ID='your-tenant-id'")
        print("  export AZURE_RESOURCE_ID='your-resource-id'")
        print()
        # We don't exit here so the user sees the error from get_workspace or can set them interactively if code was modified
    
    try:
        ws = get_workspace()

        # Three distinct coupling regimes:
        #   Vacuum (0.0), Critical (0.535), Deep (0.8)
        submitted_jobs = submit_experiment(
            ws,
            gamma_values=[0.0, 0.535, 0.8],
            shots=50,
        )
        wait_and_save_results(submitted_jobs)

    except Exception as e:
        print(f"Fatal error: {e}")
