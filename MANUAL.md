---
title: "Timing of Exempted-Volume Reallocation in the Renewable Fuel Standard: Exact Reconstruction, Uncertainty and Predictability"
subtitle: "Project Technical Design Manual"
date: "Regulatory status verified November 23, 2026"
---

# 1. Project Specification

This manual is the complete technical specification for one computational research project. Its finished form is a reproducible research repository, a scientific preprint, and a formal regulatory comment. Section 1 specifies the project (A: identity and significance; B: methodology; C: data and references; D: codebase; E: experiments; F: validation and limitations; G: preprint; H: regulatory comment; I: final artifacts). Section 2 sets the scientific standards the work must meet. Section 3 defines the deliverable architecture.

**Conventions.** Every statement of regulatory status was verified from the Federal Register, Regulations.gov, agency web pages or docket documents on November 23, 2026, and must be re-verified on the day any comment is submitted. Sources marked **[verify]** were identified but not confirmed (DOI not resolved, document not read, or URL not tested); they must be confirmed before use, and may not be cited until they are. Facts drawn from secondary sources are labeled as such. Numbers quoted from Federal Register documents were read from text extractions and must be checked against the official PDF before they are quoted in a manuscript or comment. All scenario parameters not taken from a cited source are hypothetical and are labeled as such in code, figures and text.


## 1.A Project identity and research significance

**Manuscript title.** *Reallocating exempted obligations under the Renewable Fuel Standard: exact reconstruction of percentage standards, propagation of exemption uncertainty, and the predictability of alternative timing rules*

**Agency and docket.** U.S. Environmental Protection Agency, Office of Transportation and Air Quality. Docket EPA-HQ-OAR-2024-0505.

**Verified proceeding.** "Renewable Fuel Standard (RFS) Program: Reallocation of Additional 2025 Small Refinery Exemptions," proposed rule, 91 FR 65699–65711 (October 16, 2026), FR Doc. 2026-21155, RIN 2060-AX09, 40 CFR parts 80 and 1090. Regulations.gov document EPA-HQ-OAR-2024-0505-0951.

**Status (verified November 23, 2026).** Open. Comments due **December 4, 2026**. Virtual hearing held November 4, 2026. No final rule. Submission via Regulations.gov, docket EPA-HQ-OAR-2024-0505.

**Background.** The "Set 2" final rule (91 FR 16388, April 1, 2026, FR Doc. 2026-06275; effective June 15, 2026) set 2026–2027 volumes and reallocated 70% of 2023–2025 exempted obligations through a new SRE reallocation volume (SRERV) term in 40 CFR 80.1405, projecting the 2025 exempted obligation at 990 million RINs (7.55 billion gallons exempted fuel). On August 31, 2026, EPA decided 34 petitions for 2025 (18 full, 11 partial at 50%, 3 denied, 2 ineligible), giving an estimated 13.38 billion gallons and 1.76 billion RINs exempted, 0.77 billion RINs above the projection. These estimates derive from petition data; EPA intends to use reported 2025 compliance data in the final rule, so the 0.77 billion figure may change.

**The two co-proposed alternatives (Table IV-1 of the proposal; billion RINs).** Both reallocate **100%** of the additional 0.77 billion RINs; they differ only in timing.

| Category | Set 2 2026 | Set 2 2027 | Equal split 2026 | Equal split 2027 | All in 2027 2026 | All in 2027 2027 |
|---|---|---|---|---|---|---|
| Biomass-based diesel | 0.21 | 0.25 | 0.30 | 0.34 | 0.21 | 0.43 |
| Advanced biofuel | 0.28 | 0.34 | 0.40 | 0.47 | 0.28 | 0.59 |
| Total renewable fuel | 0.99 | 1.04 | 1.37 | 1.43 | 0.99 | 1.81 |

