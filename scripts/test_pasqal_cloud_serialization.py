import json
from pulser import Sequence, Register
from pulser.devices import AnalogDevice
from pasqal_cloud.device import EmulatorType
from pasqal_cloud import SDK

def test_serialization():
    # Create sequence
    reg = Register.from_coordinates([(0,0)], prefix="q")
    seq = Sequence(reg, AnalogDevice)
    seq.declare_channel("rydberg", "rydberg_global")
    seq.measure("ground-rydberg")
    
    json_str = seq.to_abstract_repr()
    data = json.loads(json_str)

    print("Checking if we can validate this data against pasqal-cloud models...")
    
    # Try to import internal models if possible
    try:
        from pasqal_cloud.device import EmuTNBackend
        print("Found EmuTNBackend model")
    except ImportError:
        pass
        
    try:
        # The 'create_batch' method takes 'sequence_builder' which is the json string
        # Let's see if we can trigger validation by mocking SDK or looking sources
        pass 
    except Exception as e:
        print(e)
        
    # ONE CRITICAL FINDING from online docs:
    # "To run a simulation, you need to set the `emulator` argument."
    
    print("\n--- Key Observation ---")
    print("The pulser 1.7.0 JSON contains 'device' with 'pre_calibrated_layouts'.")
    print("This might be too heavy for the backend if it expects a simple device name.")
    
    # Let's try to strip device completely and print it for the user to try
    if 'device' in data:
        del data['device']
        
    print("\nAttempting to print minimal valid JSON payload:")
    print(json.dumps(data))

if __name__ == "__main__":
    test_serialization()
