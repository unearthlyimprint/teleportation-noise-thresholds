import sys
import os
import json

# Add code folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../code'))

from wormhole_pulser_continuous import build_wormhole_sequence

def debug_json():
    print("Building sequence...")
    # Use a small duration to be safe
    seq = build_wormhole_sequence(gamma=0.0, coupling_time=500)
    
    print("Serializing...")
    json_str = seq.to_abstract_repr()
    data = json.loads(json_str)
    
    print("\n--- JSON KEYS ---")
    print(data.keys())
    
    print("\n--- MEASUREMENT ---")
    if 'measurement' in data:
        print(data['measurement'])
    else:
        print("MISSING 'measurement' key")

    print("\n--- REGISTER ---")
    if 'register' in data:
        print(f"Register present. Type: {type(data['register'])}")
    else:
        print("MISSING 'register' key")

    print("\n--- CHANNELS ---")
    if 'channels' in data:
        print(data['channels'].keys())
    else:
        print("MISSING 'channels' key")
        
    print("\n--- VARIABLES ---")
    if 'variables' in data:
        print(data['variables'])
    else:
        print("MISSING 'variables' key")

if __name__ == "__main__":
    debug_json()
