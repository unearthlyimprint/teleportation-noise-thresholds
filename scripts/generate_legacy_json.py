import os
import subprocess
import json
import sys

def install_and_generate():
    venv_dir = "venv_legacy"
    if not os.path.exists(venv_dir):
        print("Creating venv...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        
    pip_exe = os.path.join(venv_dir, "bin", "pip")
    py_exe = os.path.join(venv_dir, "bin", "python")
    
    print("Installing pulser==0.19.0...")
    subprocess.check_call([pip_exe, "install", "pulser==0.19.0"])
    
    script = """
import json
from pulser import Sequence, Register
from pulser.devices import Chadoq2

reg = Register.from_coordinates([(0,0)], prefix="q")
seq = Sequence(reg, Chadoq2)
seq.declare_channel("rydberg", "rydberg_global")
seq.measure("ground-rydberg")

print(seq.serialize())
"""
    print("Generating JSON...")
    result = subprocess.check_output([py_exe, "-c", script], text=True)
    
    print("\n--- LEGACY JSON ---")
    print(result)
    
    # Save to file
    with open("legacy_seq.json", "w") as f:
        f.write(result)
    print("Saved to legacy_seq.json")

if __name__ == "__main__":
    install_and_generate()
