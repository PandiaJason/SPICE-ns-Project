# Response to Reviewer 1

**Manuscript Title:** The Limits of Discrete-Event Synchronization in Interplanetary Network Simulation: A Critical Review of Co-Simulation Fidelity

**Journal:** Simulation Modelling Practice and Theory / Acta Astronautica

**Submission Date:** September 5, 2026

---

We sincerely thank Reviewer 1 for the detailed, technically precise critique. The reviewer's comments have substantially strengthened the manuscript, and we have addressed each point with specific revisions documented below. All changes are clearly marked in the revised manuscript.

---

## Comment 1: Incorrect Speedup Claim in Abstract and Conclusion

> *"The abstract states that the 'adaptive stepping achieves speedup factors of up to 17.5x over fixed-step baselines'. However, Table 3 and Figure 7(b) explicitly show that the 17.48x speedup was achieved by the Event-Driven baseline engine on the Cislunar profile, whereas the proposed Adaptive engine achieved only a 9.02x speedup. Claiming the performance metric of a baseline method as the achievement of the proposed method is a critical error in scientific reporting."*

**Response:** The reviewer is entirely correct. This was a critical reporting error. The $17.48\times$ speedup in the earlier Cislunar profile belonged to the Event-Driven baseline, not the proposed Adaptive engine. In our validated benchmark suite, the Adaptive engine's peak speedup is $9.90\times$ (Cislunar), $8.05\times$ (Elliptical), and $5.43\times$ (Mars), while Event-Driven achieves an unphysical speedup of $435.4\times$ on Cislunar at the cost of $>30,970$~km of trajectory drift.

**Revisions Made:**
- **Abstract (line 52):** Corrected to *"adaptive stepping achieves speedup factors of up to $9.90\times$ over fixed-step baselines ($5.43\times$ on Mars, $8.05\times$ on elliptical orbits) while maintaining meter-scale orbital accuracy ($13.3$--$32.7$~m, matching continuous integration within $0.12$--$1.05$~m) and completely eliminating boundary detection error ($\epsilon_{net} = 0.00$~ms)."*
- **Highlights (line 65):** Updated to *"The adaptive method bounds event error to zero and yields up to $9.90\times$ speedup on Cislunar profiles ($8.05\times$ on Elliptical, $5.43\times$ on Mars) while maintaining meter-scale orbital accuracy ($<33$~m)."*
- **Conclusion (Section 6, line 641):** Updated to *"achieves speedup factors of up to $9.90\times$ relative to fixed-step baselines ($8.05\times$ on elliptical profiles, and $5.43\times$ on Mars)."*
- **Figure 7(b) discussion / caption (line 624):** Clarified that the highest speedup in the heatmap belongs to the Event-Driven baseline ($435.4\times$ on Cislunar) at the expense of massive orbital drift ($30,971$~km), explicitly distinguishing it from the physically faithful Adaptive result ($9.90\times$).

---

## Comment 2: Relativistic Equations Placed in Wrong Section

> *"In Section 3.5, the authors present Equations 17 through 19 detailing Relativistic Proper-Time Propagation. However, the authors admit in Section 1.4 and Section 6 that resolving relativistic clock bias (Gap 3) is beyond the scope of their current heuristic. Including complex mathematical models in the 'System Modeling' section that are not actually implemented in the CoSimOrchestrator is misleading. This section should be moved to a 'Theoretical Background' or integrated into the 'Future Work' discussion."*

**Response:** The reviewer identifies a structural inconsistency that misrepresents the scope of the implementation. The Schwarzschild metric (proper-time drift equation), the post-Newtonian clock correction, and the cumulative clock bias integral are theoretical derivations that establish the formal motivation for Fidelity Gap 3 — they are not implemented sub-steps of the orchestrator. We have completely relocated these equations.

**Revisions Made:**
- **Section 3.5 deleted:** The stand-alone subsection "Relativistic Proper-Time Propagation" has been removed from the System Modeling chapter.
- **Section 1.3 (new location, lines 95–119):** The three equations are now embedded in *"The Relativistic Simultaneity Problem and Proper-Time Drift (Fidelity Gap 3)"* within the Introduction. The Schwarzschild metric (Eq. \eqref{eq:schwarzschild}), post-Newtonian approximation (Eq. \eqref{eq:post_newtonian}), and cumulative clock bias integral (Eq. \eqref{eq:clock_bias}) are presented here as the **formal mathematical proof** of why universal coordinate time fails in deep space — the quantitative motivation for Gap 3. The numerical example ($\delta\tau/\tau \approx -4.4 \times 10^{-10}$, i.e., $38\,\mu$s/day, $14\,$ms/year for Mars low orbit) immediately follows to contextualize the fidelity ceiling.
- **Explicit scope disclaimer added (line 116):** A clearly delineated note states: *"In the co-simulation orchestrator implemented and benchmarked in this paper, numerical astrodynamics propagation and discrete network events are coupled in coordinate time $t$ (Barycentric Dynamical Time, TDB). Equations~\eqref{eq:schwarzschild}--\eqref{eq:clock_bias} are derived here to analytically quantify the accumulated timing bias and establish the theoretical fidelity ceiling (Fidelity Gap 3) for current simulators, serving as the mathematical blueprint for future proper-time-aware schedulers, but are not actively stepped in the benchmark prototype."*

