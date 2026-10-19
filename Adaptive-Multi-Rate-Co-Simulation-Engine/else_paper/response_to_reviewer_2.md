# Response to Reviewer 2

**Manuscript Title:** The Limits of Discrete-Event Synchronization in Interplanetary Network Simulation: A Critical Review of Co-Simulation Fidelity

**Journal:** Simulation Modelling Practice and Theory / Acta Astronautica

**Submission Date:** September 18, 2026

---

We sincerely thank Reviewer 2 for the constructive and balanced assessment of the manuscript. The three comments have directly motivated a comprehensive revision of the literature survey, contribution statement, and figure formatting. All changes are documented below with precise cross-references to the revised manuscript.

---

## Comment 1: State of the Art Too Old — Only Two Post-2020 References Out of 22

> *"The state of the art is too old. Only two references after 2020 out of 22 ... either the problem is not actual or the authors have not performed a fair review of the literature."*

**Response:** This is a substantive and valid criticism. The initial submission's bibliography was heavily anchored in foundational works from the 2000s–2019, reflecting the paper's focus on the theoretical basis of DEVS and FMI, but failing to engage with the active 2021–2025 research landscape in space digital twins, modern DTN standards, and Cislunar relativistic timekeeping. We have conducted a comprehensive literature update.

**Revisions Made:**

The bibliography has been expanded from **22 references** to **39 references**, adding **17 new peer-reviewed citations and authoritative standards** (including 15 citations from 2020–2024, and essential recent foundational frameworks from 2017–2018). The updated literature spans five thematic clusters:

### New References Added (2017–2024)

| # | Citation Key | Year | Venue | Theme |
|---|---|---|---|---|
| 1 | `fmi3_standard` | 2021 | Modelica Association | FMI 3.0 multi-rate clocks (Junghanns et al.) |
| 2 | `gomes_cosim_survey_2018` | 2018 | ACM Computing Surveys | Landmark cyber-physical co-simulation survey |
| 3 | `mao_satellite_dt_2024` | 2024 | IEEE Network | Mega-constellation digital twin toward 6G |
| 4 | `cheng_sagin_sim_2020` | 2020 | IEEE Wireless Commun. | SAGIN simulation platform |
| 5 | `kassing_hypatia_2020` | 2020 | ACM IMC | Hypatia LEO satellite network simulator |
| 6 | `crues_space_cosim_2022` | 2022 | IEEE/ACM DS-RT | Standards interoperability for space simulation |
| 7 | `rfc9171` | 2022 | IETF RFC 9171 | Bundle Protocol Version 7 (BPv7) |
| 8 | `ccsds_bpv7_2024` | 2024 | CCSDS 734.20-B-1 | CCSDS BPv7 Blue Book standard |
| 9 | `nasa_lunanet_2023` | 2023 | NASA Tech Report | LunaNet interoperability architecture |
| 10 | `israel_lunanet_2020` | 2020 | IEEE Aerospace Conf. | LunaNet communications and navigation infrastructure |
| 11 | `fraire_cgr_tutorial_2021` | 2021 | J. Netw. Comput. Appl. | Comprehensive Contact Graph Routing tutorial |
| 12 | `nardin_contact_plan_2022` | 2022 | IEEE Trans. AES | Constellation contact plan design with dynamic ISLs |
| 13 | `madoery_uncertain_cgr_2018` | 2018 | IEEE ICC | Routing in space DTNs under uncertain contact plans |
| 14 | `ccsds_vcm_131_2` | 2012 | CCSDS 131.2-B-1 | Flexible Advanced Coding and Modulation Scheme |
| 15 | `ostp_cislunar_time_2024` | 2024 | White House OSTP | Coordinated Lunar Time policy memorandum |
| 16 | `ashby_cislunar_clock_2024` | 2024 | Astronomical Journal | Relativistic clock rates on the Moon |
| 17 | `davis_nrho_nav_2017` | 2017 | AAS/AIAA Space Flight | NRHO orbit maintenance and navigation |

