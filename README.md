# Cross-Platform Noise Thresholds in Quantum Teleportation

**Trapped-Ion and Neutral-Atom Architectures**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Overview

This repository contains the code, data, and manuscript for the paper:

> **Cross-Platform Noise Thresholds in Quantum Teleportation: Trapped-Ion and Neutral-Atom Architectures**
> Celal Arda (2026)

We present a systematic study of teleportation fidelity under controlled parametric dephasing across two quantum architectures: **trapped-ion** (IonQ Forte-1) and **neutral-atom** (Pasqal FRESNEL_CAN1). By injecting deterministic Rz phase rotations of tunable strength γ into a minimal teleportation circuit, we map the fidelity response as a function of dephasing strength on both platforms.

### Key Results

| Result | Value | Platform |
|--------|-------|----------|
| Teleportation fidelity | F = 0.988 ± 0.003 | IonQ Forte-1 QPU |
| Gate-based dephasing threshold | γ ≈ 0.535 | IonQ Simulator |
| Analog dephasing threshold | γ ∈ [0.15, 0.30] | Pasqal EMU_FREE |
| QPU validation (γ = 0.20) | P₀ = 70.6% vs ideal 72.0% | FRESNEL_CAN1 QPU |
| Spectator qubit discovery | Compiler removes idle qubits | IonQ Forte-1 |

---

## Repository Structure

```
├── manuscript/                      # LaTeX source, figures, SI document
│   ├── teleportation_noise_v5.0.tex      # Main manuscript (v5.0)
│   ├── supporting_information_v5.0.tex   # Supplementary Information
│   ├── references_cfd.bib                # BibTeX bibliography
│   └── figures/                          # All manuscript figures
│
├── code/                            # Core experiment scripts
│   ├── experiment_1_phase_transition.py   # Dephasing sweep (IonQ)
│   └── wormhole_pulser_continuous.py      # Continuous-mode Pulser simulation
│
├── data/                            # Experimental data (CSV)
│   ├── stability_analysis.csv             # Main stability analysis
│   └── ...                                # Additional datasets
│
├── hardware_qpu_input/              # IonQ Forte-1 QPU circuit I/O
│   └── circuit-*.{input,output}.json      # Raw circuit submissions & results
│
├── scripts/                         # Analysis & sweep scripts
│   ├── tier1v3_trotter_sweep.py           # Trotter-step scaling
│   ├── trotter_noisy_corrected.py         # Noisy Trotter sweep (density matrix)
│   ├── wormhole_control_experiment.py     # Control experiment (no entanglement)
│   ├── wormhole_hardware_correct.py       # Hardware-corrected protocol
│   ├── wormhole_teleport_local_test.py    # Local teleportation test
│   └── plot_azure_data.py                 # Plotting utilities
│
├── pasqal_native/                   # Pasqal neutral-atom implementation
│   ├── code/                              # Pulser sequence builder
│   ├── scripts/                           # Submission & analysis
│   │   ├── run_wormhole_pasqal.py         # Cloud submission (γ sweep)
│   │   ├── fetch_fresnel_results.py       # Fetch FRESNEL_CAN1 QPU results
│   │   └── analyze_fresnel_can1.py        # Core-qubit QPU analysis
│   ├── results/                           # Emulator & QPU output (JSON)
│   └── figures/                           # Generated figures
│
├── .env.example                     # Credential template (Azure + Pasqal)
├── requirements.txt                 # Python dependencies
└── LICENSE                          # MIT License
```

---

## Setup

### Prerequisites

- Python ≥ 3.10
- Azure Quantum account (for IonQ access)
- Pasqal Cloud account (for neutral-atom emulator/QPU access)

### Installation

```bash
# Clone repository
git clone https://github.com/unearthlyimprint/wormhole_stability.git
cd wormhole_stability

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your Azure Quantum and Pasqal Cloud credentials
```

### Reproducing Results

```bash
# Dephasing sweep (IonQ simulator)
python code/experiment_1_phase_transition.py

# Trotter-depth sweep (local simulation)
python scripts/tier1v3_trotter_sweep.py --mode sim --shots 2000

# Pasqal neutral-atom simulation
cd pasqal_native
pip install -r requirements.txt
python scripts/run_wormhole_pasqal.py
```

---

## Citation

If you use this code or data, please cite:

```bibtex
@article{arda2026teleportation,
  title   = {Cross-Platform Noise Thresholds in Quantum Teleportation:
             Trapped-Ion and Neutral-Atom Architectures},
  author  = {Arda, Celal},
  year    = {2026},
  note    = {v5.0}
}
```

---

## Version History

- **v5.0** (Feb 2026): Complete reframe — cross-platform noise characterization study
- **v4.4** (Feb 2026): FRESNEL_CAN1 QPU hardware results added
- **v4.2** (Feb 2026): Initial public release with IonQ + Pasqal emulator data

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Contact

Celal Arda — celal.arda@outlook.de
