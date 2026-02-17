import os
import json
from azure.quantum import Workspace
from azure.quantum.target.pasqal import Pasqal
from azure.identity import DeviceCodeCredential
from pulser import Sequence, Register
from pulser.devices import AnalogDevice

def submit_trivial():
    # Setup
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    resource_id = os.environ.get("AZURE_RESOURCE_ID")
    location = os.environ.get("AZURE_LOCATION", "eastus")
    
    credential = DeviceCodeCredential(tenant_id=tenant_id)
    ws = Workspace(resource_id=resource_id, location=location, credential=credential)
    target = Pasqal(ws, name="pasqal.sim.emu-tn")
    
    # 1. Trivial Sequence: 1 Atom, Measure
    reg = Register.from_coordinates([(0,0)], prefix="q")
    seq = Sequence(reg, AnalogDevice)
    seq.declare_channel("rydberg", "rydberg_global")
    seq.measure("ground-rydberg")
    
    json_str = seq.to_abstract_repr()
    
    # Prune device if needed
    data = json.loads(json_str)
    if 'device' in data:
        del data['device']
    serialized = json.dumps(data)
    
    print("Submitting TRIVIAL job...")
    job = target.submit(
        input_data=serialized,
        name="trivial_debug",
        shots=10
    )
    print(f"Job ID: {job.id}")
    
    try:
        job.wait_until_completed(timeout_secs=60)
        print(f"Status: {job.details.status}")
        if job.details.status == "Failed":
             print(f"Error: {job.details.error_data}")
    except Exception as e:
        print(f"Wait failed: {e}")

if __name__ == "__main__":
    submit_trivial()
