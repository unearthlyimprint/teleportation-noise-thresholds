# F_bond Unified Manuscript: Comprehensive Review & Action Plan

**Date:** February 13, 2026  
**Author of Review:** Claude (for Celal Arda)  
**Target Journal:** ACS Omega (via transfer from JCTC ct-2026-00261p)

---

## 1. Executive Summary

The JCTC rejection is constructive—the editor acknowledges scientific merit and offers a transfer to ACS Omega. The core criticism is that the paper reads "like a report" and is "not fully developed." This is an opportunity: rather than patching the framework paper alone, you should unify ALL your F_bond work (framework + 4 application systems) into a single, complete, data-rich manuscript that demonstrates the descriptor across diverse chemical bonding regimes. This transforms the weakness (theoretical framework with only NH₃ validation) into a strength (comprehensive validation across ~15 systems spanning 4 orders of magnitude in F_bond).

**However, I have identified several critical inconsistencies that MUST be resolved before submission.** These are detailed below.

---

## 2. CRITICAL INCONSISTENCIES (Must Fix Before Any Submission)

### 🔴 ISSUE #1: TWO DIFFERENT F_bond DEFINITIONS USED ACROSS PAPERS

This is the most serious problem. Your papers use two fundamentally different formulas both called "F_bond":

**Formula A** (Framework paper + Cs₃Al paper):
```
F_bond = (1/2) × O_MOS × S_{E,max}
```
Where O_MOS = HOMO–LUMO gap (Ha), S_{E,max} = transformed entanglement entropy (nats)

**Formula B** (Al₄ paper + B₁₂/BN paper):
```
F_bond = Σᵢ nᵢ(2 − nᵢ)
```
Where nᵢ = natural orbital occupation numbers

**These are completely different quantities.** Formula A is a product of an energy gap and entropy. Formula B is a sum of occupation-based measures. They have different units, different magnitudes, and different physical meanings. You cannot compare F_bond values across papers that use different formulas.

**Evidence of the confusion:**
- CSV data (7 molecules, Formula A): H₂ F_bond = 0.0425, N₂ = 0.0667
- Cs₃Al paper Table 2 (claiming to compare): H₂ = 0.391, N₂ = 0.482 — these appear to be Formula B values
- Cs₃Al systems (Formula A): F_bond ≈ 0.013
- B₁₂ systems (Formula B): F_bond ≈ 0.43
- Al₄²⁻ singlet (Formula B): F_bond ≈ 0.0007

**Resolution required:** You must either:
(a) Pick ONE formula and recompute ALL systems, or  
(b) Clearly define both as distinct quantities (e.g., F_bond^{gap} and F_bond^{occ}) with explicit notation  
(c) Show the mathematical relationship between the two, if one exists

**Recommendation:** Use Formula B (Σ nᵢ(2−nᵢ)) as the primary descriptor for the unified paper—it is simpler, directly measurable from any correlated calculation, and does not require the somewhat ad hoc O_MOS → entropy transformation. Present Formula A as a derived/simplified version for specific contexts (HOMO-LUMO gap analysis).

---

### 🔴 ISSUE #2: Al₄⁴⁻ TRIPLET F_bond VALUE — DATA vs MANUSCRIPT MISMATCH

**JSON data** (`Al4_4minus_triplet_results.json`): F_bond = **6.000**  
- 6 orbitals with occupation ≈ 1.0 each → 6 × 1 × (2−1) = 6.0

**Manuscript** (`al4_fbond_manuscript.tex`): F_bond ≈ **4.17**  
**Figure caption**: F_bond = **4.1680**

**Where does 4.17 come from?** It does not match the JSON data. The computed data clearly gives 6.0. This is a serious data integrity issue.

**Possible explanations:**
- An earlier calculation with different active space or different formula
- A bug in the figure-generation script
- Using a different number of active orbitals (e.g., only 4 instead of 6)

**Resolution required:** Recompute and verify. The JSON data (6.0) is the raw computational output and is likely correct. The manuscript value (4.17) must be explained or corrected.

---

### 🔴 ISSUE #3: WRONG CROSS-REFERENCES IN Al₄ PAPER

The Al₄ manuscript states:  
> "Cs₃Al₈⁻ exhibited F_bond ≈ 4.2 and Cs₃Al₁₂⁻ showed F_bond ≈ 5.8 due to cluster orbital degeneracies"

