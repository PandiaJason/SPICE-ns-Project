# Response to Reviewer ChatGPTAstra (Revision 3)

**Manuscript Title:** The Limits of Discrete-Event Synchronization in Interplanetary Network Simulation: A Critical Review of Co-Simulation Fidelity  
**Authors:** Jason Pandian and I. Kala  
**Journal:** Simulation Modelling Practice and Theory (Elsevier)

---

We sincerely thank Reviewer ChatGPTAstra for the thorough, incisive, and rigorous evaluation of Revision 2. The reviewer's six critique points identified fundamental areas requiring physical correction, mathematical formalization, and improved reporting accuracy. 

In this major revision, we have:
1. **Completely overhauled the orbital velocity and gravitational parameter initialization**, bringing continuous trajectory errors down to **meter-scale accuracy** ($12.2$ to $32.7$ meters over multi-day arcs), matching continuous integration within $0.12$ to $1.05$ meters across all three profiles.
2. **Upgraded the Event-Driven baseline from a degenerate 1-step model to an authentic multi-event schedule** (incorporating 30-minute periodic DSN telemetry tracking passes for continuous links, producing 36 steps over the 18-hour Elliptical mission), while formalizing the **Zero-Order Hold (ZOH)** kinematic drift ($e \sim \frac{1}{2}\bar{v}\Delta t$) in Section 3.5.2 (Equations 24–28).
3. **Added Section 5.5 ("Cross-Domain Implications: How Astrodynamics Errors Invalidate Network Metrics")**, establishing the exact causal chain linking thousands of kilometers of orbital drift to RF received power (6–14 dB link margin distortion), ModCod phantom throughput, DTN custody timer desynchronization, and masked buffer overflow.
4. **Clarified the predictive event guard mathematics (Equation 20)**, resolving the broken equation reference and explaining why the 3-orbit Mars scenario completes in exactly 49 synchronization steps with zero event detection error ($\epsilon_{\text{net}} = 0.00$ ms).
5. **Detailed the predictive look-ahead timestamp calculation** (analytical conic root-finding with $<1$ ms CPU overhead) and event-matching logic in Equation 36.
6. **Harmonized Algorithm 1 with discrete CCSDS ModCod rate switching (Equation 13)** alongside continuous Shannon capacity (Equation 14), and confirmed planar Keplerian equations across all profiles.
7. **Systematically audited all cross-references, equation numbers, and figure numbers** to match the freshly compiled manuscript (`manuscript.pdf`).

Below is our detailed, point-by-point response to each critique.

---

## 1. Physical Accuracy of Orbital Trajectory Integration

### Reviewer Critique:
> *"The reported position errors do not demonstrate high accuracy. Table 3 reports these Adaptive average errors: Mars 527 km, Elliptical 34,100 km, Cislunar 94,400 km... If the reference ephemeris is high precision, a good integrator should achieve meter-scale or kilometer-scale accuracy, not tens of thousands of kilometers... Table 3 claims Adaptive matches continuous within 0.1%, but Mars 527 vs 494 is 6.7% difference, Elliptical 34.1 vs 33.9 is 0.6%..."*

### Response & Mathematical Resolution:
The reviewer was entirely correct. The previous simulation code initialized orbital velocities using a circular orbital speed approximation ($v \approx \sqrt{\mu / r}$) rather than the exact vis-viva velocity vector $[v_{x0}, v_{y0}]$ corresponding to the eccentric Keplerian state. Consequently, integrating an improperly initialized velocity vector against two-body gravity produced large kinematic divergences ($>500$ km on Mars, tens of thousands of km on Elliptical and Cislunar) that did not reflect the true accuracy of the DOP853 ODE solver.

**Actions Taken in Code & Data (`generate_data.py` & `engine.py`):**
1. **Exact Vis-Viva State Vector Initialization:** We implemented exact initial velocity calculations matching the orbital eccentricity and semi-major axis:
   $$v_{y0} = \sqrt{\mu \left(\frac{2}{r_0} - \frac{1}{a}\right)} = \sqrt{\frac{\mu (1+e)}{a(1-e)}}$$
2. **Central Body Gravity Consistency:** Set exact gravitational parameters matching the central bodies:
   - Mars: $\mu_{\text{Mars}} = 4.2828 \times 10^{13} \text{ m}^3/\text{s}^2$, $a = 3,789.5\text{ km}, e = 0.05$
   - Elliptical (Earth): $\mu_{\text{Earth}} = 3.9860 \times 10^{14} \text{ m}^3/\text{s}^2$, $a = 26,560\text{ km}, e = 0.72$
   - Cislunar (Moon): $\mu_{\text{Moon}} = 4.9049 \times 10^{12} \text{ m}^3/\text{s}^2$, $a = 34,184\text{ km}, e = 0.823$ ($T_{\text{NRHO}} = 6.56$ days)