Resulting percentage standards (Table V-1, %): total renewable fuel 15.50/15.78 (Set 2), 15.71/16.01 (equal split), 15.50/16.23 (all in 2027); biomass-based diesel 5.24/5.37, 5.29/5.43, 5.24/5.48; advanced 6.42/6.61, 6.48/6.69, 6.42/6.76; cellulosic unchanged at 0.79/0.84 (no cellulosic SRERV). EPA's RIN cost estimates (Table VI-1): 27.5/28.0 ¢/gal (existing), 27.9/28.4 (equal split), 27.5/28.8 (all in 2027); gasoline and diesel price effects each below 1 ¢/gal. The proposal also extends the 2026 compliance deadline (currently March 31, 2027) by formula tied to finalization.

**Comment solicitations.** C-1, how to split the additional SRERV between 2026 and 2027; C-2, legal authority, including CAA §211(o)(2)(A)(i); C-3, reliance interests and other effects. All other inputs to the 2026–2027 standards are held constant; base volumes, cellulosic standards and the SRE decisions themselves are not reopened.

**Not to be confused with** the September 2025 supplemental proposal (90 FR 45007, closed October 31, 2025), which compared 100% versus 50% reallocation.

**Exact regulatory question.** Between the equal-split and all-in-2027 timing alternatives, which better achieves transparent, predictable and implementable standards given that the exempted volume is itself an estimate that will be revised, and what are the quantitative consequences of each for the standards and for compliance timing?

**Scientific problem.** Percentage standards are ratios of required volumes to projected non-exempt fuel. Reallocation of exempted volumes after the fact couples standards across years and makes them depend on uncertain exemption estimates and decision timing. The algebra is simple, but its error structure is not: how forecast errors in exemptions, fuel use and decision timing propagate to standards and to obligated parties' compliance positions under alternative timing rules has not, to the project's knowledge, been quantified systematically **[confirm by literature search]**.

**Central research question.** Given exact reconstruction of EPA's standards, how do the two timing alternatives (and a family of general timing rules) differ in the magnitude and variance of standard changes, in sensitivity to revision of the exempted volume, and in the compliance-timing burden implied by carryover-RIN limits, under historical patterns of exemption decisions?

**Original contribution.**

1. A fully reproducible reconstruction of the 2026–2027 percentage standards and of both alternatives from published inputs, with any discrepancy documented.
2. An uncertainty model for exempted volumes (petition-based estimate to reported data; decision timing) and for fuel-use projections, propagated to standards.
3. A general class of timing rules (share \(w\) in year \(y\), \(1-w\) in \(y+1\); prospective projection with true-up) evaluated for predictability using the historical record of SRE decisions and projections.
4. An accounting analysis of compliance timing under the carryover-RIN cap, without inferring market prices.

**Independent value.** The reconstruction and error analysis serve researchers and practitioners who need transparent RFS accounting; the timing-rule analysis applies to any obligation-reallocation mechanism (e.g., other renewable or clean fuel standards).

**Relationship to the decision.** EPA explicitly asks how to split the additional reallocation volume between years (C-1). Quantitative evidence on accuracy, revision sensitivity and compliance timing under each split responds directly. The project does not address legal authority (C-2) except to note where quantitative findings bear on reliance (C-3).

**Chain of relevance.** Question (how do timing rules differ in predictability and compliance burden?) → exact reconstruction + uncertainty propagation + historical evaluation + carryover accounting → quantified differences between alternatives → solicitation C-1 (and C-3 where relevant) → evidence-based recommendation on timing and on transparency of the update from petition-based to reported data.

## 1.B Mathematical and computational methodology

**B.1 Percentage standards.** For year \(i\) and category \(X\in\{\mathrm{CB},\mathrm{BBD},\mathrm{AB},\mathrm{RF}\}\), the structure of 40 CFR 80.1405(c) as amended by the Set 2 rule is
\[
\mathrm{Std}_{X,i}=100\times\frac{\mathrm{RFV}_{X,i}+\mathrm{SRERV}_{X,i}}{(G_i-RG_i)+(D_i-RD_i)-GE_i-DE_i},
\]
where \(G_i,D_i\) are projected gasoline and diesel, \(RG_i,RD_i\) renewable fuel contained in them, and \(GE_i,DE_i\) projected exempt volumes (the formula is published as an image in eCFR and must be transcribed exactly from the Set 2 final rule text, including any differences for cellulosic). Inputs \(G,D,RG,RD,GE,DE\) are taken from the docket memoranda "Calculation of 2026 and 2027 RFS Percentage Standards Without the SRE Reallocation Volumes" and "Calculation of Co-Proposed Revised 2026 and 2027 RFS Percentage Standards." A back-calculation check: \(100\times 26.81/15.50\approx 172.97\) billion gallons for the 2026 denominator implied by published values; reproduction must match published standards to the rounding precision EPA uses (two decimals).