**Actual computed values** (from `fbond_results_combined.json` and `main_manuscript.tex`):
- Cs₃Al₈⁻: F_bond = **0.01270**
- Cs₃Al₁₂⁻: F_bond = **0.01280**

The claimed values (4.2 and 5.8) are off by a factor of ~300–450×. This is completely wrong and would immediately discredit the paper if caught by a reviewer.

**Root cause:** Likely confusion between Formula A and Formula B, or values from a different calculation that was later superseded.

**Resolution:** Correct all cross-references. If using Formula B consistently in the unified paper, recompute Cs₃Al values with that formula.

---

### 🟡 ISSUE #4: Cs₃Al₈⁻ Valence Electron Count Error

File `cs3al8_results.txt` states: "132 (40 valence electrons)"  
**Correct value:** 28 valence electrons (8×3 + 3×1 + 1 = 28)  
The "40 valence electrons" is the count for Cs₃Al₁₂⁻, not Cs₃Al₈⁻.

---

### 🟡 ISSUE #5: Minor Numerical Discrepancies in B₁₂

- B₁₂ icosahedral manuscript: F_bond = 0.427; JSON: F_bond = 0.4244
- B₁₂ planar manuscript: F_bond = 0.428; JSON: F_bond = 0.4279

These are rounding differences but should be consistent (use 3 significant figures throughout).

---

### 🟡 ISSUE #6: Cs₃Al Comparison Table Uses Mixed F_bond Formulas

Table 2 in `main_manuscript.tex` lists:
- H₂: F_bond = 0.391
- N₂: F_bond = 0.482
- Benzene: ~0.35–0.40

But the CSV (`Complete_7_Molecule_Summary_v2.csv`) using Formula A gives:
- H₂: F_bond = 0.0425
- N₂: F_bond = 0.0667

The Table 2 values appear to use Formula B. This means Table 2 compares Formula B values (H₂, N₂) with Formula A values (Cs₃Al systems at ~0.013). This is comparing apples to oranges.

---

### 🟡 ISSUE #7: Basis Set Inconsistency Across Systems

- Original 7 molecules: **STO-3G** (minimal basis, FCI method)
- Al₄, B₁₂, BN, Cs₃Al: **def2-SVP** (split-valence + polarization, CCSD method)

STO-3G results are qualitative at best. F_bond values from STO-3G/FCI cannot be quantitatively compared with def2-SVP/CCSD values. The unified paper must either:
(a) Recompute the small molecules at def2-SVP/CCSD, or  
(b) Clearly caveat that comparisons between basis sets are qualitative only

---

## 3. STRUCTURAL ANALYSIS OF EXISTING MANUSCRIPTS

### 3.1 Framework Paper (chemical_bonding_framework.tex) — JCTC Rejected

