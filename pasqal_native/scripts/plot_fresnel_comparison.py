"""
FRESNEL Emulator Comparison — Publication Figure
=================================================
Generates fig5_fresnel_comparison.pdf:
  Panel A: Mean Rydberg density ⟨n⟩ vs γ  (EMU_FREE sweep + EMU_FRESNEL points)
  Panel B: Ground-state probability P₀ vs γ
  Panel C: State-space diversity (unique states)

Data sources:
  - EMU_FREE:    fine sweep (19 γ points, 200 shots each)
  - EMU_SV:      3 γ cross-validation points
  - EMU_FRESNEL: 3 γ points (42 atoms, 9 core qubits, 500 shots)
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

# ============================================================================
# STYLE
# ============================================================================

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 13,
    'axes.titlesize': 13,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
})

COLORS = {
    'EMU_FREE':    '#2196F3',   # Blue
    'EMU_SV':      '#4CAF50',   # Green
    'EMU_FRESNEL': '#FF5722',   # Deep Orange
    'FRESNEL_CAN1': '#9C27B0',   # Purple (for QPU data)
}


# ============================================================================
# DATA LOADING
# ============================================================================

def load_counts_data(filepath):
    """Load JSON results and extract gamma/counts pairs."""
    with open(filepath) as f:
        data = json.load(f)
    return data


def compute_stats(counts, n_qubits=9):
    """Compute physics observables from bitstring counts."""
    total = sum(counts.values())
    if total == 0:
        return {'p0': 0, 'rho': 0, 'n_states': 0}

    ground = counts.get('0' * n_qubits, 0)
    p0 = ground / total

    rho = sum(
        bs.count('1') / n_qubits * n for bs, n in counts.items()
    ) / total

    return {
        'p0': p0,
        'rho': rho,
        'n_states': len(counts),
        'shots': total,
    }


# ============================================================================
# MAIN
# ============================================================================

results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
figures_dir = os.path.join(os.path.dirname(__file__), '..', 'figures')
os.makedirs(figures_dir, exist_ok=True)

# --- Load EMU_FREE fine sweep ---
fine_data = load_counts_data(os.path.join(results_dir, 'pasqal_fine_sweep_20260216_190558.json'))
emu_free_gamma = []
emu_free_rho = []
emu_free_p0 = []
emu_free_states = []

for entry in fine_data:
    if entry.get('status') == 'DONE' and 'counts' in entry:
        gamma = entry['gamma']
        stats = compute_stats(entry['counts'])
        emu_free_gamma.append(gamma)
        emu_free_rho.append(stats['rho'])
        emu_free_p0.append(stats['p0'])
        emu_free_states.append(stats['n_states'])

# Sort by gamma
idx = np.argsort(emu_free_gamma)
emu_free_gamma = np.array(emu_free_gamma)[idx]
emu_free_rho = np.array(emu_free_rho)[idx]
emu_free_p0 = np.array(emu_free_p0)[idx]
emu_free_states = np.array(emu_free_states)[idx]

# --- Load EMU_FREE + EMU_SV from comparison file ---
comp_data = load_counts_data(os.path.join(results_dir, 'emulator_comparison_20260216_220852.json'))
emu_sv_gamma = []
emu_sv_rho = []
emu_sv_p0 = []
emu_sv_states = []

# Also grab EMU_FREE points from comparison (coarse sweep)
comp_free_gamma = []
comp_free_rho = []
comp_free_p0 = []

for entry in comp_data:
    if entry.get('status') == 'DONE' and 'counts' in entry:
        stats = compute_stats(entry['counts'])
        if entry.get('device') == 'EMU_SV':
            emu_sv_gamma.append(entry['gamma'])
            emu_sv_rho.append(stats['rho'])
            emu_sv_p0.append(stats['p0'])
            emu_sv_states.append(stats['n_states'])
        elif entry.get('device') == 'EMU_FREE':
            comp_free_gamma.append(entry['gamma'])
            comp_free_rho.append(stats['rho'])
            comp_free_p0.append(stats['p0'])

# Merge EMU_FREE: coarse + fine (deduplicate by gamma)
all_free_gamma = list(emu_free_gamma) + comp_free_gamma
all_free_rho = list(emu_free_rho) + comp_free_rho
all_free_p0 = list(emu_free_p0) + comp_free_p0

# Deduplicate (keep fine sweep value if duplicate)
merged = {}
for g, r, p in zip(all_free_gamma, all_free_rho, all_free_p0):
    if g not in merged:
        merged[g] = (r, p)
all_free_gamma = sorted(merged.keys())
all_free_rho = [merged[g][0] for g in all_free_gamma]
all_free_p0 = [merged[g][1] for g in all_free_gamma]

# --- Load EMU_FRESNEL ---
fresnel_files = sorted([f for f in os.listdir(results_dir) if f.startswith('emu_fresnel')])
if fresnel_files:
    fresnel_data = load_counts_data(os.path.join(results_dir, fresnel_files[-1]))
else:
    fresnel_data = []

emu_fresnel_gamma = []
emu_fresnel_rho = []
emu_fresnel_p0 = []
emu_fresnel_states = []

for entry in fresnel_data:
    if entry.get('status') == 'DONE' and 'core_counts' in entry:
        stats = compute_stats(entry['core_counts'])
        emu_fresnel_gamma.append(entry['gamma'])
        emu_fresnel_rho.append(stats['rho'])
        emu_fresnel_p0.append(stats['p0'])
        emu_fresnel_states.append(stats['n_states'])

# --- Load FRESNEL_CAN1 QPU (if exists) ---
qpu_files = sorted([f for f in os.listdir(results_dir) if f.startswith('fresnel_validation')])
fresnel_qpu_gamma = []
fresnel_qpu_rho = []
fresnel_qpu_p0 = []

if qpu_files:
    qpu_data = load_counts_data(os.path.join(results_dir, qpu_files[-1]))
    for entry in qpu_data:
        if entry.get('status') == 'DONE' and 'core_counts' in entry:
            stats = compute_stats(entry['core_counts'])
            fresnel_qpu_gamma.append(entry['gamma'])
            fresnel_qpu_rho.append(stats['rho'])
            fresnel_qpu_p0.append(stats['p0'])


# ============================================================================
# FIGURE
# ============================================================================

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
fig.suptitle('Emulator Cross-Platform Comparison — Neutral-Atom Dephasing Response', fontsize=14, fontweight='bold', y=1.02)

# --- Panel A: Mean Rydberg Density ---
ax = axes[0]
ax.plot(all_free_gamma, all_free_rho, '-o', color=COLORS['EMU_FREE'],
        markersize=4, linewidth=1.5, label='EMU_FREE (9q)', zorder=3)
if emu_sv_gamma:
    ax.scatter(emu_sv_gamma, emu_sv_rho, marker='s', s=50, color=COLORS['EMU_SV'],
               edgecolors='k', linewidths=0.5, label='EMU_SV (9q)', zorder=4)
ax.scatter(emu_fresnel_gamma, emu_fresnel_rho, marker='D', s=70, color=COLORS['EMU_FRESNEL'],
           edgecolors='k', linewidths=0.8, label='EMU_FRESNEL (9/42q)', zorder=5)
if fresnel_qpu_gamma:
    ax.scatter(fresnel_qpu_gamma, fresnel_qpu_rho, marker='*', s=120, color=COLORS['FRESNEL_CAN1'],
               edgecolors='k', linewidths=0.8, label='FRESNEL_CAN1 QPU (9/42q)', zorder=6)

ax.set_xlabel(r'Dephasing Strength $\gamma$')
ax.set_ylabel(r'$\langle n \rangle$ (Mean Rydberg density)')
ax.set_title('(A) Mean Rydberg Density')
ax.axvline(x=0.535, color='gray', linestyle='--', alpha=0.4, label=r'$\gamma_c = 0.535$')
ax.legend(loc='upper right', framealpha=0.9)
ax.set_xlim(-0.02, 0.65)
ax.set_ylim(-0.01, None)
ax.xaxis.set_minor_locator(AutoMinorLocator())
ax.yaxis.set_minor_locator(AutoMinorLocator())

# --- Panel B: Ground-State Probability ---
ax = axes[1]
ax.plot(all_free_gamma, all_free_p0, '-o', color=COLORS['EMU_FREE'],
        markersize=4, linewidth=1.5, label='EMU_FREE', zorder=3)
if emu_sv_p0:
    ax.scatter(emu_sv_gamma, emu_sv_p0, marker='s', s=50, color=COLORS['EMU_SV'],
               edgecolors='k', linewidths=0.5, label='EMU_SV', zorder=4)
ax.scatter(emu_fresnel_gamma, emu_fresnel_p0, marker='D', s=70, color=COLORS['EMU_FRESNEL'],
           edgecolors='k', linewidths=0.8, label='EMU_FRESNEL', zorder=5)
if fresnel_qpu_p0:
    ax.scatter(fresnel_qpu_gamma, fresnel_qpu_p0, marker='*', s=120, color=COLORS['FRESNEL_CAN1'],
               edgecolors='k', linewidths=0.8, label='FRESNEL_CAN1 QPU', zorder=6)

ax.set_xlabel(r'Dephasing Strength $\gamma$')
ax.set_ylabel(r'$P_0$ (Ground-state probability)')
ax.set_title('(B) Fidelity Collapse')
ax.axvline(x=0.535, color='gray', linestyle='--', alpha=0.4)
ax.legend(loc='lower right', framealpha=0.9)
ax.set_xlim(-0.02, 0.65)
ax.set_ylim(-0.02, 1.05)
ax.xaxis.set_minor_locator(AutoMinorLocator())
ax.yaxis.set_minor_locator(AutoMinorLocator())

# --- Panel C: Noise Effect (Δ from EMU_FREE baseline) ---
ax = axes[2]

# Interpolate EMU_FREE baseline for comparison
from scipy.interpolate import interp1d

if len(all_free_gamma) >= 2:
    interp_rho = interp1d(all_free_gamma, all_free_rho, kind='linear', fill_value='extrapolate')
    interp_p0 = interp1d(all_free_gamma, all_free_p0, kind='linear', fill_value='extrapolate')

    # EMU_FRESNEL deltas
    if emu_fresnel_gamma:
        delta_rho = [emu_fresnel_rho[i] - interp_rho(g) for i, g in enumerate(emu_fresnel_gamma)]
        delta_p0 = [emu_fresnel_p0[i] - interp_p0(g) for i, g in enumerate(emu_fresnel_gamma)]

        ax.bar(np.array(emu_fresnel_gamma) - 0.012, delta_rho, width=0.02,
               color=COLORS['EMU_FRESNEL'], alpha=0.7, label=r'$\Delta\langle n \rangle$')
        ax.bar(np.array(emu_fresnel_gamma) + 0.012, delta_p0, width=0.02,
               color=COLORS['EMU_FRESNEL'], alpha=0.35, hatch='///', label=r'$\Delta P_0$')

    # FRESNEL_CAN1 QPU deltas (if available)
    if fresnel_qpu_gamma:
        delta_rho_qpu = [fresnel_qpu_rho[i] - interp_rho(g) for i, g in enumerate(fresnel_qpu_gamma)]
        delta_p0_qpu = [fresnel_qpu_p0[i] - interp_p0(g) for i, g in enumerate(fresnel_qpu_gamma)]
        ax.bar(np.array(fresnel_qpu_gamma) - 0.012, delta_rho_qpu, width=0.02,
               color=COLORS['FRESNEL_CAN1'], alpha=0.7, label=r'QPU $\Delta\langle n \rangle$')
        ax.bar(np.array(fresnel_qpu_gamma) + 0.012, delta_p0_qpu, width=0.02,
               color=COLORS['FRESNEL_CAN1'], alpha=0.35, hatch='///', label=r'QPU $\Delta P_0$')

ax.axhline(y=0, color='k', linewidth=0.5)
ax.set_xlabel(r'Dephasing Strength $\gamma$')
ax.set_ylabel(r'$\Delta$ from EMU_FREE baseline')
ax.set_title('(C) Hardware Noise Effect')
ax.legend(loc='best', framealpha=0.9)
ax.set_xlim(-0.02, 0.65)
ax.xaxis.set_minor_locator(AutoMinorLocator())
ax.yaxis.set_minor_locator(AutoMinorLocator())

# --- Finalize ---
plt.tight_layout()
outpdf = os.path.join(figures_dir, 'fig5_fresnel_comparison.pdf')
outpng = os.path.join(figures_dir, 'fig5_fresnel_comparison.png')
plt.savefig(outpdf, bbox_inches='tight')
plt.savefig(outpng, bbox_inches='tight')
print(f"\n✅ Saved: {outpdf}")
print(f"✅ Saved: {outpng}")

# --- Print summary table ---
print("\n" + "=" * 75)
print("  Comparison Summary (9 core qubits)")
print("=" * 75)
print(f"  {'γ':<6} | {'EMU_FREE ⟨n⟩':<13} | {'EMU_FRESNEL ⟨n⟩':<15} | {'Δ⟨n⟩':<9} | "
      f"{'EMU_FREE P₀':<12} | {'EMU_FRESNEL P₀':<14}")
print("-" * 75)

for i, g in enumerate(emu_fresnel_gamma):
    ref_rho = float(interp_rho(g))
    ref_p0 = float(interp_p0(g))
    dr = emu_fresnel_rho[i] - ref_rho
    dp = emu_fresnel_p0[i] - ref_p0
    print(f"  {g:<6.3f} | {ref_rho:<13.4f} | {emu_fresnel_rho[i]:<15.4f} | {dr:<+9.4f} | "
          f"{ref_p0:<12.1%} | {emu_fresnel_p0[i]:<14.1%}")

plt.close()
