import os
import json
from azure.quantum import Workspace
from azure.quantum.target.pasqal import Pasqal
from azure.identity import DeviceCodeCredential
from pulser import Sequence, Register
from pulser.devices import AnalogDevice

def submit_to_target(ws, target_name):
    print(f"\n--- Testing Target: {target_name} ---")
    try:
        target = Pasqal(ws, name=target_name)
        
        # Trivial Sequence
        reg = Register.from_coordinates([(0,0)], prefix="q")
        seq = Sequence(reg, AnalogDevice)
        seq.declare_channel("rydberg", "rydberg_global")
        seq.measure("ground-rydberg")
        
        json_str = seq.to_abstract_repr()
        
        # Standard pruning
        data = json.loads(json_str)
        if 'device' in data: del data['device']
        serialized = json.dumps(data)
        
        job = target.submit(
            input_data=serialized,
            name=f"test_{target_name}",
            shots=10
        )
        print(f"Job ID: {job.id}")
        job.wait_until_completed(timeout_secs=60)
        
        if job.details.status == "Succeeded":
            print("SUCCESS")
        else:
            print(f"FAILED: {job.details.error_data}")
            
    except Exception as e:
        print(f"Error submitting to {target_name}: {e}")

def run_targets():
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    resource_id = os.environ.get("AZURE_RESOURCE_ID")
    location = os.environ.get("AZURE_LOCATION", "eastus")
    
    if not tenant_id:
        print("Set AZURE env vars!")
        return

    credential = DeviceCodeCredential(tenant_id=tenant_id)
    ws = Workspace(resource_id=resource_id, location=location, credential=credential)
    
    # List of known targets
    targets = [
        "pasqal.sim.emu-tn",
        "pasqal.sim.emu-sv",  # State Vector (might be stricter or looser)
    ]
    
    for t in targets:
        submit_to_target(ws, t)

if __name__ == "__main__":
    run_targets()
