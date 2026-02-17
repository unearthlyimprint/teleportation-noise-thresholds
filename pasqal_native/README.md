# Pasqal Native — CFD Wormhole Simulation

Direct submission to **Pasqal Cloud** using the native `pasqal-cloud` SDK.
No Azure wrapper — clean, direct access to EMU-TN emulator.

## Directory Structure

```
pasqal_native/
├── code/                          # Sequence builder (Pulser)
│   └── wormhole_pulser_continuous.py
├── scripts/                       # Submission & analysis scripts
│   └── run_wormhole_pasqal.py
├── results/                       # Output JSON files
├── pasqal_env/                    # Virtual environment
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Activate environment
source pasqal_env/bin/activate

# 2. Set credentials (get from https://portal.pasqal.cloud)
export PASQAL_PROJECT_ID="your-project-id"
export PASQAL_USERNAME="your-email@example.com"
export PASQAL_PASSWORD="your-password"
```

## Run

```bash
cd scripts
python run_wormhole_pasqal.py
```

This will:
1. Authenticate with Pasqal Cloud
2. Build Pulser sequences for γ = [0.0, 0.1, ..., 1.0]
3. Submit each as a batch to **EMU-TN** emulator
4. Poll for completion and save results to `results/`

## Installed Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `pulser` | 1.7.0 | Sequence builder |
| `pasqal-cloud` | 0.20.8 | Direct Pasqal Cloud SDK |
| `qutip` | 5.2.3 | Local simulation fallback |
| `numpy` | 2.4.2 | Numerical |
| `scipy` | 1.16.3 | Scientific |
| `matplotlib` | 3.10.8 | Plotting |
