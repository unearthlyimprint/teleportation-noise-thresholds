import json
import inspect
from pulser import Sequence, Register
from pulser.devices import AnalogDevice

try:
    import pasqal_cloud
    print(f"pasqal-cloud version: {pasqal_cloud.__version__}")
except ImportError:
    print("pasqal-cloud not found")

# Try to find serialization logic
try:
    from pasqal_cloud.utils import normalize_sequence
    print("\nFound pasqal_cloud.utils.normalize_sequence")
except ImportError:
    print("\nnormalize_sequence not found in pasqal_cloud.utils")

# Create a sequence
reg = Register.from_coordinates([(0,0)], prefix="q")
seq = Sequence(reg, AnalogDevice)
seq.declare_channel("rydberg", "rydberg_global")
seq.measure("ground-rydberg")

# Serialization test
print("\n--- Pulser 1.7.0 Default Serialization ---")
print(seq.to_abstract_repr())

# Check if we can use pasqal_cloud to validate/serialize
# Only if we find a relevant function
