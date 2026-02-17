import os
import json
from azure.quantum import Workspace
from azure.quantum.target.pasqal import Pasqal
from azure.identity import DeviceCodeCredential

def submit_structure(target, data, name):
    print(f"\n--- Submitting Structure: {name} ---")
    print(f"Payload: {json.dumps(data)}")
    
    # We must bypass any SDK logic that wraps this.
    # But Target.submit() just uploads 'input_data' as a blob.
    
    serialized = json.dumps(data)
    try:
        job = target.submit(
            input_data=serialized,
            name=f"debug_{name}",
            shots=10
        )
        print(f"Job ID: {job.id}")
        job.wait_until_completed(timeout_secs=60)
        
        if job.details.status == "Failed":
             print(f"Error: {job.details.error_data}")
        else:
             print("SUCCESS!")
             
    except Exception as e:
        print(f"Exception: {e}")

def run_probes():
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    resource_id = os.environ.get("AZURE_RESOURCE_ID")
    location = os.environ.get("AZURE_LOCATION", "eastus")
    
    if not tenant_id:
        print("Set AZURE env vars!")
        return

    credential = DeviceCodeCredential(tenant_id=tenant_id)
    ws = Workspace(resource_id=resource_id, location=location, credential=credential)
    target = Pasqal(ws, name="pasqal.sim.emu-tn")
    
    # Probe 1: Empty Object
    submit_structure(target, {}, "empty")
    
    # Probe 2: Nested sequence field
    # (common in some backends)
    pulser_json = '{"register": [{"name": "q0", "x": 0, "y": 0, "z": 0}], "channels": {"rydberg": "rydberg_global"}, "operations": [], "measurement": "ground-rydberg", "version": "1"}'
    valid_seq = json.loads(pulser_json)
    
    submit_structure(target, {"sequence": valid_seq}, "nested_sequence")
    
    # Probe 3: Nested data field
    submit_structure(target, {"data": valid_seq}, "nested_data")
    
    # Probe 4: Input format explicit
    # Maybe the backend ignores our metadata and tries to parse the string?
    # This probes if the JSON ITSELF is expected to have a 'sequence' key.

if __name__ == "__main__":
    run_probes()
