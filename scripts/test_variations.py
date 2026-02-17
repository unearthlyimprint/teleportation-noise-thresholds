import os
import json
import copy
from azure.quantum import Workspace
from azure.quantum.target.pasqal import Pasqal
from azure.identity import DeviceCodeCredential
from pulser import Sequence, Register
from pulser.devices import AnalogDevice

def get_base_json():
    # 1. Trivial Sequence
    reg = Register.from_coordinates([(0,0)], prefix="q")
    seq = Sequence(reg, AnalogDevice)
    seq.declare_channel("rydberg", "rydberg_global")
    seq.measure("ground-rydberg")
    return json.loads(seq.to_abstract_repr())

def submit_variation(target, data, name):
    print(f"\n--- Submitting Variation: {name} ---")
    serialized = json.dumps(data)
    try:
        job = target.submit(
            input_data=serialized,
            name=f"debug_{name}",
            shots=10
        )
        print(f"Job ID: {job.id}")
        job.wait_until_completed(timeout_secs=60)
        
        if job.details.status == "Succeeded":
            print("SUCCESS!")
            return True
        else:
            print(f"FAILED. Error: {job.details.error_data}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def run_tests():
    # Setup
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    resource_id = os.environ.get("AZURE_RESOURCE_ID")
    location = os.environ.get("AZURE_LOCATION", "eastus")
    
    if not tenant_id:
        print("Set AZURE env vars!")
        return

    credential = DeviceCodeCredential(tenant_id=tenant_id)
    ws = Workspace(resource_id=resource_id, location=location, credential=credential)
    target = Pasqal(ws, name="pasqal.sim.emu-tn")
    
    base = get_base_json()
    
    # Variation 1: As-Is (Keep Device) -- This is the default output of Pulser
    v1 = copy.deepcopy(base)
    # No changes
    submit_variation(target, v1, "1_default_with_device")

    # Variation 2: Strip Device (What we tried)
    v2 = copy.deepcopy(base)
    if 'device' in v2: del v2['device']
    submit_variation(target, v2, "2_no_device")

    # Variation 3: Strip Device + Add Z
    v3 = copy.deepcopy(base)
    if 'device' in v3: del v3['device']
    if 'register' in v3:
        for q in v3['register']:
            if 'z' not in q: q['z'] = 0.0
    submit_variation(target, v3, "3_no_device_add_z")
    
    # Variation 4: Default + Add Z (Maybe device field is fine, just missing Z?)
    v4 = copy.deepcopy(base)
    if 'register' in v4:
        for q in v4['register']:
            if 'z' not in q: q['z'] = 0.0
    submit_variation(target, v4, "4_device_add_z")

    # Variation 5: No Variables
    v5 = copy.deepcopy(base)
    if 'device' in v5: del v5['device']
    if 'variables' in v5: del v5['variables']
    submit_variation(target, v5, "5_no_device_no_vars")

    # Variation 6: No Pulser Version
    v6 = copy.deepcopy(base)
    if 'device' in v6: del v6['device']
    if 'pulser_version' in v6: del v6['pulser_version']
    submit_variation(target, v6, "6_no_device_no_version")

if __name__ == "__main__":
    run_tests()