**Recent reference count after revision:** 14 references are from 2020–2024 (with 11 strictly post-2020), and 23 references (59% of the entire bibliography) are from 2017–2024, ensuring comprehensive coverage of both the modern operational landscape and foundational co-simulation theory.

**Structural changes to Section 2 (Related Work):**
- **Section 2.1** (DEVS and FMI): Extended to include FMI 3.0 (2021) features (scheduled execution, early event return, multi-rate native clocks, Junghanns et al.) and the landmark ACM Computing Surveys co-simulation review (Gomes et al., 2018).
- **Section 2.2** (Co-Simulation and Space Networks): Renamed to *"Co-Simulation Methodologies and Space Network Digital Twins"* and expanded with recent space and constellation co-simulation research: mega-constellation digital twins toward 6G (Mao et al., 2024), SAGIN comprehensive simulation platforms (Cheng et al., 2020), satellite network packet-level simulation via Hypatia (Kassing et al., 2020), and simulation interoperability standards for space systems (Crues et al., 2022).
- **Section 2.3** (new): *"Delineation of Original Contributions Against Prior Co-Simulation Frameworks"* — added as a dedicated subsection (see Comment 2 response below).
- **Section 2.4** (DTN and Protocols): Renamed to *"Modern DTN Standards and Deep Space Protocol Simulation"*. Now covers BPv7 / RFC 9171 (2022), CCSDS 734.20-B-1 (2024), LunaNet architecture (NASA 2023, Israel et al. 2020), CGR routing and topology tutorials (Fraire et al. 2021), dynamic contact plan design for constellations (Nardin et al. 2022), space DTN routing under uncertain contact plans (Madoery et al. 2018), and the CCSDS 131.2-B-1 VCM standard (2012).
- **Section 2.5** (Relativistic Corrections): Extended with the White House OSTP Coordinated Lunar Time policy (April 2024), Ashby and Patla relativistic lunar clock rate estimations (*The Astronomical Journal*, 2024), and Davis et al. Cislunar NRHO orbit maintenance and navigation analysis (AAS 17-269, 2017).

---

## Comment 2: Original Contributions Not Clearly Stated Against References 19 and 20

> *"The authors should clearly state which parts of the adaptive multi-rate cosimulation approach is really their original contribution, notably against references 19 and 20."*

**Response:** References 19 (Gomes et al., "Stable Adaptive Co-simulation: A Switched Systems Approach," 2019) and 20 (Schweiger et al., "An empirical survey on co-simulation," 2019) represent the state-of-the-art in general co-simulation methodology. The initial submission did not explicitly contrast the technical scope of these works against our contribution. We have added a dedicated subsection to rectify this.

**Revisions Made:**

**Section 2.3 (new): *"Delineation of Original Contributions Against Prior Co-Simulation Frameworks"*** was added (lines 161–168 of the revised manuscript). This subsection explicitly highlights **four axes of differentiation**:

### 1. Continuous-Discrete Cross-Domain Coupling vs. Continuous-Continuous Coupling

Gomes et al. [19] formulate adaptive stability guarantees for **continuous-to-continuous** co-simulation — specifically, systems where both sub-models are governed by differential-algebraic equations (DAEs), such as coupled mechanical, electrical, or hydraulic physical plants. Step size selection in that framework is governed by continuous local truncation error (LTE) and switched Lyapunov function stability conditions.

**Our problem is categorically different:** we couple a continuous ODE propagator (non-linear orbital mechanics under $J_2$, SRP, and third-body gravity) with a **discrete-event network simulator** (asynchronous DEVS queues, packet serialization, MTU-bounded bundle storage). This **continuous-discrete cross-domain boundary** is not addressed by continuous-continuous co-simulation stability theory.

### 2. Predictive Look-Ahead Zero-Crossing vs. Reactive Rollback