**Strengths:** Rigorous mathematical formulation, good theoretical breadth, proper citations  
**Weaknesses (editor's criticism):**
- Only validated on NH₃ (single closed-shell molecule)
- Reads as a theoretical review/report, not a research paper
- F_bond value (5.22×10⁻⁴) is only one data point
- No comparison across bonding regimes
- Many sections are aspirational ("future work") rather than demonstrated

### 3.2 Cs₃Al Superatom Paper (main_manuscript.tex) — ChemRxiv Published

**Strengths:** Clear narrative, interesting finding (size-independence), well-structured  
**Weaknesses:**
- Uses Formula A for F_bond
- Comparison Table 2 mixes Formula A and Formula B values
- Limited to two data points in the same chemical family
- Benzene value is "estimated" (footnote a)

### 3.3 Al₄ Aromaticity Paper (al4_fbond_manuscript.tex) — Draft

**Strengths:** Clear aromaticity/antiaromaticity comparison, triplet analysis  
**Weaknesses:**
- Uses Formula B (different from framework and Cs₃Al)
- F_bond triplet value (4.17) contradicts JSON data (6.0)
- Cross-references to Cs₃Al are wrong (quotes 4.2/5.8 instead of 0.013)
- References contain placeholders (\cite{YourPreviousWork}, \cite{YourCs3AlWork})
- Missing correlation energies in Table 1

### 3.4 Boron/BN Paper (boron_fbond_manuscript.tex) — Draft

**Strengths:** Interesting geometry vs. chemistry comparison, clear results  
**Weaknesses:**
- Uses Formula B (inconsistent with framework)
- Very short manuscript (essentially a communication)
- Missing B₁₂N₁₂ data (calculation still running)
- Incomplete references

### 3.5 B₁₂N₁₂ Calculation — Still Running

Lambda equations at cycle 61, norm ≈ 1.7×10⁻⁴ (converging slowly).  
**Risk:** May not converge to tolerance (1×10⁻⁵) without further intervention.

### 3.6 Au₂₅ Ligand-Protected Cluster — Not Started

No data, no manuscript. This should be listed as future work only.

---

## 4. PROPOSED UNIFIED MANUSCRIPT STRUCTURE

### Title (suggested):
**"The F_bond Descriptor: A Universal Quantum Correlation Measure Across Molecular, Cluster, and Superatom Systems"**

### Target: ACS Omega (broad scope, interdisciplinary, accepts comprehensive studies)

### Proposed Structure:

**Abstract** (~250 words)  
Present F_bond as a universal descriptor. Highlight key results: 15+ systems spanning closed-shell molecules to open-shell clusters, F_bond ranges from ~10⁻⁴ to ~6.0, clear regime separation.

**1. Introduction** (1.5 pages)  
- Chemical bonding as a multifaceted concept
- Limitations of existing descriptors (NICS, ELF, etc.)
- Need for a unified quantum information descriptor
- F_bond concept and goals of this work
- (Condense the framework paper introduction heavily)

**2. Theory** (2 pages)  
- Electronic structure foundations (brief)
- Natural orbital analysis and occupation numbers
- F_bond definition — USE ONE CONSISTENT FORMULA
- Relationship to orbital entanglement entropy
- Classification scheme (weak/moderate/strong correlation regimes)
- Connection to HOMO-LUMO gap analysis

**3. Computational Methods** (1.5 pages)  
- FCI calculations for small molecules (H₂, NH₃, H₂O, CH₄, N₂, C₂H₂, C₂H₄)
- CCSD calculations for clusters (Al₄, B₁₂, B₆N₆, Cs₃Al)
- Basis sets, convergence criteria, software
- Natural orbital extraction protocol
- Honest discussion of basis set limitations (STO-3G vs def2-SVP)

**4. Results** (4–5 pages)  
- **4.1 Small Molecules: Establishing the F_bond Scale**
  - Table: All 7 molecules with energies, occupations, F_bond
  - Regime classification (weak vs strong correlation)
  
- **4.2 Aluminum Clusters: Aromaticity and Spin States**
  - Al₄²⁻ (aromatic) vs Al₄⁴⁻ (antiaromatic)
  - Singlet vs triplet comparison
  - Connection to Hückel rules
  
- **4.3 Boron and BN Clusters: Geometry vs Chemistry**
  - B₁₂ planar vs icosahedral (geometry effect: negligible)
  - B₁₂ vs B₆N₆ (heteroatomic effect: +68%)
  - B₁₂N₁₂ if available
  
- **4.4 Superatom Clusters: Size-Independent Signatures**
  - Cs₃Al₈⁻ vs Cs₃Al₁₂⁻
  - Compensating gap/entropy mechanism
  - Magic number analysis

- **4.5 Unified F_bond Landscape**
  - Master table: ALL systems
  - Master figure: F_bond across all systems (bar chart or scatter)
  - Regime boundaries and classification

**5. Discussion** (2–3 pages)  
- Physical interpretation of F_bond regimes
- Comparison to existing descriptors (NICS, ELF, T₁ diagnostic)
- Diagnostic utility: when to use multireference methods
- Limitations and caveats
- Comparison with CASSCF/DMRG approaches for multiconfigurational character

**6. Conclusions and Outlook** (0.5–1 page)  
- Summary of key findings
- Future directions: Au₂₅, reaction pathways, excited states, larger basis sets

**Supporting Information**  
- Complete natural orbital occupations for all systems
- Optimized geometries (XYZ)
- Calculation scripts and reproducibility guide
- Basis set convergence tests (if available)

---

## 5. ACTION PLAN

### Phase 1: Data Integrity (Days 1–3) ⚡ CRITICAL

| # | Task | Priority | Status |
|---|------|----------|--------|
| 1.1 | **Choose ONE F_bond formula** for the unified paper | 🔴 Critical | Not started |
| 1.2 | **Recompute all F_bond values** with the chosen formula | 🔴 Critical | Not started |
| 1.3 | **Resolve Al₄⁴⁻ triplet discrepancy** (4.17 vs 6.0) | 🔴 Critical | Not started |
| 1.4 | **Fix all cross-reference errors** (Cs₃Al values in Al₄ paper) | 🔴 Critical | Not started |
| 1.5 | **Fix Cs₃Al₈⁻ valence electron count** (28, not 40) | 🟡 Medium | Not started |
| 1.6 | **Verify all JSON ↔ manuscript numerical consistency** | 🔴 Critical | Not started |
| 1.7 | **Decide on B₁₂N₁₂**: include if converged, drop if not | 🟡 Medium | Running |

### Phase 2: Recomputation (Days 3–7) — If Using Formula B Consistently

| # | Task | Priority | Notes |
|---|------|----------|-------|
| 2.1 | Recompute 7 small molecules with Formula B at STO-3G/FCI | 🟡 Medium | Already have wavefunctions |
| 2.2 | Recompute Cs₃Al systems with Formula B from existing CCSD density matrices | 🔴 Critical | Need Σ nᵢ(2−nᵢ) from existing occupations |
| 2.3 | (Optional) Recompute small molecules at def2-SVP/CCSD for fair comparison | 🟢 Nice to have | Strengthen paper significantly |
| 2.4 | Create master data table with ALL systems, one formula | 🔴 Critical | — |

### Phase 3: Manuscript Writing (Days 5–14)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| 3.1 | Write unified Introduction (condense framework + motivate applications) | 🔴 Critical | Cut framework from 10 pages to 2 |
| 3.2 | Write Theory section (one clear F_bond definition) | 🔴 Critical | Resolve formula issue first |
| 3.3 | Write Methods (two subsections: FCI for molecules, CCSD for clusters) | 🟡 Medium | Largely exists |
| 3.4 | Write Results sections (4 subsections as outlined above) | 🔴 Critical | Integrate existing work |
| 3.5 | Create master comparison figure | 🔴 Critical | Most impactful figure |
| 3.6 | Write Discussion (new, connects all results) | 🔴 Critical | The "added value" section |
| 3.7 | Write Conclusions | 🟡 Medium | — |
| 3.8 | Compile SI with all data | 🟡 Medium | Extend existing SI |

### Phase 4: Quality Control (Days 12–16)

| # | Task | Priority |
|---|------|----------|
| 4.1 | Cross-check every number: manuscript ↔ JSON ↔ figures | 🔴 Critical |
| 4.2 | Verify all references (replace placeholders like \cite{YourPreviousWork}) | 🔴 Critical |
| 4.3 | Check figure quality (300 dpi, consistent styling) | 🟡 Medium |
| 4.4 | Proofread for grammar/style (report → paper tone) | 🟡 Medium |
| 4.5 | Format for ACS Omega (use achemso class) | 🟡 Medium |
| 4.6 | Prepare cover letter addressing JCTC editor feedback | 🟡 Medium |

### Phase 5: Submission (Days 16–18)

| # | Task |
|---|------|
| 5.1 | Final compilation and PDF check |
| 5.2 | Upload via ACS manuscript transfer |
| 5.3 | Upload supplementary files (XYZ, JSON, scripts) |
| 5.4 | Submit |

---

## 6. SPECIFIC RECOMMENDATIONS

### 6.1 On the F_bond Formula Decision

**Strongest option:** Use **Formula B** (F_bond = Σ nᵢ(2−nᵢ)) as the primary descriptor because:
- It is directly computable from ANY post-HF method (CCSD, CASSCF, DMRG, FCI)
- It does not require the ad hoc entropy transformation
- It has a clear physical interpretation (deviation from idempotency)
- It is already established in the literature (related to the "I_ND" or "T_1"-like diagnostics)

Then present the HOMO-LUMO gap analysis (O_MOS × S_E,max version) as a **complementary** measure in the Cs₃Al section, showing how it captures compensating trends. But make clear these are two different quantities.

### 6.2 On the JCTC Editor's Feedback

The editor's criticisms map directly to what we're fixing:
- "Not within scope" → ACS Omega has broader scope ✅
- "Written like a report" → Restructure as an applications paper with results ✅
- "Not fully developed" → Add all 15+ systems with consistent data ✅

### 6.3 On the Au₂₅ System

Do NOT include Au₂₅ in the unified paper if calculations haven't started. Mention it in "Future Directions" only. Including half-baked or placeholder data will weaken the paper.

### 6.4 On the B₁₂N₁₂ Calculation

The lambda equations are converging but slowly (norm ~1.7×10⁻⁴ at cycle 61). Two options:
- **Wait:** It may converge within 100–150 more cycles. If F_bond turns out reasonable, include it.
- **Proceed without it:** The paper is strong with B₁₂ + B₆N₆. Add B₁₂N₁₂ as future work.

### 6.5 On Basis Set Concerns

Be transparent about STO-3G limitations. Add a paragraph in the Methods section:
> "The STO-3G basis set for small molecules, while providing qualitatively correct F_bond trends, likely underestimates absolute correlation effects. Quantitative comparison between STO-3G/FCI and def2-SVP/CCSD results should be interpreted cautiously. A systematic basis set convergence study is planned for future work."

### 6.6 Key Figures for the Unified Paper

1. **Master F_bond bar chart** — All ~15 systems organized by bonding regime (most important figure)
2. **Al₄ singlet/triplet comparison** (existing figure, corrected values)
3. **B₁₂ geometry vs BN chemistry comparison** (existing concept, updated)
4. **Cs₃Al compensating trends diagram** (gap vs entropy)
5. **Natural orbital occupation diagram** for representative systems

---

## 7. SYSTEMS INVENTORY AND DATA STATUS

| System | Formula Used | F_bond | Basis/Method | Status | Data Verified? |
|--------|-------------|--------|-------------|--------|---------------|
| NH₃ | A | 0.0321 | STO-3G/FCI | ✅ | ✅ |
| H₂O | A | 0.0352 | STO-3G/FCI | ✅ | ✅ |
| CH₄ | A | 0.0400 | STO-3G/FCI | ✅ | ✅ |
| H₂ | A | 0.0425 | STO-3G/FCI | ✅ | ✅ |
| C₂H₂ | A | 0.0651 | STO-3G/FCI | ✅ | ✅ |
| N₂ | A | 0.0667 | STO-3G/FCI | ✅ | ✅ |
| C₂H₄ | A | 0.0718 | STO-3G/FCI | ✅ | ✅ |
| Al₄²⁻ (S) | B | 0.000621 | def2-SVP/CCSD | ✅ | ✅ |
| Al₄⁴⁻ (S) | B | 0.000704 | def2-SVP/CCSD | ✅ | ✅ |
| Al₄⁴⁻ (T) | B | **6.0 (JSON) vs 4.17 (ms)** | def2-SVP/CCSD | ⚠️ CONFLICT | ❌ |
| B₁₂ planar | B | 0.4279 | def2-SVP/CCSD | ✅ | ✅ |
| B₁₂ icosahedral | B | 0.4244 | def2-SVP/CCSD | ✅ | ✅ |
| B₆N₆ planar | B | 0.7182 | def2-SVP/CCSD | ✅ | ✅ |
| B₁₂N₁₂ cage | B | TBD | def2-SVP/CCSD | ⏳ Running | — |
| Cs₃Al₈⁻ | A | 0.01270 | def2-SVP/CCSD | ✅ | ✅ |
| Cs₃Al₁₂⁻ | A | 0.01280 | def2-SVP/CCSD | ✅ | ✅ |
| Au₂₅ | — | — | — | ❌ Not started | — |

**Minimum for publication:** 13 systems (excluding B₁₂N₁₂ and Au₂₅), with consistent formula

---

## 8. ESTIMATED TIMELINE

| Week | Tasks |
|------|-------|
| Week 1 (Feb 13–19) | Resolve all critical data issues (#1–#3). Choose formula. Recompute as needed. |
| Week 2 (Feb 20–26) | Write unified manuscript sections 1–4 (Theory, Methods, Results). Create figures. |
| Week 3 (Feb 27–Mar 5) | Write Discussion, Conclusions. Compile SI. Internal review. |
| Week 4 (Mar 6–12) | Proofreading, formatting, final cross-checks. Submit to ACS Omega. |

---

## 9. FINAL NOTES

This project has genuine scientific value. The F_bond descriptor—once consistently defined—offers a simple, interpretable measure of electron correlation across diverse systems. The dataset you've assembled (small molecules → aluminum clusters → boron clusters → superatom systems) is impressive for a solo researcher and spans a wide range of bonding scenarios.

The main risk is the inconsistency issue. If a reviewer notices different formulas being compared as if they're the same quantity, the paper will be immediately rejected. Fix this first, and everything else follows.

The JCTC-to-ACS-Omega transfer is genuinely positive—ACS Omega is a well-regarded journal that welcomes this kind of comprehensive, cross-disciplinary work. With consistent data and a strong narrative, this has a good chance of acceptance.
