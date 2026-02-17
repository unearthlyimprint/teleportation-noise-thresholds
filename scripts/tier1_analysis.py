"""
Tier 1 Analysis: Fit and Plot Depth Sweep Results
===================================================

Takes the JSON output from tier1_depth_sweep.py and:
1. Plots fidelity vs entangling gate count
2. Fits three models: sharp (CFD), exponential (standard), linear
3. Computes chi-squared goodness-of-fit for each
4. Generates publication-quality figure

Usage:
  python tier1_analysis.py tier1_results_hardware_YYYYMMDD_HHMMSS.json

Or manually enter results:
  python tier1_analysis.py --manual
"""

import sys
import json
import argparse
import numpy as np

def load_results(filename):
    """Load results from JSON file."""
    with open(filename, 'r') as f:
        data = json.load(f)
    return data['results']

def manual_entry():
    """Manually enter hardware results."""
    print("\nEnter results from Forte-1 hardware run:")
    print("(Enter fidelity for each circuit size)\n")
    
    configs = [
        (1, 3, 10),
        (2, 5, 17),
        (3, 7, 24),
        (4, 9, 31),
    ]
    
    results = []
    for n_pairs, qubits, cx in configs:
        f_str = input(f"  N={n_pairs} ({qubits} qubits, {cx} CX gates) — Fidelity: ")
        s_str = input(f"  N={n_pairs} — Sigma (uncertainty): ")
        results.append({
            'n_pairs': n_pairs,
            'total_qubits': qubits,
            'cx_total': cx,
            'fidelity': float(f_str),
            'sigma': float(s_str),
        })
    
    return results

def fit_models(cx_gates, fidelities, sigmas):
    """
    Fit three competing models to the data.
    
    Model 1 (CFD): Sharp transition — sigmoid/step function
      F(n) = F_max / (1 + exp((n - n_c) / w))
      where n_c is the critical gate count and w is transition width
    
    Model 2 (Standard): Exponential decay
      F(n) = A * exp(-n / n_char)
      where n_char is the characteristic decay length
    
    Model 3 (Linear): Simple linear decay
      F(n) = a - b*n
    """
    from scipy.optimize import curve_fit
    from scipy.stats import chi2
    
    n = np.array(cx_gates, dtype=float)
    f = np.array(fidelities, dtype=float)
    s = np.array(sigmas, dtype=float)
    
    # Replace zero sigmas with small value to avoid division issues
    s = np.where(s < 0.01, 0.05, s)
    
    fits = {}
    
    # --- Model 1: Sigmoid (CFD sharp transition) ---
    def sigmoid(n, f_max, n_c, w):
        return f_max / (1 + np.exp((n - n_c) / w))
    
    try:
        popt, pcov = curve_fit(sigmoid, n, f, p0=[1.0, 20, 3], 
                               sigma=s, absolute_sigma=True,
                               bounds=([0, 5, 0.5], [1.5, 40, 15]))
        residuals = f - sigmoid(n, *popt)
        chi2_val = np.sum((residuals / s)**2)
        dof = len(n) - 3
        p_value = 1 - chi2.cdf(chi2_val, max(dof, 1))
        
        fits['sigmoid_cfd'] = {
            'params': {'F_max': popt[0], 'n_critical': popt[1], 'width': popt[2]},
            'chi2': chi2_val,
            'dof': dof,
            'p_value': p_value,
            'label': f'CFD sigmoid (n_c={popt[1]:.1f}, w={popt[2]:.1f})',
            'func': lambda n_arr, p=popt: sigmoid(n_arr, *p),
        }
    except Exception as e:
        fits['sigmoid_cfd'] = {'error': str(e)}
    
    # --- Model 2: Exponential decay ---
    def exp_decay(n, a, n_char):
        return a * np.exp(-n / n_char)
    
    try:
        popt, pcov = curve_fit(exp_decay, n, f, p0=[1.0, 15],
                               sigma=s, absolute_sigma=True,
                               bounds=([0, 1], [2.0, 100]))
        residuals = f - exp_decay(n, *popt)
        chi2_val = np.sum((residuals / s)**2)
        dof = len(n) - 2
        p_value = 1 - chi2.cdf(chi2_val, max(dof, 1))
        
        fits['exponential'] = {
            'params': {'A': popt[0], 'n_char': popt[1]},
            'chi2': chi2_val,
            'dof': dof,
            'p_value': p_value,
            'label': f'Exponential (n_char={popt[1]:.1f})',
            'func': lambda n_arr, p=popt: exp_decay(n_arr, *p),
        }
    except Exception as e:
        fits['exponential'] = {'error': str(e)}
    
    # --- Model 3: Linear decay ---
    def linear(n, a, b):
        return a - b * n
    
    try:
        popt, pcov = curve_fit(linear, n, f, p0=[1.0, 0.03],
                               sigma=s, absolute_sigma=True)
        residuals = f - linear(n, *popt)
        chi2_val = np.sum((residuals / s)**2)
        dof = len(n) - 2
        p_value = 1 - chi2.cdf(chi2_val, max(dof, 1))
        
        fits['linear'] = {
            'params': {'intercept': popt[0], 'slope': popt[1]},
            'chi2': chi2_val,
            'dof': dof,
            'p_value': p_value,
            'label': f'Linear (slope={popt[1]:.4f})',
            'func': lambda n_arr, p=popt: linear(n_arr, *p),
        }
    except Exception as e:
        fits['linear'] = {'error': str(e)}
    
    return fits


