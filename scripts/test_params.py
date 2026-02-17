import os
import json
from azure.quantum import Workspace
from azure.quantum.target.pasqal import Pasqal
from azure.identity import DeviceCodeCredential
from pulser import Sequence, Register
from pulser.devices import AnalogDevice

def submit_param_test(target, params, name):
    print(f"\n--- Submitting Params: {name} ---")
    print(f"input_params: {params}")
    
    # Trivial Sequence
    reg = Register.from_coordinates([(0,0)], prefix="q")
    seq = Sequence(reg, AnalogDevice)
    seq.declare_channel("rydberg", "rydberg_global")
    seq.measure("ground-rydberg")
    
    # Standard JSON (strip device to be safe)
    data = json.loads(seq.to_abstract_repr())
    if 'device' in data: del data['device']
    serialized = json.dumps(data)
    
    try:
        # We pass input_params explicitly to override SDK defaults
        job = target.submit(
            input_data=serialized,
            name=f"debug_{name}",
            shots=params.get('runs', params.get('count', 10)), # SDK uses this for cost estimation maybe?
            input_params=params
        )
        print(f"Job ID: {job.id}")
        job.wait_until_completed(timeout_secs=60)
        
        if job.details.status == "Succeeded":
            print("SUCCESS! This parameter set works.")
        else:
            print(f"FAILED. Error: {job.details.error_data}")
            
    except Exception as e:
        print(f"Exception: {e}")

def run_tests():
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    resource_id = os.environ.get("AZURE_RESOURCE_ID")
    location = os.environ.get("AZURE_LOCATION", "eastus")
    
    if not tenant_id:
        print("Set AZURE env vars!")
        return

    credential = DeviceCodeCredential(tenant_id=tenant_id)
    ws = Workspace(resource_id=resource_id, location=location, credential=credential)
    target = Pasqal(ws, name="pasqal.sim.emu-tn")
    
    # Test 1: "runs" (Matches pasqal-cloud model)
    submit_param_test(target, {"runs": 10}, "explicit_runs")

    # Test 2: "count" (Legacy / Azure SDK default)
    submit_param_test(target, {"count": 10}, "explicit_count")
    
    # Test 3: "nb_runs" (Older legacy)
    submit_param_test(target, {"nb_runs": 10}, "explicit_nb_runs")
    
    # Test 4: Both
    submit_param_test(target, {"runs": 10, "count": 10}, "both")

if __name__ == "__main__":
    run_tests()