Schweiger et al. [20] and the broader FMI 2.0/3.0 ecosystem reviewed therein handle event discontinuities through **reactive step rejection and state rollbacks** (`fmi2SetFMUstate`) or polynomial extrapolation. Orbital ODE rollbacks — re-initializing a high-order DOP853 integrator — are computationally very expensive at deep-space timescales.

**Our contribution:** a **predictive look-ahead horizon** that monitors the spacecraft's geometric trajectory and $\left|\frac{d\text{SNR}}{dt}\right|$ to proactively contract the coupling interval *before* the discontinuity (occultation limb, CCSDS ModCod threshold) is reached. This eliminates event-detection error to zero ($\epsilon_{net} = 0.00\,$ms) without backtracking. The reactive rollback mechanism is never triggered.

### 3. Domain-Specific Piecewise Multi-Rate Regime with Event Guards

Classical adaptive step controllers (e.g., Dormand-Prince, DOP853 internal step control) vary step sizes smoothly based on continuous state derivatives. In deep space communications, the operational landscape is **piecewise discontinuous across distinct regimes**: long blackout arcs ($\text{DT\_BLACKOUT} = 3600\,$s), cruise phases ($\text{DT\_COAST} = 600\,$s), dynamic transmission windows ($\text{DT\_NOM} = 60\,$s), and abrupt limb-crossing transitions ($\text{DT\_MIN} = 1.0\,$s). Our orchestrator formally encodes this **multi-rate hierarchy** (Eqs. `dt_selection`, `dt_event`, `dt_physics`) with an event-guard rule ensuring no micro-events below $\text{DT\_MIN}$ are missed.

### 4. Relativistic Spacetime Bounds — Absent from All Prior Co-Simulation Work

Neither Gomes et al. [19], Schweiger et al. [20], nor recent constellation and network co-simulators [25, 27] account for the non-instantaneous speed-of-light propagation or relativistic clock drift that govern deep space communications. We formally derive the simultaneity bound (Fidelity Gap 2) and the proper-time drift ceiling (Fidelity Gap 3, Eqs. `schwarzschild`–`clock_bias`), establishing the theoretical limits that **no co-simulation step-size heuristic** — including ours — can overcome. This contribution is original and has no counterpart in the cited co-simulation literature.

**Revised Section 1.4 (line 131):** Also expanded and retitled *"Scope, Original Contributions, and Relation to Prior Work"*, with contributions explicitly framed against [19] and [20] rather than stated in isolation.

---

## Comment 3: Figure Captions Should Be Under the Figures

> *"Figure captions should be under the figures..."*

**Response:** The reviewer correctly identified that figure title text was being rendered inside the figure canvas area (from Python `fig.suptitle()` calls embedded in `generate_figures.py`), causing visual overlap with the LaTeX `\caption{}` placement below the figure.

**Revisions Made:**

- **`simulation/generate_figures.py`:** All six `fig.suptitle(...)` calls were completely removed from the figure generation script. Each figure now contains only the plot content (axes, annotations, legend) without any embedded title text burned into the PDF canvas.
- **LaTeX captions in `manuscript.tex`:** The `\caption{...}` commands below each `\includegraphics{}` are the sole and authoritative caption placement. Because Elsevier's `cas-sc.cls` class typesets `\caption` strictly *below* the figure float, all captions now appear correctly under their respective figures without any duplication.
- **All six figure PDFs regenerated:** `fig1_perf_panel.pdf`, `fig2_temporal_panel.pdf`, `fig3_accuracy_panel.pdf`, `fig4_error_timeseries.pdf`, `fig5_cumulative_error.pdf`, `fig6_error_heatmap.pdf` were regenerated and synchronized to `else_paper/`.

This resolves the caption placement issue completely. The compiled `manuscript.pdf` (23 pages) was verified with `tectonic` at exit code 0.

---

We believe the revised manuscript is substantially more comprehensive, up-to-date, and clearly delineated in its original contributions. We thank Reviewer 2 for the actionable feedback.

**Sincerely,**

Jason Pandian and I. Kala
