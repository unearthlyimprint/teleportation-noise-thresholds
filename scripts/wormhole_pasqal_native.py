import os
import time
import json
from pasqal_cloud import SDK
from pasqal_cloud.device import EmulatorType

# Import our sequence builder
# Ensure this script is run from the project root or the path is correct
try:
    from wormhole_pulser_continuous import build_wormhole_sequence
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../code'))
    from wormhole_pulser_continuous import build_wormhole_sequence

# ============================================================================
# 1. SETUP PASQAL CLOUD CLIENT
# ============================================================================

def get_client():
    """Authenticate with Pasqal Cloud using Client ID and Secret."""
    
    # Credentials must be set in environment variables
    project_id = os.environ.get("PASQAL_PROJECT_ID")
    username = os.environ.get("PASQAL_USERNAME") # Or Client ID often used as username in some contexts, but usually it's Client ID/Secret
    password = os.environ.get("PASQAL_PASSWORD") # Or Client Secret
    
    # Modern Pasqal SDK uses Client ID / Secret via Auth0
    client_id = os.environ.get("PASQAL_CLIENT_ID")
    client_secret = os.environ.get("PASQAL_CLIENT_SECRET")
    
    if not project_id:
        raise EnvironmentError("PASQAL_PROJECT_ID is missing.")
        
    if not client_id or not client_secret:
        raise EnvironmentError(
            "PASQAL_CLIENT_ID and PASQAL_CLIENT_SECRET are required for native SDK access."
        )

    print(f"Authenticating to Pasqal Cloud (Project: {project_id})...")
    
    # Data is passed to SDK constructor
    # The SDK handles Auth0 flow automatically if client_id/secret are provided 
    # (though typically mapped to username/password params in some versions, 
    # let's check exact usage or use the correct auth provider).
    
    # Based on pasqal-cloud source we inspected:
    # Client(project_id=..., username=..., password=...)
    # Logic: if username/password provided, it uses Auth0TokenProvider(username, password)
    # For Machine-to-Machine (M2M) credentials (Client ID/Secret), the flow is slightly different
    # but often Client ID = username, Client Secret = password works for M2M if configured.
    
    client = SDK(
        project_id=project_id,
        username=client_id,
        password=client_secret,
        # endpoints=... if needed
    )
    return client

# ============================================================================
# 2. JOB SUBMISSION
# ============================================================================

def submit_experiment(client, gamma_values=None, runs=100):
    """Submit batch of jobs to Emulator."""
    
    if gamma_values is None:
        gamma_values = [0.0, 0.535, 0.8]

    # Target: Emulator Tensor Network
    # Use the enum from pasqal_cloud
    device_type = EmulatorType.EMU_TN 
    
    print(f"Targeting: {device_type}")

    jobs_info = []

    for gamma in gamma_values:
        print(f"\n--- Preparing Batch for gamma = {gamma} ---")

        # 1. Build Sequence
        seq = build_wormhole_sequence(gamma=gamma, coupling_time=500)
        
        # 2. Create Batch
        print("Creating Batch...")
        try:
            batch = client.create_batch(
                serialized_sequence=seq.to_abstract_repr(),
                jobs=[{"runs": runs, "variables": {}}], # Defined at batch creation
                emulator=device_type,
                # configuration=EmuTNConfig(dt=10.0, ...) # Optional config
            )
            
            print(f"Batch created with ID: {batch.id}")
            jobs_info.append({"gamma": gamma, "batch": batch})
            
        except Exception as e:
            print(f"Failed to submit batch (gamma={gamma}): {e}")

    return jobs_info

# ============================================================================
# 3. RESULT RETRIEVAL
# ============================================================================

def wait_and_save_results(client, jobs_info, output_dir="."):
    """Poll batches."""
    print("\n--- Waiting for results ---")
    results_data = []

    for item in jobs_info:
        gamma = item["gamma"]
        batch = item["batch"]
        
        print(f"Waiting for Batch {batch.id} (gamma={gamma})...")
        
        # Wait for termination
        while batch.status in ["PENDING", "RUNNING"]:
            time.sleep(2)
            batch = client.get_batch(batch.id) # Refresh
            
        print(f"Batch Status: {batch.status}")
        
        # Fetch results
        if batch.status == "DONE":
            # Native SDK might require iterating jobs
            for job in batch.ordered_jobs:
                print(f"  Job {job.id}: {job.status}")
                if job.status == "DONE":
                    # Fetch detailed result (counts)
                    # job.result is a convenience property?
                    # or client.get_job_result(job.id)
                    res = client.get_job_results(job.id)
                    if res:
                        print(f"    Result count: {len(res.counter)}")
                        results_data.append({
                            "gamma": gamma,
                            "batch_id": batch.id,
                            "job_id": job.id,
                            "counts": res.counter
                        })
        else:
            print("  Batch failed or cancelled.")
            results_data.append({
                "gamma": gamma,
                "batch_id": batch.id,
                "status": batch.status
            })

    # Save
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"pasqal_native_results_{timestamp}.json")
    
    with open(filename, "w") as f:
        json.dump(results_data, f, indent=2)
        
    print(f"\nResults saved to {filename}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        client = get_client()
        jobs = submit_experiment(client, runs=50) # Small test
        wait_and_save_results(client, jobs)
    except Exception as e:
        print(f"Fatal Error: {e}")