def plot_results(results, fits, output_file='tier1_depth_sweep.png'):
    """Generate publication-quality figure."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    
    cx_gates = [r.get('cx_total', 0) for r in results]
    fidelities = [r.get('fidelity', 1.0) for r in results]
    sigmas = [r.get('sigma', 0.05) for r in results]
    qubits = [r.get('total_qubits', 0) for r in results]

    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [2, 1]})
    
    # --- Left panel: Fidelity vs Gate Count ---
    ax1.errorbar(cx_gates, fidelities, yerr=sigmas, 
                 fmt='o', markersize=10, capsize=5, capthick=2,
                 color='#d62728', ecolor='#d62728', 
                 label='IonQ Forte-1 Hardware', zorder=5)
    
    # Add qubit labels
    for i, (cx, f, q) in enumerate(zip(cx_gates, fidelities, qubits)):
        ax1.annotate(f'{q}q', (cx, f), textcoords="offset points",
                    xytext=(12, 8), fontsize=10, fontweight='bold',
                    color='#333333')
    
    # Plot model fits
    n_smooth = np.linspace(5, 35, 200)
    
    colors = {
        'sigmoid_cfd': ('#1f77b4', '-', 2.5),
        'exponential': ('#ff7f0e', '--', 2.0),
        'linear': ('#2ca02c', ':', 2.0),
    }
    
    for model_name, fit_data in fits.items():
        if 'error' not in fit_data:
            c, ls, lw = colors.get(model_name, ('gray', '-', 1))
            y_fit = fit_data['func'](n_smooth)
            ax1.plot(n_smooth, y_fit, color=c, linestyle=ls, linewidth=lw,
                    label=fit_data['label'], alpha=0.8)
    
    # Reference lines
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax1.axhline(y=2/3 - 0.5, color='gray', linestyle='--', alpha=0.4)  # Classical bound mapped
    ax1.text(33, 0.35, 'Classical\nbound', fontsize=8, color='gray', 
             ha='right', style='italic')
    
    ax1.set_xlabel('Entangling Gates (CNOT equivalent)', fontsize=13)
    ax1.set_ylabel('Teleportation Fidelity F', fontsize=13)
    ax1.set_title('Wormhole Fidelity vs Circuit Depth\nIonQ Forte-1 Hardware (γ = 0)', fontsize=14)
    ax1.legend(fontsize=10, loc='upper right')
    ax1.set_xlim(5, 36)
    ax1.set_ylim(-0.15, 1.15)
    ax1.grid(True, alpha=0.3)
    
    # --- Right panel: Model comparison ---
    model_names = []
    chi2_values = []
    bar_colors = []
    
    color_map = {'sigmoid_cfd': '#1f77b4', 'exponential': '#ff7f0e', 'linear': '#2ca02c'}
    label_map = {'sigmoid_cfd': 'CFD\n(sigmoid)', 'exponential': 'Standard\n(exponential)', 'linear': 'Linear'}
    
    for model_name, fit_data in fits.items():
        if 'error' not in fit_data:
            model_names.append(label_map.get(model_name, model_name))
            chi2_values.append(fit_data['chi2'])
            bar_colors.append(color_map.get(model_name, 'gray'))
    
    if model_names:
        bars = ax2.barh(model_names, chi2_values, color=bar_colors, alpha=0.7, edgecolor='black')
        ax2.set_xlabel('χ² (lower = better fit)', fontsize=12)
        ax2.set_title('Model Comparison', fontsize=14)
        
        for bar, val in zip(bars, chi2_values):
            ax2.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                    f'{val:.3f}', va='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"\nFigure saved to: {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Analyze Tier 1 depth sweep results')
    parser.add_argument('filename', nargs='?', help='JSON results file')
    parser.add_argument('--manual', action='store_true', help='Enter results manually')
    args = parser.parse_args()
    
    if args.manual:
        results = manual_entry()
    elif args.filename:
        results = load_results(args.filename)
    else:
        print("Usage: python tier1_analysis.py <results.json>")
        print("       python tier1_analysis.py --manual")
        sys.exit(1)
    
    # Extract arrays
    cx_gates = [r.get('cx_total', 0) for r in results]
    fidelities = [r.get('fidelity', 1.0) for r in results]
    sigmas = [r.get('sigma', 0.05) for r in results]
    qubits = [r.get('total_qubits', 0) for r in results]

    
    print("\n" + "=" * 60)
    print("MODEL FITTING")
    print("=" * 60)
    
    fits = fit_models(cx_gates, fidelities, sigmas)
    
    for model_name, fit_data in fits.items():
        print(f"\n--- {model_name.upper()} ---")
        if 'error' in fit_data:
            print(f"  Fit failed: {fit_data['error']}")
        else:
            print(f"  Parameters: {fit_data['params']}")
            print(f"  χ² = {fit_data['chi2']:.4f}  (dof = {fit_data['dof']})")
            print(f"  p-value = {fit_data['p_value']:.4f}")
    
    # --- Verdict ---
    valid_fits = {k: v for k, v in fits.items() if 'error' not in v}
    if valid_fits:
        best = min(valid_fits.items(), key=lambda x: x[1]['chi2'])
        print(f"\n{'='*60}")
        print(f"BEST FIT: {best[0].upper()}")
        print(f"  χ² = {best[1]['chi2']:.4f}")
        
        if best[0] == 'sigmoid_cfd':
            n_c = best[1]['params']['n_critical']
            w = best[1]['params']['width']
            print(f"  Critical gate count: {n_c:.1f} ± {w:.1f}")
            print(f"  → SUPPORTS CFD phase boundary interpretation")
            # Map back to qubit count
            for n_pairs in [1, 2, 3, 4]:
                cx = 7 * n_pairs + 3
                if abs(cx - n_c) < w:
                    print(f"  → Phase boundary near N={n_pairs} pairs "
                          f"({2*n_pairs+1} qubits)")
        elif best[0] == 'exponential':
            print(f"  Characteristic scale: {best[1]['params']['n_char']:.1f} gates")
            print(f"  → Standard decoherence (smooth exponential)")
        elif best[0] == 'linear':
            print(f"  → Simple linear degradation")
    
    # --- Plot ---
    try:
        plot_results(results, fits)
    except ImportError:
        print("\n(matplotlib not available — skipping plot)")
    except Exception as e:
        print(f"\nPlotting error: {e}")


if __name__ == '__main__':
    main()