**B.2 Exempted obligation.** The exempted obligation for compliance year \(y\) is \(\mathrm{ERVO}_{X,y}=\sum_{r} e_r\,\mathrm{Std}_{X,y}\,V_{r,y}/100\), with \(V_{r,y}\) the obligated volume of refinery \(r\) and \(e_r\in\{0,0.5,1\}\) the exemption share; the reallocation volume for year \(i\) is \(\mathrm{SRERV}_{X,i}=\sum_y \omega_{y\to i}\,\alpha_y\,\mathrm{ERVO}_{X,y}\) with reallocation share \(\alpha_y\) and timing weights \(\omega\). Category splits (BBD, advanced, total) follow EPA's stated method, reconstructed and tested against Table IV-1 (e.g., the implied split of the 0.77 billion RINs into BBD ≈ 0.18, other advanced ≈ 0.07, conventional ≈ 0.52).

**B.3 Uncertainty model.** (a) Revision of the exempted volume: the ratio of reported-data to petition-based exempted volumes is modeled with a distribution informed by any past cases where both are documented in EPA materials; if none, a documented range (e.g., ±20%) is used and labeled an assumption. (b) Fuel-use projection error: historical ratios of actual EIA consumption to the projections used in past RFS rules (assembled from rule documents and EIA data) give an empirical error distribution by forecast horizon. (c) Decision-timing uncertainty: the lag between compliance year and SRE decisions in the historical record. Monte Carlo propagation (\(10^5\) draws) gives distributions of realized versus published standards and of the eventual true-up.

**B.4 Timing-rule family and predictability metrics.** For a share \(w\) of additional reallocation assigned to year \(i\) and \(1-w\) to \(i+1\) (\(w=0.5\) equal split; \(w=0\) all in 2027), compute: (i) the change in each year's standard relative to Set 2; (ii) the variance of standards under B.3 uncertainty; (iii) the expected absolute revision if the exempted volume is updated before or after finalization; (iv) the share of the obligation imposed for a year after that year has ended (retroactivity measure, in RIN-years). A historical backtest applies each rule to the record of past exemption projections and decisions (from EPA's SRE data and past rules) and reports the realized forecast error of standards.

**B.5 Compliance-timing accounting.** Obligated parties may use carryover RINs up to 20% of an obligation (40 CFR 80.1427(a)(5); to be confirmed) and may carry deficits forward one year subject to conditions (80.1427(b)). Using EPA's published estimates of the carryover RIN bank (from the Set 2 rule and RIA), compute under each alternative the aggregate RINs that must be generated or drawn from the bank by each compliance deadline, the fraction of the additional obligation coverable by the bank within the 20% cap, and the effect of the proposed deadline extension. This is accounting only; no price or market-equilibrium inference is made beyond reproducing EPA's own cost estimates.

**B.6 Reproduction of EPA cost estimates.** Reproduce Table VI-1 (RIN cost per gallon) from EPA's stated method and RIN price assumptions, as a transparency check, without extending it.

## 1.C Data and scientific references

