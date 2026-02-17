import os
import json
import copy
from azure.quantum import Workspace
from azure.quantum.target.pasqal import Pasqal
from azure.identity import DeviceCodeCredential
from pulser import Sequence, Register
from pulser.devices import AnalogDevice

def get_base_json():
    # Trivial Sequence
    reg = Register.from_coordinates([(0,0), (10,0)], prefix="q")
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
            print("SUCCESS! This is the working format.")
            return True
        else:
            print(f"FAILED. Error: {job.details.error_data}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

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
    
    base = get_base_json() # Has 'register' list, 'version': '1', etc.
    
    # Variation 7: Legacy 'qubits' format (Pulser < 0.14)
    # Convert 'register' (list) -> 'qubits' (dict)
    v7 = copy.deepcopy(base)
    if 'device' in v7: del v7['device']
    if 'register' in v7:
        qubits = {}
        for atom in v7['register']:
            name = atom.pop('name')
            qubits[name] = atom
        v7['qubits'] = qubits
        del v7['register']
    # Also usually version is removed or set to '1' (v0 had no version field sometimes)
    if 'version' in v7: del v7['version']
    if 'pulser_version' in v7: del v7['pulser_version']
    submit_variation(target, v7, "7_legacy_qubits_dict")

    # Variation 8: Add 'effective_size'
    v8 = copy.deepcopy(base)
    if 'device' in v8: del v8['device']
    v8['effective_size'] = len(base['register'])
    submit_variation(target, v8, "8_effective_size")
    
    # Variation 9: Minimal (Only register, channels, operations, measurement)
    v9 = {}
    v9['register'] = base['register']
    v9['channels'] = base['channels']
    v9['operations'] = base['operations']
    v9['measurement'] = base['measurement']
    # Try to sneak it past validation without extra metadata
    submit_variation(target, v9, "9_minimal_fields")

if __name__ == "__main__":
    run_tests()