This placement — in the Theoretical Background preceding the Identified Fidelity Gaps — unambiguously frames Gap 3 as a formal, quantified impossibility of universal coordinate time in deep space, without implying implementation.

---

## Comment 3: Insufficient Analysis of Adaptive Engine Slowdown on Mars Profile

> *"The results in Table 3 indicate that the Adaptive engine is actually slower than the Fixed-Step baseline for the Mars profile, recording a speedup factor of 0.77x (wall time of 0.1744s vs 0.1342s). While Section 5.4 briefly attributes this to overhead of 'frequent step contractions and ODE solver restarts', a high-tier journal requires a more rigorous analysis."*

**Response:** We thank the reviewer for this critical observation. In the initial revision, step chattering occurred near occultation boundaries because the step selector lacked an explicit boundary-intercept guard. To solve this, we formulated and implemented the predictive boundary event guard rule (Eq.~\eqref{eq:event_guard}):
$$\Delta t = \min \left( \Delta t_{\text{prop}}, \max(\Delta t_{\epsilon}, t_{\text{next}} - t), t_{end} - t \right)$$

Rather than marching at rigid 1-second intervals across a wide fixed transition window, the orchestrator cruises at $\Delta t_{\text{coast}} = 600$~s during line-of-sight and $\Delta t_{\text{blackout}} = 3600$~s during occultation, contracting toward 1.0~s only during the immediate approach to the transition epoch, and stepping directly onto $t_{\text{next}}$ via Eq.~\eqref{eq:event_guard}. Once the occultation boundary is crossed, the channel state is stably occulted ($\text{LOS} = 0$), allowing the step selector to immediately transition to $\Delta t_{\text{blackout}}$ without redundant sub-stepping in the dark.

**Revisions Made:**
- **Section 3.4 & Algorithm 1:** Documented the event-guard rule as Eq.~\eqref{eq:event_guard} and integrated it into line 6 of Algorithm 1.
- **Section 5.4.2:** Added a dedicated analytical boundary analysis explaining why the Mars scenario completes in only 49 synchronization steps with zero event error ($\epsilon_{\text{net}} = 0.00$~ms).
- **Table 3 & Figure 4(a):** Updated with final benchmark metrics: Mars adaptive execution time dropped to $0.0169$~s across 49 steps, delivering a **$5.43\times$ speedup** over the Fixed-Step baseline ($0.0917$~s, 343 steps), completely resolving the bottleneck.

---

## Comment 4: Verification Under Extreme Network Load and Sub-Second Micro-Events

> *"The authors should clarify if this validation holds true under extreme network load conditions (e.g., massive packet flooding during a brief line-of-sight window), and how the adaptive engine prevents missing micro-events that might occur between the 1.0-second DT_MIN lower bound."*

**Response:** We have expanded Section 4.3 with two dedicated sub-analyses.

**Revisions Made:**
- **Section 4.3, Extreme Load Verification (line 438):** The verification framework now explicitly handles the overload case $\lambda(\tau) \gg R_{bit}(\tau)$. The boundary operator $\min(C_{buf}, \cdot)$ in the analytical buffer model (Eq. \eqref{eq:buffer_anal}) rigorously mirrors discrete saturation. Dropped traffic volume is computed as $\Delta D_{drop} = \max\!\left(0, \int_{t_i}^{t_{i+1}} \frac{\lambda - R_{bit}}{8}\,d\tau - (C_{buf} - B_{anal}(t_i))\right)$. Verification against $\Delta t_{ref} = 0.01\,$s confirms $\epsilon_{logic} < 10^{-7}$ bytes and zero drop discrepancy under impulse saturation.
- **Section 4.3, Sub-Second Micro-Event Resolution (lines 440–449):** A formal **time-scale separation principle** (three parts) establishes: (1) $\text{DT\_MIN} = 1.0\,$s is a *macro-coupling* bound — orbital displacement is $< 3.5\,$km/s, causing $< 0.001\,$dB path-loss change per second; (2) the DiscreteEngine maintains its own sub-millisecond internal DEVS priority queue within each 1-second window; (3) the **event-guard rule** $\Delta t = \min(\Delta t_{adaptive}, \max(\Delta t_\epsilon, t_{event} - t))$ with $\Delta t_\epsilon = 10^{-4}\,$s contracts the coupling step exactly to the micro-event epoch without skipping.

---

## Comment 5: Continuous Shannon Approximation vs. Discrete CCSDS ModCod

> *"Real-world deep space links rely on discrete Variable Coding and Modulation (VCM) schemes defined by specific CCSDS standards. Treating capacity as a continuous logarithmic curve may artificially smooth out the discrete step-changes in throughput."*