| Source | Identifier | Use | Limitations |
|---|---|---|---|
| Proposed rule | 91 FR 65699; FR Doc 2026-21155; https://www.govinfo.gov/content/pkg/FR-2026-10-16/pdf/2026-21155.pdf | Alternatives, tables, solicitations | — |
| Set 2 final rule | 91 FR 16388; FR Doc 2026-06275; https://www.govinfo.gov/content/pkg/FR-2026-04-01/html/2026-06275.htm | Formula, inputs, carryover bank estimate | Formula image must be transcribed |
| Docket memoranda (percentage standard calculations; fuel price impacts) | Regulations.gov EPA-HQ-OAR-2024-0505 (item numbers to be identified) | Exact inputs \(G,D,RG,RD,GE,DE\) | Must be downloaded |
| EPA Set 2 detailed fact sheet | https://www.epa.gov/system/files/documents/2026-03/set-2-detailed-fact-sheet.pdf | Volumes RFV and SRERV | — |
| eCFR 40 CFR 80.1405, 80.1427 | https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-80/subpart-M/section-80.1405 | Standards table; carryover provisions | — |
| EPA SRE data and decision pages | https://www.epa.gov/fuels-registration-reporting-and-compliance-help/rfs-small-refinery-exemptions ; https://www.epa.gov/renewable-fuel-standard/august-31-2026-decisions-petitions-rfs-small-refinery-exemptions ; decision document EPA-420-R-26-017 | Historical petitions, decisions, exempted volumes | Aggregated |
| September 2025 supplemental proposal | 90 FR 45007 | Historical projections of exempt volumes (2023–2025) | Superseded figures, used only for backtest |
| EPA EMTS RIN data | EPA RIN data pages **[verify URL]** | RIN generation by D-code | — |
| EIA consumption data and STEO/AEO | https://www.eia.gov **[verify specific series]** | Projection error analysis | — |

**References.** Knittel, C. R., Meiselman, B. S., & Stock, J. H. (2017). The pass-through of RIN prices to wholesale and retail fuels under the Renewable Fuel Standard. *Journal of the Association of Environmental and Resource Economists*, 4(4) **[verify DOI 10.1086/692071]** (cited only for context; no price inference is made). Lade, G. E., Lin Lawell, C.-Y. C., & Smith, A. (2018). Policy shocks and market-based regulations: Evidence from the Renewable Fuel Standard. *American Journal of Agricultural Economics*, 100, 707–731 **[verify DOI]**. Congressional Research Service, R43325 (RFS overview) and R46244 (SRE FAQs) **[verify current versions]**. Hubbs, T., & Irwin, S. (2026). farmdoc daily 16:204 (November 11, 2026), https://farmdocdaily.illinois.edu/wp-content/uploads/2026/11/fdd111126.pdf (secondary analysis used as an independent cross-check only).

## 1.D Research codebase specification

Repository `rfs-sre-reallocation`, package `rfsrealloc`.

| Module | Function |
|---|---|
| `rfsrealloc.inputs` | Transcribed inputs with page/table citations (double-entered) |
| `rfsrealloc.standards` | Exact percentage-standard computation with EPA rounding conventions |
| `rfsrealloc.reallocation` | ERVO and SRERV computation; category splits; timing rules |
| `rfsrealloc.uncertainty` | Exemption revision, fuel-projection error, decision-timing models; Monte Carlo |
| `rfsrealloc.backtest` | Historical evaluation of timing rules |
| `rfsrealloc.carryover` | Compliance-timing accounting under carryover caps and deficit rules |
| `rfsrealloc.costs` | Reproduction of EPA's RIN cost table |

Libraries: pandas, NumPy, SciPy, matplotlib, pydantic, pytest, hypothesis. Exact rational arithmetic (Python `fractions`) is used in tests to separate rounding from formula errors.

Tests: reproduce Set 2 standards (Table 1 of 80.1405) and both alternatives (Tables IV-1 and V-1) to published precision; SRERV category splits match Table IV-1; carryover accounting conserves RINs; double-entered inputs agree.

Network hosts required: www.govinfo.gov, www.federalregister.gov, www.regulations.gov / downloads.regulations.gov, www.epa.gov, www.ecfr.gov, www.eia.gov.

## 1.E Computational experiments

