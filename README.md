# Wormhole Stability from Coherence Field Dynamics

**Quantum Simulation and Hardware Validation on IonQ Forte**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Overview

This repository contains the code, data, and manuscript for the paper:

> **Wormhole Stability from Coherence Field Dynamics: Quantum Simulation and Hardware Validation on IonQ Forte**
> Celal Arda (2026)

We introduce **Coherence Field Dynamics (CFD)**, a theoretical framework modeling decoherence as deterministic interaction with a background field γ, and apply it to traversable wormhole stability in the ER=EPR correspondence.

### Key Results

| Result | Value | Platform |
|--------|-------|----------|
| Critical decoherence threshold | γ_c ≈ 0.535 | IonQ Simulator |
| Hardware teleportation fidelity | F = 0.988 ± 0.003 | IonQ Forte-1 QPU |
| Active Shielding recovery | F: 0.00 → 0.92 | Simulation |
| Pasqal critical threshold | γ_c ≈ 0.20 | Pasqal EMU_FREE |
| Critical exponent | β ≈ 1.0 (mean-field) | Simulation |

---

## Repository Structure

```
├── manuscript/                      # LaTeX source, figures, SI document
│   ├── wormhole_cfd_manuscript_v4.2.tex   # Main manuscript (v4.2)
│   ├── supporting_information.tex         # Supplementary Information
│   ├── references_cfd.bib                 # BibTeX bibliography
│   └── figures/                           # All manuscript figures
│
├── code/                            # Core experiment scripts
│   ├── experiment_1_phase_transition.py   # Phase transition sweep (IonQ)
│   ├── experiment_2_active_shielding.py   # Active Shielding protocol
│   └── wormhole_pulser_continuous.py      # Continuous-mode Pulser simulation
│
├── data/                            # Experimental data (CSV)
│   ├── stability_analysis.csv             # Main stability analysis
│   ├── phase_diagram_throat_radius.csv    # Phase diagram data
│   ├── quantum_corrections.csv            # Quantum correction terms
│   └── ...                                # Additional datasets
│
├── hardware_qpu_input/              # IonQ Forte-1 QPU circuit I/O
│   └── circuit-*.{input,output}.json      # Raw circuit submissions & results
│
├── scripts/                         # Analysis & sweep scripts
│   ├── tier1_analysis.py                  # Tier-1 result analysis
│   ├── tier1_depth_sweep.py               # Depth sweep experiment
│   ├── tier1v3_trotter_sweep.py           # Trotter-step scaling
│   ├── wormhole_azure_pasqal.py           # Azure ↔ Pasqal bridge
│   ├── wormhole_control_experiment.py     # Control experiment (no entanglement)
│   ├── wormhole_hardware_correct.py       # Hardware-corrected protocol
│   ├── wormhole_teleport_local_test.py    # Local teleportation test
│   ├── wormhole_teleport_sweep.py         # Teleportation parameter sweep
│   ├── verify_tensor_derivation.py        # Tensor derivation verification
│   └── plot_azure_data.py                 # Plotting utilities
│
├── pasqal_native/                   # Pasqal neutral-atom implementation
│   ├── code/                              # Pulser sequence builder
│   ├── scripts/                           # Submission & analysis
│   ├── results/                           # Emulator output (JSON)
│   ├── figures/                           # Generated figures
│   └── README.md                          # Pasqal-specific documentation
│
├── .env.example                     # Azure Quantum credentials template
├── requirements.txt                 # Python dependencies
└── LICENSE                          # MIT License
```

---

## Setup

### Prerequisites

- Python ≥ 3.10
- Azure Quantum account (for IonQ access)
- Pasqal Cloud account (for neutral-atom emulator access)

### Installation

```bash
# Clone repository
git clone https://github.com/CelalArda/wormhole-cfd-stability.git
cd wormhole-cfd-stability

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your Azure Quantum credentials
```

### Reproducing Results

```bash
# Phase transition sweep (IonQ simulator)
python code/experiment_1_phase_transition.py

# Active Shielding experiment
python code/experiment_2_active_shielding.py

# Trotter-depth sweep analysis
python scripts/tier1v3_trotter_sweep.py

# Pasqal neutral-atom simulation
cd pasqal_native
pip install -r requirements.txt
python scripts/run_wormhole_pasqal.py
```

---

## Citation

If you use this code or data, please cite:

```bibtex
@article{arda2026wormhole,
  title   = {Wormhole Stability from Coherence Field Dynamics:
             Quantum Simulation and Hardware Validation on IonQ Forte},
  author  = {Arda, Celal},
  year    = {2026},
  note    = {v4.2}
}
```

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Contact

Celal Arda — celal.arda@outlook.de
