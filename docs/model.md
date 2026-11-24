# Mathematical specification

Notation follows 40 CFR 80.1405 (as amended by the Set 2 rule, 91 FR 16487–16488) and
the project manual. Volumes are in billion gallons, RIN quantities in billion
gallon-RINs unless stated, and standards in percent.

## 1. Percentage standards

For compliance year $i$ and category $X \in \{\mathrm{CB},\mathrm{BBD},\mathrm{AB},\mathrm{RF}\}$,
paragraph (c) of 40 CFR 80.1405 (2026 and 2027 only) reads

$$
\mathrm{Std}_{X,i} = 100 \times \frac{\mathrm{RFV}_{X,i} + \mathrm{SRERV}_{X,i}}
{(G_i - RG_i) - GE_i + (D_i - RD_i) - DE_i},
\qquad \mathrm{SRERV}_{\mathrm{CB},i} = 0 .
$$

Paragraph (b) (other years) omits SRERV. The equations were transcribed from the image
on 91 FR 16488 (the eCFR renders them as an image). `rfsrealloc.standards` evaluates them
in exact rational arithmetic; published values are rounded half-up to two decimals.
The denominator is the *obligated volume* $V_i$.

Sensitivities: $\partial \mathrm{Std}/\partial \mathrm{SRERV} = 100/V_i$ (percentage points
per billion RINs) and $\partial \mathrm{Std}/\partial V = -100\,(\mathrm{RFV}+\mathrm{SRERV})/V_i^2$.

## 2. Exempted obligations and reallocation volumes

For a compliance year $y$ with exempted fuel volume $F_y$ (gasoline plus diesel) the
exempted RVO is $\mathrm{ERVO}_{X,y} = \mathrm{Std}_{X,y} F_y / 100$, printed to
10 million RINs in Table IV.C-2 (91 FR 16439); nearest rounding reproduces 11 of the 12
printed cells. The Set 2 rule reallocates a share
$\alpha = 0.7$ with timing weights $\omega_{2023\to2026}=1$, $\omega_{2024\to2026}=\omega_{2024\to2027}=1/2$,
$\omega_{2025\to2027}=1$ and rounds the 2026 volume *down* and the 2027 volume *up* to
10 million RINs. The proposal's note to Table IV-1 (91 FR 65706) says that volumes
ending in five were rounded down for 2026 and up for 2027; applied to the printed
obligations that rule reproduces three of the six Set 2 volumes, whereas the
floor/ceiling convention reproduces all six (see `tests/test_reproduction.py`).

The additional 2025 exempted RVO is $A_X = \mathrm{round}_{10}(\mathrm{Std}_{X,2025} F^{\mathrm{act}}_{2025}/100) - \mathrm{ERVO}^{\mathrm{proj}}_{X,2025}$
with $F^{\mathrm{act}}_{2025} = 13.38$ billion gallons, giving 180, 250 and 770 million RINs
for BBD, advanced and total renewable fuel.

### Timing-rule family

For a share $w \in [0,1]$ assigned to 2026 and $1-w$ to 2027,
$\mathrm{SRERV}_{X,2026}(w) = \mathrm{SRERV}^{\mathrm{Set2}}_{X,2026} + wA_X$ and
$\mathrm{SRERV}_{X,2027}(w) = \mathrm{SRERV}^{\mathrm{Set2}}_{X,2027} + (1-w)A_X$, with EPA's
rounding convention when published values are required. $w = 1/2$ is the equal
reallocation approach and $w = 0$ the 2027 reallocation approach.

Metrics as functions of $w$:

* step size: $\mathrm{Std}_{X,i}(w) - \mathrm{Std}^{\mathrm{Set2}}_{X,i}$;
* revision exposure: $\mathbb{E}\,|\mathrm{Std}_{X,i}(w; r) - \mathrm{Std}_{X,i}(w; 1)|$ where
  $r$ is the ratio of the reported to the petition-based exempted RVO;
* variance of the standard under the uncertainty model;
* retroactivity: $R(w, t) = w f_{2026}(t) + (1-w) f_{2027}(t)$ where $f_i(t)$ is the fraction
  of compliance year $i$ elapsed at the final rule's effective date $t$ (RIN-years per
  RIN reallocated).

## 3. Uncertainty model

* **Exemption revision** $r$: smoothed bootstrap of the empirical log ratios
  $\log(\mathrm{reported}/\mathrm{petition\mbox{-}based})$ for compliance years with both figures
  (EPA decision documents and dashboard Table SRE-1). The additional volume becomes
  $A_X(r) = r\,\mathrm{ERVO}^{\mathrm{act}}_{X,2025} - \mathrm{ERVO}^{\mathrm{proj}}_{X,2025}$.
  A uniform $\pm 20\%$ alternative is available as a labelled assumption.
* **Fuel-use error** $e_i$: smoothed bootstrap of $\log(\text{reported}/\text{projected})$
  non-renewable gasoline-plus-diesel volume for past rules in place by the middle of the
  compliance year and not later revised (dashboard RVO
  Table 1), binned by lead time; the 2026 and 2027 draws share a configurable rank
  correlation. Realized RINs implied by a standard are $\mathrm{Std}\,V_i e^{e_i}/100$.
* **Decision timing**: per-petition lags between the end of the compliance year and the
  decision date (dashboard Table SRE-3) and the dates of EPA decision actions.

Monte Carlo draws use `numpy.random.SeedSequence.spawn` so the sample does not depend on
the number of workers. Variance-based sensitivity uses Saltelli sampling with Jansen
estimators (SALib) on the three independent factors with bootstrap intervals.

## 4. Historical backtest

For each compliance year the three-year-average projection of the exempted RVO is
compared with the realized value, in hindsight and using only decisions issued before
the rule for that year. For the timing-rule family, the share of the reallocated amount
that was still undecided when the receiving year's standard was set measures the
forecast error attributable to the rule; a lead-time policy of $L$ months only
reallocates amounts decided at least $L$ months before the standard is set.

## 5. Carryover accounting

With $b_{t-1}$ the vintage-$(t-1)$ RINs carried into year $t$, obligation $O_t$, generation
$g_t$ and cap $c = 0.2$ (40 CFR 80.1427(a)(5)):
$u_t = \min(b_{t-1}, cO_t)$, new RINs required $n_t = O_t - u_t$, $b_t = \max(0, g_t - n_t)$,
expired $x_t = b_{t-1} - u_t$, deficit $d_t = \max(0, n_t - g_t)$, with the identity
$b_{t-1} + g_t = O_t - d_t + b_t + x_t$ checked for every year. Generation is assumed equal
to the volume requirement; the bank entering 2026 is EPA's effective 2024 carryover plus
the 0.77 billion RINs freed by the 2025 exemptions; alternative bank sizes are labelled
hypothetical scenarios. Compliance deadlines follow 40 CFR 80.1451(f)(1)(i)(C) and the
quarterly deadlines of 80.1451(f)(2).

## 6. RIN cost reproduction

Total RIN cost per gallon of obligated fuel is $\sum_X s_X p_X$ over cellulosic (D3),
biomass-based diesel (D4), other advanced (D5) and conventional (D6) shares of the
standards with the RIN prices of docket memorandum EPA-HQ-OAR-2024-0505-0961; the
impact of an alternative relative to the existing standards is the difference of total
RIN cost. No price inference is made.
