# Tier 1: Circuit-Depth Sweep — Quick Start
## What This Tests

Your paper has two hardware data points: F=0.988 (3 qubits) and F≈0 (9 qubits).
This experiment fills in the gap with 4 data points using the SAME wormhole
architecture at different scales:

| N pairs | Qubits | CX Gates | What it tells you |
|---------|--------|----------|-------------------|
| 1       | 3      | 10       | Shallow circuit baseline |
| 2       | 5      | 17       | Light-intermediate |
| 3       | 7      | 24       | Deep-intermediate |
| 4       | 9      | 31       | Full protocol (should match F≈0) |

All circuits run at γ=0 (no injected noise). The ONLY noise source is
hardware decoherence, which scales with gate count.

## Step 1: Local Validation (free, no credits)

```bash
python tier1_depth_sweep.py --mode sim --shots 2000
```

Expected: All 4 circuits give F=1.0 (noiseless simulator).
This confirms the circuits are mathematically correct.

## Step 2: Run on Forte-1 Hardware

```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_RESOURCE_ID="your-resource-id"

python tier1_depth_sweep.py --mode hardware --shots 200
```

Estimated cost: ~20-30 AQTS (you have ~9,600 remaining).
200 shots gives ±0.05 uncertainty on fidelity, which is sufficient
to distinguish sharp from smooth transitions.

## Step 3: Analyze Results

```bash
python tier1_analysis.py tier1_results_hardware_YYYYMMDD_HHMMSS.json
```

This fits three competing models (sigmoid, exponential, linear) and
generates a publication-quality figure.

Or enter results manually:
```bash
python tier1_analysis.py --manual
```

## What to Look For

**Sharp drop (CFD prediction):**
- Fidelity holds ~0.7+ for N=1,2 then crashes to ~0 at N=3 or N=4
- Sigmoid fit has narrow width (w < 3)
- Largest ΔF concentrated between two adjacent points

**Smooth decay (standard decoherence):**
- Fidelity decreases roughly linearly or exponentially with gate count
- All three models fit comparably well
- No single dominant ΔF

**Either result is publishable.** Sharp supports CFD; smooth constrains it.

## Files
- `tier1_depth_sweep.py` — Main experiment script (sim + hardware)
- `tier1_analysis.py` — Model fitting and plotting
