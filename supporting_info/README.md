# Wormhole Stability from Coherence Field Dynamics

[![arXiv](https://img.shields.io/badge/arXiv-pending-red.svg)](https://arxiv.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

This repository contains the simulation code, experimental data, and manuscript for the paper:

> **"Wormhole Stability from Coherence Field Dynamics: A Quantum Simulation on Azure Quantum"**  
> Celal Arda  
> _Submitted to Physical Review X_ (2026)

## Abstract

We demonstrate the first experimental realization of a decoherence-induced phase transition in a quantum wormhole analog using Azure Quantum's IonQ simulator. The Coherent Field Dynamics (CFD) framework predicts a critical collapse threshold at γ_crit = 0.535, confirmed with 9.6σ statistical significance. We further demonstrate Active Shielding—a unitary protocol that restores traversability at high decoherence by pre-correcting for information scrambling.

**Key Results:**
- ✅ Traversable wormhole: F = 0.92 ± 0.04 (37% above classical limit)
- ✅ Critical collapse at γ = 0.535 (as predicted by theory)
- ✅ Active Shielding recovery: F = 0.92 at γ = 0.8 (previously collapsed)

---

## Repository Structure

```
/Wormhole Stability/
│
├── manuscript/                    # LaTeX manuscript and bibliography
│   ├── wormhole_cfd_manuscript_FINAL.pdf    ← Published version
│   ├── wormhole_cfd_manuscript_FINAL.tex
│   ├── references.bib
│   ├── corrections-needed.md      (historical, applied to FINAL)
│   ├── README_COMPILATION.md
│   └── figures/
│
├── code/                          # Key experimental scripts
│   ├── experiment_1_phase_transition.py     ← Critical threshold scan
│   └── experiment_2_active_shielding.py     ← Unitary recovery demo
│
├── data/                          # Experimental results (CSV)
│   ├── experimental_wormhole_data.csv
│   ├── stability_analysis.csv
│   ├── phase_diagram_throat_radius.csv
│   └── ...
│
├── archive/                       # Historical versions and old code
│   ├── old_scripts/               (15 iterative development scripts)
│   ├── old_drafts/                (previous manuscript versions)
│   ├── personal_scripts/          (backup with hardcoded credentials)
│   ├── supporting_info/           (experimental summaries & figures)
│   └── logs/                      (LaTeX build artifacts)
│
├── .env.example                   # Template for Azure credentials
├── .gitignore
└── README.md                      # This file
```

---

## Key Files

### 🔬 Experiments

1. **`experiment_1_phase_transition.py`**  
   Scans the CFD noise parameter γ from 0.0 to 1.0 to map the phase transition.  
   **Output:** Critical threshold γ_crit = 0.535, survival probabilities

2. **`experiment_2_active_shielding.py`**  
   Applies unitary Active Shielding at γ = 0.8 to recover traversability.  
   **Output:** Unshielded F = 0.00, Shielded F = 0.92

### 📊 Data

All experimental CSV files are in `data/`:
- `experimental_wormhole_data.csv` — Baseline vs critical condition fidelity
- `stability_analysis.csv` — Stability metrics across γ
- `phase_diagram_throat_radius.csv` — Heatmap data for phase diagram

### 📄 Manuscript

The final published version is:
- `manuscript/wormhole_cfd_manuscript_FINAL.pdf`
- `manuscript/wormhole_cfd_manuscript_FINAL.tex`

---

## How to Run

### Prerequisites

- Python 3.8+
- Azure Quantum account with IonQ access
- Required packages: `qiskit`, `azure-quantum`, `numpy`

```bash
pip install qiskit azure-quantum azure-identity numpy
```

### Set Azure Credentials

The scripts use environment variables for security. You have two options:

**Option 1: Export variables (per session)**

```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_RESOURCE_ID="/subscriptions/your-subscription/resourceGroups/..."
```

**Option 2: Use a `.env` file (recommended)**

1. Copy the template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual credentials

3. Install `python-dotenv` and add to scripts:
   ```bash
   pip install python-dotenv
   ```

4. Add at the top of each script:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Run Experiments

```bash
cd code

# Experiment 1: Critical threshold scan (~5 minutes on simulator)
python experiment_1_phase_transition.py

# Experiment 2: Active Shielding recovery (~2 minutes)
python experiment_2_active_shielding.py
```

---

## Citation

If you use this code or reference this work, please cite:

```bibtex
@article{arda2026wormhole,
  title={Wormhole Stability from Coherence Field Dynamics: A Quantum Simulation on Azure Quantum},
  author={Arda, Celal},
  journal={Physical Review X},
  year={2026},
  note={arXiv:pending}
}
```

---

## Theoretical Framework

The **Coherent Field Dynamics (CFD)** framework introduces a coherence field ϕ(γ) that controls wormhole traversability. The key insight is that environmental decoherence (parameterized by γ) induces a **geometric phase transition**:

- **γ < γ_crit:** Traversable wormhole (ER bridge intact)
- **γ ≈ γ_crit:** Critical collapse (horizon formation)
- **γ > γ_crit:** Collapsed geometry (information firewall)

**Active Shielding** reverses this collapse via a unitary pre-correction:

```
U_shield = N^(-1)(γ)
```

This allows engineered stabilization of quantum wormholes at arbitrarily high decoherence.

---

## Reproducibility

All experimental results in the manuscript can be reproduced by running the scripts in `code/`. The CSV files in `data/` contain the exact output used to generate figures in the paper.

For questions or issues, please open a GitHub issue or contact: [your email]

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Azure Quantum** for IonQ simulator access
- **Qiskit** development team for circuit libraries
- Collaborators and reviewers for valuable feedback
