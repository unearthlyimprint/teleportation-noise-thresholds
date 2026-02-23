import json
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = SCRIPT_DIR # Data is in the same dir as scripts based on file list
FIGURE_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'manuscript', 'figures')

os.makedirs(FIGURE_DIR, exist_ok=True)

def load_data():
    """Parses all tier1 result files."""
    data = []
    # Pattern to match: tier1*_results_*.json
    files = glob.glob(os.path.join(DATA_DIR, 'tier1*_results_*.json'))
    
    print(f"Found {len(files)} data files.")
    
    for f in files:
        try:
            with open(f, 'r') as fp:
                content = json.load(fp)
                # Content might be a list or dict. 
                # Assuming list of experiments based on filenames
                if isinstance(content, list):
                    data.extend(content)
                elif isinstance(content, dict):
                    # Check if it has 'results' key or is a single result
                    if 'results' in content:
                        data.extend(content['results'])
                    else:
                        data.append(content)
        except Exception as e:
            print(f"Skipping {f}: {e}")
            
    return data

def plot_phase_diagram(data):
    """Fidelity vs Gamma."""
    gammas = []
    fidelities = []
    
    # Filter for standard simulation/hardware results where we varied Gamma
    for entry in data:
        # Check structure
        g = entry.get('gamma') or entry.get('metadata', {}).get('gamma')
        f = entry.get('fidelity')
        
        if g is not None and f is not None:
            gammas.append(float(g))
            fidelities.append(float(f))
            
    plt.figure(figsize=(6, 4))
    plt.scatter(gammas, fidelities, c='blue', alpha=0.6, label='Experimental Data')
    
    # Critical line
    plt.axvline(x=0.535, color='red', linestyle='--', label=r'$\gamma_c \approx 0.535$')
    
    plt.xlabel(r'Dephasing Strength $\gamma$')
    plt.ylabel('Teleportation Fidelity $F$')
    plt.title('Teleportation Fidelity vs. Parametric Dephasing')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    out_path = os.path.join(FIGURE_DIR, 'phase_diagram.pdf')
    plt.savefig(out_path, bbox_inches='tight')
    print(f"Saved {out_path}")
    plt.close()

def plot_survival_probability(data):
    """P(0) vs Gamma (or similar metric)."""
    # Assuming 'survival' or 'counts' are available
    gammas = []
    survivals = []
    
    for entry in data:
        g = entry.get('gamma') or entry.get('metadata', {}).get('gamma')
        counts = entry.get('counts') # {'00...': X, ...}
        
        if g is not None and counts:
            # Survival P(0) usually means All Zeros or specific '0' on Bob
            # Assuming '0' count on Bob/Message
            # If counts is simple {'0': N, '1': M}
            total = sum(counts.values())
            p0 = counts.get('0', 0) / total
            
            gammas.append(float(g))
            survivals.append(p0)
            
    plt.figure(figsize=(6, 4))
    plt.scatter(gammas, survivals, c='green', marker='s', alpha=0.6, label='Survival P(0)')
    
    # Theoretical curve (schematic)
    gs = np.linspace(0, 1, 100)
    # Theory: R ~ exp(-beta gamma)
    
    plt.axvline(x=0.535, color='red', linestyle='--', label='Critical Threshold')
    
    plt.xlabel(r'Dephasing Strength $\gamma$')
    plt.ylabel('Survival Probability $P(0)$')
    plt.title('Survival Probability vs. Dephasing Strength')
    plt.legend()
    plt.grid(True)
    
    out_path = os.path.join(FIGURE_DIR, 'survival_probability.pdf')
    plt.savefig(out_path, bbox_inches='tight')
    print(f"Saved {out_path}")
    plt.close()

if __name__ == "__main__":
    data = load_data()
    if data:
        plot_phase_diagram(data)
        plot_survival_probability(data)
    else:
        print("No data found to plot.")