| # | Varied | Output | Purpose | Criteria |
|---|---|---|---|---|
| E1 | — | Reconstructed standards and SRERVs | Verify reproduction | Exact match at published precision |
| E2 | Exempted volume revision | Standards under each alternative | Revision sensitivity | ∂Std/∂ERVO by alternative; distributions |
| E3 | Fuel-projection error | Realized vs published standards | Forecast error | Error distributions |
| E4 | Timing share w ∈ [0,1] | Variance, retroactivity measure, revision exposure | General timing-rule trade-offs | Trade-off curves |
| E5 | Historical backtest | Realized forecast errors by rule | Empirical predictability | Mean absolute error by rule |
| E6 | Carryover bank and cap | Bank coverage; deadline effects | Compliance timing | Accounting tables |
| E7 | — | RIN cost table | Transparency check | Match to EPA Table VI-1 |

**Competing outcomes.** The all-in-2027 option may reduce retroactive obligation and revision exposure at the cost of a larger single-year step; the equal split may smooth standards but impose obligations for a completed year; differences may be small relative to fuel-projection uncertainty, in which case the comment would emphasize transparency of the data update rather than timing. The analysis determines which.

## 1.F Validation and limitations

1. *Numerical correctness*: exact reproduction (E1, E7).
2. *Model verification*: independent cross-check against secondary analyses (farmdoc) for derived quantities.
3. *Empirical validity*: the backtest uses the historical record; uncertainty distributions for exemption revisions may rest on limited data and are flagged.
4. *Regulatory applicability*: findings address C-1 (and C-3 where quantitative); no legal or price conclusions.

## 1.G Scientific preprint

**Title.** *Reallocating exempted obligations under the Renewable Fuel Standard: exact reconstruction, uncertainty propagation and the predictability of alternative timing rules.*

**Target venues.** *Energy Policy*; *Applied Economic Perspectives and Policy* (as a methods/data note); preprint on SSRN or arXiv (econ.GN).

**Structure.** Abstract; 1 Introduction (RFS standards, SREs, reallocation history); 2 Methods (formula and inputs; ERVO and SRERV; uncertainty; timing-rule family; backtest; carryover accounting); 3 Results (reproduction; revision sensitivity; forecast error; timing trade-offs; backtest; compliance timing); 4 Discussion; 5 Limitations; 6 Conclusions. *Figures*: (1) flow of volumes from exemptions to standards; (2) reproduction residuals; (3) standards under alternatives with uncertainty bands; (4) timing-rule trade-off curves; (5) backtest errors; (6) carryover coverage. *Tables*: inputs with sources; reconstructed tables; uncertainty parameters; accounting results. *SI*: full transcription, code-to-equation map.

## 1.H Formal regulatory comment

**Proceeding and route.** Docket EPA-HQ-OAR-2024-0505 via Regulations.gov by December 4, 2026, responding to solicitation C-1 (and C-3 as warranted).

**Findings that could support recommendations (determined by results).** Quantified differences between the alternatives in retroactive obligation, revision exposure and single-year step size (E2, E4); the share of each standard's uncertainty attributable to the exemption estimate versus fuel projections (E2–E3); compliance-timing effects under carryover limits (E6); and, regardless of timing preference, a transparency recommendation that the final rule publish the reported-data exemption figures and full calculation inputs in machine-readable form, if E1 shows reproduction required non-public or non-obvious steps.

**Structure.** Identification; summary; the C-1 question; reconstruction and verification; findings with Figures 3–6; recommendation; limitations; references; technical attachment with reproduced tables.

## 1.I Final artifacts

Repository `rfs-sre-reallocation`; transcribed input dataset with citations; reconstruction and uncertainty outputs; six figures, four tables; manuscript (LaTeX, PDF, DOCX) and SI; comment (DOCX, PDF) and technical attachment.

# 2. Scientific Standards

The standards in this section apply to every part of this project. Where Section 1 is more specific, Section 1 governs.

## 2.1 Computational reproducibility