**Response:** The reviewer raises a valid concern about physical realism. We have implemented a realistic discrete CCSDS ModCod staircase model alongside the continuous Shannon envelope.

**Revisions Made:**
- **Section 3.2 (lines 270–287):** A new CCSDS VCM discrete staircase equation (Eq. \eqref{eq:modcod}) is introduced. The piecewise model maps hardware SNR demodulation thresholds $\Gamma = \{\gamma_1, \ldots, \gamma_K\}$ (e.g., QPSK rate-1/2 at $1.5\,$dB, 8PSK rate-2/3 at $6.2\,$dB, 16APSK/32APSK at higher regimes) to operational bitrates $R_k$, exactly reflecting CCSDS 131.2-B-1 (LDPC) and CCSDS 231.0-B-1 (Turbo code) standards.
- The continuous Shannon limit (Eq. \eqref{eq:shannon}) is retained as the **theoretical upper capacity envelope** for upper-bounding error analysis, with explicit statement that the staircase is the operationally correct physical model.
- **Adaptive relevance explicitly stated (line 286):** The discrete ModCod thresholds *amplify* the necessity of adaptive co-simulation: under fixed-step coupling, the simulator misses the exact epoch at which $\text{SNR}$ crosses $\gamma_k$, causing delayed down-modulation (simulated packet drops) or delayed up-modulation (link under-utilization). The adaptive gradient detector ($\left|\frac{d\text{SNR}}{dt}\right| > 0.04\,$dB/s) contracts the coupling step to capture ModCod boundaries with sub-second precision.

---

## Comment 6: Scalability Claims Unsupported by Benchmark Range

> *"This conclusion is drawn from a benchmark of only 3 to 30 spacecraft nodes. A 30-node network is insufficiently small to confidently claim O(1) or sub-linear routing/computational complexity for 'large' swarms. The authors should either expand the scalability test to a genuinely large network (e.g., 100–500 nodes) or restrict their claims."*

**Response:** We have expanded the scalability benchmark by an order of magnitude.

**Revisions Made:**
- **`simulation/generate_data.py`:** Node counts updated to `[10, 50, 100, 200, 300, 400, 500]`.
- **`simulation/run_scalability.py`:** A dedicated scalability script was executed, producing `scalability_metrics.csv`. Results: 10 nodes → 0.839 s; 500 nodes → 8.335 s (1,722 steps).
- **Figure 1(b):** Updated to plot 7 points spanning 10–500 nodes against $O(N)$ and $O(N^2)$ reference curves, demonstrating empirically sub-linear scaling.
- **Section 5.4.1 (line 586):** *"we varied the network size in the Cislunar profile across a wide range of node counts from 10 to 500 nodes... a 50-fold expansion in network node count that incurs only a 9.9-fold increase in wall-clock time, growing far below the linear $O(N)$ reference curve."*
- The scope claim has been correspondingly revised to *"small-to-medium relay constellations"* in the conclusion; a note acknowledges that large swarms ($N > 500$) with dynamic inter-satellite links and topology-aware routing would require a dedicated complexity analysis.

---

## Comment 7: DTN Buffer as Continuous Fluid vs. Discrete Bundle Protocol

> *"Equation (13) models DTN buffer occupancy as a continuous fluid flow based on bitrates. The DTN Bundle Protocol (RFC 5050/9171) operates on discrete bundles, not continuous data flows. A fluid approximation masks actual discrete queueing dynamics."*

**Response:** The reviewer correctly identifies a misrepresentation. We have replaced the fluid model with an explicit discrete packet queue formulation and tempered all protocol simulation claims.

**Revisions Made:**
- **Section 3.3 (lines 295–303):** The buffer model is now a **discrete packet summation**: $B_{buf}(t) = \sum_{p \in \mathcal{Q}(t)} S(p)$ (Eq. \eqref{eq:buffer_discrete}). Each packet $p$ has an explicit byte size $S(p)$ bounded by $\text{MTU} = 1024$ bytes. Packet generation, drop, transmission serialization, and reception timestamps are all discretized. The per-step transmission byte allowance is $M_{tx} = \lfloor R_{bit}\Delta t/8 \rfloor$ (integer floor), correctly reflecting discrete dequeuing.
- **DTN scope disclaimer (line 302):** *"We emphasize that the DiscreteEngine implements an abstracted queue and custody management model designed to evaluate cross-domain temporal synchronization and storage dynamics, rather than a full-stack RFC 5050 / RFC 9171 protocol emulator."* This explicitly tempers over-reaching protocol simulation claims while validating the abstraction as sufficient for synchronization benchmarking.
- The continuous analytical buffer (Eq. \eqref{eq:buffer_anal}) is retained **only** in Section 4.3 as the verification reference against which the discrete engine is validated — not as the operational model.

---

We trust that the above revisions fully address all technical concerns raised by Reviewer 1. The manuscript is substantially strengthened by these corrections.

**Sincerely,**

Jason Pandian and I. Kala