3. **High-Precision Integration Tolerances:** DOP853 ODE tolerances were set to $\text{rtol} = 10^{-9}$ and $\text{atol} = 10^{-9}$.

### Results in Updated Table 3 (`manuscript.pdf`, Page 17):
All position errors are now validated at **meter-scale precision** across multi-day simulation arcs:

| Profile | Engine | Wall Time (s) | Steps | Speedup | Time-Avg Pos. Error ($\bar{\epsilon}_{\text{pos}}$) | Event Error ($\epsilon_{\text{net}}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Mars** | Fixed | 0.0917 | 343 | $1.00\times$ | **12.20 m** | $29.9\text{ s}$ ($2.99 \times 10^4\text{ ms}$) |
| | Event-Driven | 0.0053 | 7 | $17.30\times$ | **6,943 km** ($6.94 \times 10^6\text{ m}$) | 0.00 ms |
| | Adaptive | 0.0169 | 49 | **$5.43\times$** | **13.25 m** | **0.00 ms** |
| **Elliptical** | Fixed | 0.2828 | 1,077 | $1.00\times$ | **17.64 m** | 0.00 ms |
| | Event-Driven | 0.0155 | 36 | $18.66\times$ | **5,890 km** ($5.89 \times 10^6\text{ m}$) | 0.00 ms |
| | Adaptive | 0.0351 | 108 | **$8.05\times$** | **18.00 m** | **0.00 ms** |
| **Cislunar** | Fixed | 5.0311 | 18,901 | $1.00\times$ | **32.56 m** | $32.7\text{ s}$ ($3.27 \times 10^4\text{ ms}$) |
| | Event-Driven | 0.0116 | 13 | $435.44\times$ | **30,971 km** ($3.10 \times 10^7\text{ m}$) | 0.00 ms |
| | Adaptive | 0.5082 | 1,532 | **$9.90\times$** | **32.68 m** | **0.00 ms** |

**Manuscript Updates:**
- **Exact Differences Stated Truthfully:** We removed the loose "within 0.1%" claim. In Section 5.3, Section 5.4.3, and Figure 7 caption, we report the exact meter differences:
  - On Cislunar (13.1-day arc): Adaptive ($32.68$ m) matches Fixed-Step ($32.56$ m) within **$0.12$ m ($0.37\%$)**.
  - On Elliptical: Adaptive ($18.00$ m) matches Fixed-Step ($17.64$ m) within **$0.36$ m ($2.0\%$)**.
  - On Mars: Adaptive ($13.25$ m) matches Fixed-Step ($12.20$ m) within **$1.05$ m**.
- All errors remain strictly bounded to $<33$ meters over 13.1 days, proving genuine physical trajectory fidelity.

---

## 2. Event-Driven Baseline Justification, Zero-Order Hold Drift, and Cross-Domain Implications

### Reviewer Critique:
> *"The event-driven baseline comparison is poorly justified and misleadingly described. Why does Event-Driven have 7,240 km error on Mars and 101,559 km error on Cislunar? Is it because the integrator takes huge steps between events, or because node positions are held static? The text claims 'over 7,200 km higher error' but the table says 1.02e8 vs 9.43e7..."*

### Response & Physical Explanation:
In traditional discrete-event network simulation frameworks (such as standard NS-3 or OMNeT++ operating without continuous orbital co-simulation), network entities are updated strictly when discrete network events occur (packet generation, arrival, custody transfers, or contact plan boundaries). Between scheduled events—most notably during multi-day occultation blackouts where line-of-sight is severed and no radio packets can traverse the channel—the simulator applies a **zero-order hold (ZOH)** on node coordinates:
$$\hat{\mathbf{r}}(t) = \mathbf{r}(t_i), \quad \forall t \in [t_i, t_{i+1})$$

While coordinates are held static in the network engine, the physical spacecraft traverses its continuous orbital trajectory $\mathbf{r}_{ref}(t)$ under gravitational acceleration. The instantaneous kinematic tracking error $\mathbf{e}_{\text{ZOH}}(t)$ is:
$$\mathbf{e}_{\text{ZOH}}(t) = ||\mathbf{r}_{ref}(t) - \hat{\mathbf{r}}(t)|| = \left|\left|\int_{t_i}^t \mathbf{v}(\tau) d\tau\right|\right|$$
Over an interval $\Delta t_i$ with mean velocity $\bar{v}_i$, the time-averaged position error accumulates as:
$$\bar{\epsilon}_{\text{ZOH}, i} = \frac{1}{\Delta t_i} \int_{t_i}^{t_{i+1}} ||\mathbf{r}_{ref}(t) - \mathbf{r}(t_i)|| dt \approx \frac{1}{2} \bar{v}_i \Delta t_i$$

In Cislunar NRHO, where communication blackouts span $\Delta t_i \approx 6.0 \times 10^4$ s with orbital velocity $\bar{v}_i \approx 1.0$ km/s:
$$\bar{\epsilon}_{\text{ZOH}} \approx \frac{1}{2} (10^3\text{ m/s}) (6.0 \times 10^4\text{ s}) \approx 3.0 \times 10^7\text{ m} \quad (30,000\text{ km})$$

### Upgrade of the Elliptical Baseline:
In the previous draft, because the Elliptical scenario featured continuous line-of-sight with no occultation events, the pure event-driven baseline executed in 1 single step of 18 hours. To ensure the baseline is completely authentic and representative of operational space networks, we implemented a realistic multi-event network schedule: **periodic 30-minute DSN telemetry tracking passes** for continuous links. 
- The Event-Driven engine now executes **36 discrete steps** across the 18-hour mission.
- Between 30-minute passes, the zero-order hold freezes coordinates, accumulating an average kinematic trajectory drift of **$5,890$ km** ($5.89 \times 10^6$ m) with an $18.66\times$ speedup.
- Mars executes in 7 steps (3 orbits, 6 ingress/egress boundaries + initial/terminal epochs), accumulating $6,943$ km drift.
- Cislunar executes in 13 steps (incorporating line-of-sight transitions and DTN custody events), accumulating $30,971$ km drift.

### New Section 5.5: Cross-Domain Implications on Network Metrics
To directly address how this orbital error compromises communications modeling, we added **Section 5.5 ("Cross-Domain Implications: How Astrodynamics Errors Invalidate Network Metrics")** to the manuscript:
1. **Distortion of Received Power and Link Margin:** Received power decays quadratically ($P_{rx} \propto d^{-2}$). The path loss error $\Delta \text{FSPL}$ resulting from an orbital position error $\epsilon_{pos}(t)$ is:
   $$\Delta \text{FSPL}(t) = 20 \log_{10} \left(1 + \frac{\epsilon_{pos}(t)}{d_{true}(t)}\right) \tag{37}$$
   In Cislunar or eccentric orbits ($d \in [6,000, 70,000]$ km), a $30,000$ km drift introduces a **$6.2$ to $14.1$ dB error**. Because deep-space links operate on narrow $2$--$3$ dB margins, this $10$ dB error causes the simulator to model high-SNR throughput when the physical signal is in total radio blackout.
2. **ModCod Bitrate Mismatch and Phantom Throughput:** By freezing coordinates, an uncoupled simulator freezes SNR at an outdated value. If the spacecraft moves from perigee to apogee, the simulator continues transmitting at peak capacity ($20$ Mbps, 32APSK), whereas the physical channel can only sustain QPSK ($5$ Mbps) or outage ($0$ Mbps), generating optimistic "phantom throughput" and masking frame drops.
3. **DTN Custody Transfer and Timer Desynchronization:** Custody transfer timers depend on round-trip light time $\tau_{RTT} = 2 d(t) / c$ (Eq. 15). Spatial displacement of $30,000$ km introduces light-time errors of $\approx 100$ ms (scaling to minutes across interplanetary links), causing premature timer expiration, spurious retransmissions, duplicate bundle storms, and artificial queue congestion.
4. **Masked Onboard Buffer Overflows:** When an event-driven engine overestimates channel throughput, it calculates that the queue is clearing (Eq. 16). In physical reality, degraded link throughput causes telemetry to accumulate, triggering unpredicted buffer overflow and permanent data loss.

**Manuscript Updates:**
- Added formal mathematical derivation of ZOH drift in Section 3.5.2 (Equations 24–28).
- Added Section 5.5 explaining the causal chain to network metrics.
- Elevated and highlighted these cross-domain network implications across the Abstract (line 52), Highlights (Item 2), Introduction (Section 1.2 Item 2, and Section 1.3 Contribution 3), and Conclusion (Section 6), ensuring the cross-disciplinary impact is clear to computer network reviewers.
- Updated Figure 5, Figure 6, and Figure 7 captions with exact numbers ($30,971$ km for Event-Driven, $32.68$ m for Adaptive).

---

## 3. Event Guard Logic and Step Count Explanation

### Reviewer Critique:
> *"The event guard logic is mathematically inconsistent with the reported step counts. Table 3 says Adaptive Mars takes 54 steps over 20,580 seconds (average step 381 s). But if event guard requires 1-second steps near transitions, and transition zone is ±120 s (240 s per transition) with 4 transitions, 4 * 240 = 960 steps minimum just in transition zones. How can the total be 54? Also Section 5.4.2 cites 'Eq. (??)' for event guard."*

### Response & Mathematical Formulation:
1. **Broken Cross-Reference Resolved:** We fixed the unlabelled equation in Section 3.4 by explicitly defining and labeling the event-guard equation as **Equation (20)** (`\label{eq:event_guard}`):
   $$\Delta t = \min \left( \Delta t_{\text{prop}}, \max(\Delta t_{\epsilon}, t_{\text{next}} - t), t_{end} - t \right) \tag{20}$$
   where $\Delta t_{\text{prop}} = \min(\Delta t_{\text{event}}, \Delta t_{\text{physics}})$ and $t_{\text{next}} = \min \{ t_c \in \mathcal{T}_{\text{crit}} \mid t_c > t \}$. In the compiled PDF, Section 5.3.2 now correctly cites **Equation (20)** without any "Eq. (??)" artifacts.

2. **Step Count Explanation (Why Mars Takes Exactly 49 Steps):**
   The reviewer assumed that the orchestrator must execute rigid 1-second steps throughout the entire 240 s transition zone. In our engine implementation:
   - During cruise outside the event window, $\Delta t$ expands to $\Delta t_{\text{coast}} = 600$ s or $\Delta t_{\text{blackout}} = 3600$ s.
   - As the simulation epoch $t$ approaches $t_{\text{next}}$ within the anticipation horizon, $\Delta t$ contracts smoothly toward $\text{DT\_MIN} = 1.0$ s.
   - **Clamping onto the Event Epoch:** The event guard Equation (20) clamps the final step size so that the simulation epoch lands *exactly* on $t_{\text{next}}$ ($\Delta t = t_{\text{next}} - t$), eliminating event detection error ($\epsilon_{\text{net}} = 0.00$ ms).
   - **Immediate Post-Event Expansion:** Once the event boundary is crossed, if the channel enters a stable state (such as an occultation blackout where $\text{LOS} = 0$), the step size does not linger unnecessarily at fine sub-second steps; it immediately re-expands to $\Delta t_{\text{blackout}} = 3600$ s (or $\Delta t_{\text{coast}} = 600$ s in clear line-of-sight).
   - Across the 3 Mars orbits ($20,580$ s duration, 6 ingress/egress boundaries), this combination of long cruising steps and localized boundary-intercept clamping yields **exactly 49 total synchronization steps** while guaranteeing $\epsilon_{\text{net}} = 0.00$ ms.

**Manuscript Updates:**
- Added complete mathematical formulation in Section 3.4 (Equation 20).
- Added detailed explanation in Section 5.3.2 directly addressing the 49-step execution mechanism.

---

## 4. Predictive Look-Ahead Timestamp Calculation

### Reviewer Critique:
> *"The predictive look-ahead timestamp calculation is not explained. Where do t_next_event timestamps come from? How are they calculated? What is the computational overhead? And how does Equation (32) perform event matching?"*

### Response & Algorithmic Details:
1. **Source of Event Epochs ($\mathcal{T}_{\text{crit}}$):** Prospective critical event epochs $t_c \in \mathcal{T}_{\text{crit}}$ correspond to deterministic geometric occultation ingress/egress boundaries and scheduled ground station handover windows.
2. **Calculation Method:** In our co-simulation architecture, prospective occultation epochs are computed during initialization (or refreshed at orbital period milestones) via analytical orbital geometry root-finding algorithms (analogous to the SPICE `gfoclt_c` occultation search tool). The root-finder locates the zero-crossings of the geometric grazing constraint function:
   $$\delta(t) - \delta_{\text{occ}} = 0$$
3. **Computational Overhead:** Because this root-finding is performed on analytical conic arcs or pre-generated ephemeris polynomials, it requires $<1$ ms of CPU time per orbit—representing $<0.1\%$ of total execution time.
4. **Equation (36) Event Matching Logic:** In Section 4.4, we clarified that link state transitions $\hat{t}_e \in \mathcal{E}_{\text{trans}}$ are paired with ground-truth transitions $t_c \in \mathcal{T}_{\text{crit}}$ by matching transition event type (loss-of-signal ingress vs. acquisition-of-signal egress) and node link identity within an association window. This isolates the physical detection delay for each specific occultation event.

**Manuscript Updates:**
- Documented in Section 3.4 (lines 304–308) and Section 4.4 (lines 488–494).

---

## 5. ModCod Staircase vs. Shannon Capacity & 2D Orbital Equations

### Reviewer Critique:
> *"Algorithm 1 is inconsistent with the text regarding continuous vs. discrete data rates. Algorithm 1 line 13 still references continuous Shannon capacity B log2(1+SNR) (Eq. 14), but Section 3.3 and Eq. (13) define the CCSDS ModCod discrete staircase mapping. Also confirm 2D orbital equations for all 3 scenarios."*

### Response & Algorithmic Updates:
1. **Algorithm 1 Updated:** Line 9 of Algorithm 1 (in `manuscript.pdf`, Page 11) now explicitly references the discrete CCSDS ModCod staircase mapping (Equation 13) for transmission bitrate $R_{\text{bit}}$, alongside the continuous Shannon envelope (Equation 14):
   $$\text{Calculate link parameters: } \text{SNR}(t+\Delta t), R_{\text{bit}} \text{ via ModCod Eq. (13), and } R_{\text{shannon}} \text{ via Eq. (14)}$$
2. **Discrete Engine Integration:** Section 4.1 clarifies that `DiscreteEngine` uses discrete ModCod rate switching (Equation 13) to step packet serialization and queue flushing.
3. **2D Orbital Equations Confirmed:** Section 4.1 confirms that all three benchmark profiles integrate the planar two-body Keplerian equations of motion $\ddot{\mathbf{r}} = -\frac{\mu}{||\mathbf{r}||^3}\mathbf{r}$ in the 2D orbital plane $[x, y, v_x, v_y]$ using SciPy's DOP853 integrator.

---

## 6. Response Letter Cross-References and Equation Numbering

### Reviewer Critique:
> *"Response letter locations and equation numbers do not match the manuscript..."*

### Response:
All section numbers, table numbers, figure numbers, and equation numbers across `Response_to_Reviewer1.txt`, `Response_to_Reviewer2.txt`, and this letter have been systematically audited and synchronized against the compiled PDF (`manuscript.pdf`):
- **Equation (1)–(3):** Relativistic time dilation & proper-time drift rate (Section 1.1).
- **Equation (10):** Free-space path loss FSPL (Section 3.2).
- **Equation (13):** Discrete CCSDS ModCod staircase mapping (Section 3.2).
- **Equation (14):** Continuous Shannon capacity upper envelope (Section 3.2).
- **Equation (15):** Dynamic propagation delay $\tau_{\text{prop}} = d/c$ (Section 3.3).
- **Equation (16):** Discrete packet buffer summation (Section 3.3).
- **Equations (17)–(19):** Adaptive step size selection $\Delta t_{\text{prop}}$ (Section 3.4).
- **Equation (20):** Predictive event-guard step bounding rule (Section 3.4).
- **Equations (24)–(28):** Event-driven zero-order hold kinematic drift bounds (Section 3.5.2).
- **Equation (31):** Instantaneous position error relative to reference (Section 4.3).
- **Equation (32):** Analytical buffer conservation model (Section 4.3).
- **Equation (35):** Time-averaged continuous position error $\bar{\epsilon}_{\text{pos}}$ (Section 4.4).
- **Equation (36):** Boundary detection timing error $\epsilon_{\text{net}}$ (Section 4.4).
- **Equation (37):** Path loss error $\Delta \text{FSPL}$ due to position drift (Section 5.5).
- **Table 1:** Comparison of simulation tools (Page 6).
- **Table 2:** Simulation parameters (Page 15).
- **Table 3:** Benchmark performance metrics (Page 17).
- **Figure 1:** System architecture diagram (Page 12).
- **Figure 2:** Temporal dynamics panel (Mars step adaptation & Cislunar buffer evolution, Page 16).
- **Figure 3:** Accuracy-efficiency panel (Pareto frontier & error breakdown, Page 17).
- **Figure 4:** Computational performance panel (Wall-clock time & Scalability 10–500 nodes, Page 17).
- **Figure 5:** Per-step position error timeseries (Page 18).
- **Figure 6:** Cumulative integrated position error curves (Page 19).
- **Figure 7:** Summary error & speedup heatmaps (Page 19).

---

We believe these comprehensive revisions thoroughly address all six critique points and establish the manuscript on unassailable physical and mathematical foundations.

**Sincerely,**  
Jason Pandian and I. Kala  
*Simulation Modelling Practice and Theory (Elsevier)*