1. **Single-command reproduction.** Every repository exposes one entry point (`make all`, or `python -m rfsrealloc.pipeline run --config configs/paper.yaml`) that regenerates every number, table and figure in the manuscript and the comment attachments from raw inputs. A second target (`make quick`) runs a reduced configuration (fewer Monte Carlo replicates, coarser grids) for continuous integration and must finish on a laptop.
2. **Pinned environments.** Python ≥ 3.11. Dependencies are declared in `pyproject.toml` and locked (`uv.lock` or `conda-lock.yml`). A `Dockerfile` or `environment.yml` reproduces the environment. Solvers external to Python (HiGHS, AERMOD, AERMET) are pinned by version and checksum, and the build fetches them by script.
3. **Seeded randomness.** All stochastic code takes an explicit `numpy.random.Generator`. Seeds are stored in the configuration file and written into every output's metadata. Parallel Monte Carlo uses `SeedSequence.spawn` so results do not depend on worker count.
4. **Configuration as data.** Every experiment is a YAML file under `configs/` validated by a schema (pydantic). No parameter that appears in the manuscript may be hard-coded in a module.
5. **Output provenance.** Each output file (Parquet, NetCDF, CSV, PNG/PDF) carries or is accompanied by a JSON sidecar recording the git commit, configuration hash, input-data checksums, package versions and seed.
6. **Deterministic figures.** Figures are produced only by scripts in `figures/` reading saved results, never by notebooks with hidden state. Fonts and styles are fixed in a shared `matplotlibrc`.

## 2.2 Numerical validation

Each project separates four levels of evidence, and each manuscript reports them separately:

| Level | Question | Typical evidence |
|---|---|---|
| Numerical correctness | Does the code compute what the equations say? | Unit tests, analytical solutions, conservation and identity checks, convergence under refinement, solver optimality certificates |
| Model verification | Do the equations represent the intended conceptual model? | Comparison with independent implementations or published benchmark cases; limiting-case behavior; dimensional analysis |
| Empirical validity | Does the model reproduce observations of the real system? | Out-of-sample comparison with measured data where any exist; otherwise explicitly stated as not established |
| Regulatory applicability | Does the result bear on the decision the agency is actually making? | Mapping from result to a specific provision, question or criterion in the docket |

Minimum requirements for all projects:

- Monte Carlo estimators report standard errors and the replicate count is chosen so that the Monte Carlo standard error of every reported headline quantity is below 2% of its value (or a stated absolute tolerance), demonstrated by a convergence plot in the supporting information.
- Discretized solvers report a grid- or time-step-refinement study with the observed order of convergence.
- Optimization models report solver status, optimality gap (MILP gap ≤ 0.1% unless stated) and verify primal feasibility of the returned solution with an independent check.
- Units are carried with `pint` in input parsing and checked by dimensional tests at module boundaries; core numerical kernels may operate on plain arrays in SI units.
- Property-based tests (`hypothesis`) cover invariants (non-negativity, monotonicity in a parameter where theory requires it, conservation).

## 2.3 Source reliability and hierarchy

Sources are ranked and the rank is recorded in the bibliography database:

1. Statute, regulation (eCFR), and Federal Register documents; docket documents (technical support documents, supporting statements, memoranda to the docket).
2. Agency datasets with documented methodology (EPA AQS, EIA-930, PHMSA incident data, EMTS, AP-42, USGS).
3. Peer-reviewed literature and recognized technical standards (NFPA, IEC, API, ASTM).
4. National-laboratory and government technical reports (NREL, LBNL, Sandia, GAO, OIG, CRS).
5. Grey literature from trade associations, advocacy organizations and consultancies, used only to locate primary sources or to represent stakeholder positions, never as the sole basis of a quantitative parameter.

A parameter taken from rank-5 material must be flagged in the parameter table and included in the sensitivity analysis.

## 2.4 Data provenance

