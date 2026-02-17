import json
import os
import glob
import sys

# Path to results directory
results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')

def load_all_results():
    json_files = glob.glob(os.path.join(results_dir, "pasqal_*.json"))
    all_data = []
    print(f"Loading {len(json_files)} files...")
    for f in json_files:
        try:
            with open(f) as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    all_data.extend(data)
                    print(f"  + {os.path.basename(f)}: {len(data)} entries")
        except Exception as e:
            print(f"  ! Error loading {f}: {e}")
    return all_data

def merge_datasets(raw_data):
    """
    Priority:
    1. Status=DONE
    2. Higher shot count (sum of counts)
    3. Latest in list (if duplicate gamma)
    """
    merged = {}
    
    for entry in raw_data:
        gamma = entry.get('gamma')
        if gamma is None: continue
        
        # Round gamma to avoid float key mismatch
        g_key = round(gamma, 4)
        
        status = entry.get('status', 'UNKNOWN')
        counts = entry.get('counts') or {}
        n_shots = sum(counts.values())
        
        # Determine if this entry is better than existing
        is_better = True
        if g_key in merged:
            curr = merged[g_key]
            curr_status = curr.get('status')
            curr_shots = sum((curr.get('counts') or {}).values())
            
            if curr_status == 'DONE' and status != 'DONE':
                is_better = False
            elif curr_status == 'DONE' and status == 'DONE':
                if curr_shots >= n_shots:
                    is_better = False
            # If both not DONE, new one replaces old (maybe retrying later)
            
        if is_better:
            entry['gamma'] = g_key # Standardize
            merged[g_key] = entry

    # Sort
    final = list(merged.values())
    final.sort(key=lambda x: x['gamma'])
    return final

if __name__ == "__main__":
    print("--- Merging Results ---")
    raw = load_all_results()
    merged = merge_datasets(raw)
    
    out_file = os.path.join(results_dir, "pasqal_merged_final.json")
    with open(out_file, "w") as f:
        json.dump(merged, f, indent=2)
        
    print(f"\nSaved combined dataset to: {out_file}")
    print(f"Total unique points: {len(merged)}")
    
    print("\n--- Data Summary ---")
    print(f"{'γ':>6} | {'Status':>8} | {'Shots':>6} | {'P₀':>6}")
    print("-" * 34)
    for r in merged:
        c = r.get('counts') or {}
        n = sum(c.values())
        p0 = c.get('0'*9, 0)/n if n>0 else 0
        s = r.get('status', '?')
        print(f"{r['gamma']:>6.3f} | {s:>8} | {n:>6} | {p0:>6.1%}")
