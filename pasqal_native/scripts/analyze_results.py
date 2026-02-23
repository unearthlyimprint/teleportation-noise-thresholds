"""
CFD Wormhole — Pasqal Results Analysis
=======================================
Generates publication-quality plots from EMU_FREE results:
  1. Mean Rydberg Density vs γ  (traversability proxy)
  2. Ground State Probability vs γ  (collapse indicator)
  3. Shannon Entropy vs γ            (state diversity)
  4. Per-qubit excitation heatmap

Usage:
    python analyze_results.py [path_to_json]
"""

import json
import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from collections import Counter

# ============================================================================
# STYLE
# ============================================================================

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.grid': True,
    'grid.alpha': 0.3,
})

# Colour palette
C_PRIMARY   = '#2563EB'   # blue
C_SECONDARY = '#DC2626'   # red
C_ACCENT    = '#059669'   # emerald
C_CRITICAL  = '#F59E0B'   # amber
C_BG        = '#F8FAFC'


# ============================================================================
# DATA LOADING
# ============================================================================

def load_results(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


# ============================================================================
# METRICS COMPUTATION
# ============================================================================

def compute_metrics(results: list[dict]) -> dict:
    """Extract physics from raw count data."""
    metrics = {
        'gamma': [],
        'rydberg_density': [],       # mean excitation fraction
        'ground_prob': [],            # P(|000...0⟩)
        'entropy': [],                # Shannon entropy  (log₂)
        'n_distinct': [],             # # of distinct bitstrings
        'per_qubit_excitation': [],   # per-qubit Rydberg probability
    }

    for entry in results:
        if entry.get('status') != 'DONE' or 'counts' not in entry:
            continue

        gamma  = entry['gamma']
        counts = entry['counts']
        total  = sum(counts.values())
        n_qubits = len(next(iter(counts)))  # bitstring length

        # 1. Mean Rydberg density  <n> = avg fraction of '1's
        rydberg_sum = sum(
            bs.count('1') / n_qubits * n for bs, n in counts.items()
        )
        rydberg_density = rydberg_sum / total

        # 2. Ground state probability
        ground_prob = counts.get('0' * n_qubits, 0) / total

        # 3. Shannon entropy
        probs = np.array([n / total for n in counts.values()])
        entropy = -np.sum(probs * np.log2(probs + 1e-15))

        # 4. Per-qubit excitation
        qubit_exc = np.zeros(n_qubits)
        for bs, n in counts.items():
            for i, bit in enumerate(bs):
                if bit == '1':
                    qubit_exc[i] += n
        qubit_exc /= total

        metrics['gamma'].append(gamma)
        metrics['rydberg_density'].append(rydberg_density)
        metrics['ground_prob'].append(ground_prob)
        metrics['entropy'].append(entropy)
        metrics['n_distinct'].append(len(counts))
        metrics['per_qubit_excitation'].append(qubit_exc)

    # Sort by gamma
    idx = np.argsort(metrics['gamma'])
    for key in metrics:
        metrics[key] = [metrics[key][i] for i in idx]

    return metrics


# ============================================================================
# PLOTTING
# ============================================================================

def plot_traversability(metrics: dict, output_dir: str):
    """Fig 1: Mean Rydberg density — traversability proxy."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    gamma = metrics['gamma']
    rho   = metrics['rydberg_density']

    ax.plot(gamma, rho, 'o-', color=C_PRIMARY, lw=2.5, ms=8, mec='white', mew=1.5,
            label=r'$\langle n \rangle$ (Rydberg density)')
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--', lw=1.5, alpha=0.8,
               label=r'$\gamma_c = 0.535$ (CFD critical)')

    ax.set_xlabel(r'Dephasing Strength $\gamma$')
    ax.set_ylabel(r'Mean Rydberg Density $\langle n \rangle$')
    ax.set_title('Rydberg Excitation vs. Dephasing — Pasqal EMU_FREE')
    ax.legend(loc='upper right', framealpha=0.9)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(bottom=-0.01)

    path = os.path.join(output_dir, 'fig1_traversability.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def plot_collapse(metrics: dict, output_dir: str):
    """Fig 2: Ground state probability — collapse indicator."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    gamma = metrics['gamma']
    gp    = metrics['ground_prob']

    ax.plot(gamma, gp, 's-', color=C_SECONDARY, lw=2.5, ms=8, mec='white', mew=1.5,
            label=r'$P(|0\rangle^{\otimes 9})$')
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--', lw=1.5, alpha=0.8,
               label=r'$\gamma_c = 0.535$')
    ax.axhline(y=0.5, color='grey', ls=':', lw=1, alpha=0.5)

    ax.set_xlabel(r'Dephasing Strength $\gamma$')
    ax.set_ylabel(r'Ground State Probability $P_0$')
    ax.set_title('Fidelity Collapse vs. Dephasing — Pasqal EMU_FREE')
    ax.legend(loc='center right', framealpha=0.9)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

    path = os.path.join(output_dir, 'fig2_collapse.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def plot_entropy(metrics: dict, output_dir: str):
    """Fig 3: Shannon entropy — state diversity measure."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    gamma = metrics['gamma']
    ent   = metrics['entropy']

    ax.plot(gamma, ent, 'D-', color=C_ACCENT, lw=2.5, ms=8, mec='white', mew=1.5,
            label=r'$S = -\sum p_i \log_2 p_i$')
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--', lw=1.5, alpha=0.8,
               label=r'$\gamma_c = 0.535$')

    ax.set_xlabel(r'Dephasing Strength $\gamma$')
    ax.set_ylabel(r'Shannon Entropy $S$ (bits)')
    ax.set_title('State Diversity — Pasqal EMU_FREE')
    ax.legend(loc='upper right', framealpha=0.9)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(bottom=-0.1)

    path = os.path.join(output_dir, 'fig3_entropy.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def plot_combined(metrics: dict, output_dir: str):
    """Fig 4: Combined 2×2 panel for manuscript."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor(C_BG)

    gamma = metrics['gamma']

    # Panel A: Rydberg density
    ax = axes[0, 0]
    ax.set_facecolor(C_BG)
    ax.plot(gamma, metrics['rydberg_density'], 'o-', color=C_PRIMARY, lw=2, ms=7, mec='white', mew=1.2)
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--', lw=1.2, alpha=0.7)
    ax.set_xlabel(r'$\gamma$')
    ax.set_ylabel(r'$\langle n \rangle$')
    ax.set_title('(a) Mean Rydberg Density')

    # Panel B: Ground state prob
    ax = axes[0, 1]
    ax.set_facecolor(C_BG)
    ax.plot(gamma, metrics['ground_prob'], 's-', color=C_SECONDARY, lw=2, ms=7, mec='white', mew=1.2)
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--', lw=1.2, alpha=0.7)
    ax.set_xlabel(r'$\gamma$')
    ax.set_ylabel(r'$P_0$')
    ax.set_title('(b) Ground State Probability')

    # Panel C: Shannon entropy
    ax = axes[1, 0]
    ax.set_facecolor(C_BG)
    ax.plot(gamma, metrics['entropy'], 'D-', color=C_ACCENT, lw=2, ms=7, mec='white', mew=1.2)
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--', lw=1.2, alpha=0.7)
    ax.set_xlabel(r'$\gamma$')
    ax.set_ylabel(r'$S$ (bits)')
    ax.set_title('(c) Shannon Entropy')

    # Panel D: Per-qubit excitation heatmap
    ax = axes[1, 1]
    qubit_data = np.array(metrics['per_qubit_excitation'])
    im = ax.imshow(qubit_data.T, aspect='auto', cmap='inferno',
                   extent=[min(gamma)-0.025, max(gamma)+0.025, 8.5, -0.5])
    ax.set_xlabel(r'$\gamma$')
    ax.set_ylabel('Qubit Index')
    ax.set_title('(d) Per-Qubit Excitation')
    ax.set_xticks(gamma)
    ax.set_xticklabels([f'{g:.1f}' for g in gamma], fontsize=9)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'$P(|1\rangle)$')

    for a in axes.flat:
        a.grid(True, alpha=0.2)

    fig.suptitle('System Dynamics under Parametric Dephasing — Pasqal Neutral-Atom Emulation', fontsize=18, y=1.01)
    fig.tight_layout()

    path = os.path.join(output_dir, 'fig4_combined_panel.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")

    # Also save PNG for quick viewing
    png_path = os.path.join(output_dir, 'fig4_combined_panel.png')
    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
    fig2.patch.set_facecolor(C_BG)
    # Re-draw for PNG
    ax = axes2[0, 0]; ax.set_facecolor(C_BG)
    ax.plot(gamma, metrics['rydberg_density'], 'o-', color=C_PRIMARY, lw=2, ms=7, mec='white', mew=1.2)
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--'); ax.set_xlabel(r'$\gamma$'); ax.set_ylabel(r'$\langle n \rangle$'); ax.set_title('(a) Mean Rydberg Density')

    ax = axes2[0, 1]; ax.set_facecolor(C_BG)
    ax.plot(gamma, metrics['ground_prob'], 's-', color=C_SECONDARY, lw=2, ms=7, mec='white', mew=1.2)
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--'); ax.set_xlabel(r'$\gamma$'); ax.set_ylabel(r'$P_0$'); ax.set_title('(b) Ground State Probability')

    ax = axes2[1, 0]; ax.set_facecolor(C_BG)
    ax.plot(gamma, metrics['entropy'], 'D-', color=C_ACCENT, lw=2, ms=7, mec='white', mew=1.2)
    ax.axvline(x=0.535, color=C_CRITICAL, ls='--'); ax.set_xlabel(r'$\gamma$'); ax.set_ylabel(r'$S$ (bits)'); ax.set_title('(c) Shannon Entropy')

    ax = axes2[1, 1]
    im = ax.imshow(qubit_data.T, aspect='auto', cmap='inferno', extent=[min(gamma)-0.025, max(gamma)+0.025, 8.5, -0.5])
    ax.set_xlabel(r'$\gamma$'); ax.set_ylabel('Qubit Index'); ax.set_title('(d) Per-Qubit Excitation')
    fig2.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label(r'$P(|1\rangle)$')

    for a in axes2.flat: a.grid(True, alpha=0.2)
    fig2.suptitle('System Dynamics under Parametric Dephasing — Pasqal Neutral-Atom Emulation', fontsize=18, y=1.01)
    fig2.tight_layout()
    fig2.savefig(png_path)
    plt.close(fig2)
    print(f"  Saved: {png_path}")

    return path


def print_summary_table(metrics: dict):
    """Print a LaTeX-ready summary table."""
    print("\n" + "=" * 70)
    print("  Summary Table")
    print("=" * 70)
    print(f"{'γ':>6} | {'⟨n⟩':>8} | {'P₀':>8} | {'S (bits)':>10} | {'# states':>8}")
    print("-" * 55)
    for i in range(len(metrics['gamma'])):
        print(f"{metrics['gamma'][i]:>6.3f} | "
              f"{metrics['rydberg_density'][i]:>8.4f} | "
              f"{metrics['ground_prob'][i]:>8.2f} | "
              f"{metrics['entropy'][i]:>10.4f} | "
              f"{metrics['n_distinct'][i]:>8d}")
    print("-" * 55)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Find results files
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        # Auto-detect latest results file
        json_files = sorted([
            f for f in os.listdir(results_dir)
            if f.endswith('.json') and f.startswith('pasqal_')
        ])
        if not json_files:
            print("ERROR: No results JSON found in ../results/")
            sys.exit(1)
        json_path = os.path.join(results_dir, json_files[-1])

    print(f"Loading: {json_path}")
    results = load_results(json_path)
    metrics = compute_metrics(results)

    # Output directory for figures
    fig_dir = os.path.join(os.path.dirname(__file__), '..', 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    print("\nGenerating figures...")
    plot_traversability(metrics, fig_dir)
    plot_collapse(metrics, fig_dir)
    plot_entropy(metrics, fig_dir)
    plot_combined(metrics, fig_dir)
    print_summary_table(metrics)

    print(f"\nAll figures saved to: {fig_dir}")