- Raw downloaded files are stored unmodified under `data/raw/` (or fetched on demand by `scripts/fetch_data.py` when licensing or size forbids redistribution), with a `data/MANIFEST.yaml` recording source organization, URL, retrieval date, SHA-256 checksum, license or terms of use, and the exact query parameters used.
- All transformations from raw to analysis-ready data are code in `src/rfsrealloc/data/` and are idempotent. No manual spreadsheet edits.
- Synthetic data are generated only by code, stored under `data/synthetic/`, and every synthetic file name and metadata record carries the word `synthetic`. Figures based on synthetic data say so in the caption.
- Values digitized or transcribed from documents (tables in a Federal Register notice, a technical support document, a figure in a paper) are stored in `data/transcribed/` with a citation to page and table, and are double-entered and reconciled by a test that compares the two entries.

## 2.5 Citation accuracy

- Every reference is held in a single BibTeX file per repository. Every DOI is resolved through doi.org and the resolved metadata (title, authors, year, venue) is checked against the entry by a script (`scripts/check_refs.py`) that queries Crossref; mismatches fail the build.
- Federal Register documents are cited by volume, page, date and FR document number; regulations by CFR section and the eCFR "current as of" date; docket documents by their Regulations.gov document ID or FERC eLibrary accession number.
- A reference is cited only for a claim it actually supports. Statements in this manual marked **[verify]** identify sources that must be located and checked before use; they may not be cited until verified.
- No preprint DOI, journal acceptance or review status is stated unless it exists.

## 2.6 Statistical rigor

- Uncertainty is propagated, not appended: reported quantities are accompanied by intervals derived from the uncertainty model (parametric distributions, bootstrap, or posterior), with the interval type stated.
- Global sensitivity analysis uses variance-based Sobol indices (Saltelli estimator with Jansen formulas, implemented with `SALib`) when inputs are independent and the model is cheap enough for N(k+2) evaluations with N ≥ 2¹²; otherwise Morris elementary effects for screening followed by Sobol indices on the retained factors. Bootstrap confidence intervals on indices are reported.
- Hypothesis tests are pre-specified in the configuration, with multiplicity controlled (Holm or Benjamini–Hochberg as stated) when more than one comparison supports a single claim.
- Rare-event probabilities below 10⁻³ are estimated with variance reduction (importance sampling or subset simulation) or analytically, never by naive Monte Carlo with too few events. The number of observed events behind each estimate is reported.
- Distributions fitted to data report goodness of fit (Anderson–Darling or a likelihood-based comparison) and the effect of the distributional choice on headline results is tested.

## 2.7 Professional manuscript preparation

- Manuscripts are written in LaTeX (`revtex4-2` or `elsarticle` class, per the intended venue) with a single notation table per paper, SI units, and equations numbered. Every number in the text is generated by the pipeline into `paper/generated/values.tex` as LaTeX macros, so prose and results cannot drift apart. A test fails if any macro is undefined or stale.
- Figures are vector PDF with embedded fonts, colorblind-safe palettes (Okabe–Ito or viridis family), labeled axes with units, and captions that state the data basis (observed, modeled, synthetic, hypothetical scenario).
- Editable output: the LaTeX source plus a DOCX produced with `pandoc` from the same source. PDF output: compiled with `latexmk`.
- Author contributions, funding and competing-interest statements follow venue conventions. Acknowledgments name only people and organizations that contributed.
- Target venues are suggested in each project specification; the manuscript must also stand alone as a preprint (arXiv physics.soc-ph, stat.AP, eess.SY, or EarthArXiv / ESS Open Archive, as appropriate).

## 2.8 Regulatory relevance

Each comment satisfies these tests before it is finalized:

1. **Proceeding test.** The comment is addressed to the exact document and docket identified in the project specification and was confirmed open on the date of submission from the Federal Register or the agency docket. If the period has closed, the comment is not filed as if timely; the specification states the alternative (later stage of the same proceeding, or no filing).
2. **Scope test.** Each recommendation names the provision, question, criterion or decision in the docket it addresses and the agency authority under which it could be acted on in that proceeding.
3. **Evidence test.** Each recommendation is traced to a specific figure or table in the attachment and to the validation level (Section 2.2) that supports it. Recommendations resting only on hypothetical scenarios are phrased as requests for analysis, disclosure or clarification, not as findings about real facilities.
4. **Restraint test.** No claim of harm, violation, or benefit at a real facility is made without facility-specific evidence. Adverse or null results that bear on the question are reported.

Comments follow a common structure: (i) identification of commenter and docket; (ii) summary of recommendations (one page); (iii) the specific issue in the proposal; (iv) analysis and findings, with figures; (v) recommendations, each tied to a provision; (vi) limitations; (vii) references; (viii) technical attachment (a condensed version of the preprint and the repository archive identifier, if public). Comments are submitted as PDF with an editable DOCX retained.

## 2.9 Scientific integrity

- Conclusions are determined by validated results. Each project specification lists competing hypotheses and the observations that would distinguish them; the manuscript reports which outcome occurred, including null or unfavorable results.
- No empirical data, measurements, validation results, citations, or publication metadata are fabricated. A model that cannot be validated against observations is described as a verified model of stated assumptions, not as a prediction.
- Hypothetical scenarios are labeled as such everywhere they appear: configuration names (`scenario_hypothetical_*`), figure captions, table headers, and text.
- Any facility, site, or company is analyzed only from public documents, and inferences about it are stated with the evidence they rest on.

## 2.10 Research repository organization

The repository `rfs-sre-reallocation` uses this skeleton:

```
rfs-sre-reallocation/
├── README.md               # purpose, installation, reproduction, citation
├── LICENSE                 # BSD-3-Clause for code; CC BY 4.0 for text, figures, derived data
├── CITATION.cff
├── pyproject.toml
├── uv.lock                 # or conda-lock.yml
├── Dockerfile
├── Makefile
├── configs/                # experiment configurations (YAML), schema-validated
├── data/
│   ├── MANIFEST.yaml       # provenance of every input
│   ├── raw/                # unmodified downloads (or fetched by script)
│   ├── transcribed/        # values transcribed from documents, double-entered
│   ├── synthetic/          # generated synthetic inputs
│   └── processed/          # analysis-ready derived data
├── src/rfsrealloc/          # importable library
├── scripts/                # fetch_data.py, check_refs.py, run_experiments.py
├── figures/                # one script per manuscript figure
├── notebooks/              # exploratory analysis with scientific content only
├── tests/                  # unit, property, validation and regression tests
├── results/                # generated outputs (git-ignored except small summaries)
├── docs/
│   ├── model.md            # mathematical specification of the model
│   ├── data.md             # data sources, variables, limitations
│   └── reproduction.md     # step-by-step reproduction and expected runtimes
├── paper/                  # LaTeX manuscript, SI, bibliography, generated values
└── comment/                # regulatory comment source, attachments, final PDF
```

Files that do not serve a scientific, computational, documentation, publication or regulatory function are not created. In particular, repositories contain no development logs, progress records, session notes, change narratives beyond conventional `git` history and a `CHANGELOG.md` limited to released versions, task lists, or files describing how the repository was produced.

Continuous integration (GitHub Actions) runs linting (`ruff`), type checking (`mypy --strict` on `src/`), the test suite, `make quick`, and the reference checker on every push.

# 3. Deliverable Architecture

## 3.1 Repository

The project is implemented as one self-contained repository, `rfs-sre-reallocation`, with importable Python package `rfsrealloc`, organized as in Section 2.10 and with the modules listed in Section 1.D. It has no code dependency on any other repository and can be archived, cited and reproduced alone.

## 3.2 Publication package

Each project produces, inside its repository:

- `paper/manuscript.tex`, `paper/manuscript.pdf`, `paper/manuscript.docx` — the preprint.
- `paper/si.tex`, `paper/si.pdf` — supporting information (extended methods, verification results, convergence studies, full parameter tables, additional figures).
- `paper/figures/` — final vector figures as used in the manuscript.
- `comment/comment.docx`, `comment/comment.pdf` — the formal regulatory comment.
- `comment/attachment_technical.pdf` — the technical attachment (condensed methods, results and figures, written for agency technical staff).
- A tagged release (`v1.0.0`) archived to Zenodo when made public, producing a DOI that is then (and only then) cited in the comment and manuscript.
