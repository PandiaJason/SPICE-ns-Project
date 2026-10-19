# Lightning Talk Proposal — ICNS3 - 2026

**Conference:** International Conference on ns-3 (ICNS3 - 2026)  
**Session:** Lightning Talks (5-Minute Technical Presentation)  
**Presentation Mode:** Virtual Presentation *(or In-Person, subject to travel grant/visa approval)*  

---

### Title
**The Limits of Discrete-Event Schedulers in Interplanetary Network Simulation: Why Deep Space Breaks Conventional DES Paradigms**

*(Alternative Title: Rethinking Discrete-Event Simulation for Interplanetary Networks: Fundamental Synchronization Limits in Long-Delay Regimes)*

---

### Presenter Names and Affiliations
- **Jason Pandian** (Presenter)  
  *Department of Information Technology, Nehru Institute of Technology, Coimbatore, Tamil Nadu, India*  
  *Email:* pandiajason@gmail.com  


---

### Abstract *(Word count: 196 words — strictly < 200 words)*

Conventional Discrete-Event Simulation (DES) frameworks, such as ns-3, assume that network states evolve exclusively via instantaneous, causal state transitions triggered by discrete event queue pops. While highly effective for terrestrial and near-Earth topologies, this paradigm collapses in deep space, where network topology is a continuous function of time $\mathcal{G}(t)$ governed by $n$-body gravitational motion, multi-minute light-time delays (up to 24 min on Mars), and planetary occultations.

Standard DES faces an unavoidable dilemma: pure event-driven scheduling freezes orbital dynamics during communication blackouts, accumulating over 30,970 km in unphysical trajectory drift that severely distorts received power (by 6.2 to 14.1 dB) and induces ModCod rate switching errors; conversely, fixed-step synchronization introduces tens of seconds in boundary quantization delay ($\epsilon_{\text{net}}$ up to 32.7 s) and massive computational waste. Furthermore, multi-minute propagation delays break static delay modeling, requiring iterative light-cone solving for causal arrival scheduling.

This lightning talk presents a critical architectural evaluation of DES fidelity in interplanetary networking. We report empirical Pareto frontiers demonstrating 5.43$\times$ to 9.90$\times$ speedups with zero boundary error ($\epsilon_{\text{net}} = 0.00$ ms) across three canonical space profiles, verify sublinear scalability to 500 nodes, and propose three concrete blueprints to extend ns-3 for solar-system-scale simulation.

---

### 5-Minute Lightning Talk Schedule & Slide Breakdown (8 Content Slides)

| Time Slot | Slide | Focus & Visual Artifact | Key Technical Takeaway |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:35** | **Slide 1** | **Core DES Abstraction vs. Deep Space Reality** | Why continuous $\mathcal{G}(t)$ and multi-minute delays break discrete event queues; Causal Inversion problem. |
| **0:35 – 1:10** | **Slide 2** | **The DES Synchronization Dilemma** | Approach A (Fixed-Step 32.7 s error) vs. Approach B (Event-Driven $>30,970$ km blackout drift); The Incompatibility Theorem. |
| **1:10 – 1:50** | **Slide 3** | **Multi-Rate Co-Simulation Engine Architecture**<br/>*(Hero Graph: System Architecture Schematic)* | Continuous SPICE/ODE integrator coupled with discrete ns-3 event queue; Predictive event guard $\Delta t_k = \min(\Delta t_{\text{prop}}, t_{\text{evt}} - t_k)$ achieving zero boundary delay ($\epsilon_{\text{net}} = 0.00$ ms). |
| **1:50 – 2:30** | **Slide 4** | **Pareto Frontier & Empirical Benchmarks**<br/>*(Hero Graph: Log-Log Clean Pareto Frontier)* | Optimal knee achieving $5.43\times$–$9.90\times$ speedup with $\epsilon_{\text{net}} = 0.00$ ms; cross-profile benchmark summary table; sublinear 500-node scalability. |
| **2:30 – 3:10** | **Slide 5** | **Long-Arc Trajectory Drift Across Regimes**<br/>*(Hero Graph: Integrated Cumulative Drift Plot)* | Freezing coordinates during blackouts explodes to $>30,970$ km in Event-Driven DES; Adaptive suppresses drift to meters ($13.3$–$32.7$ m) across Mars, Molniya, and Cislunar. |
| **3:10 – 3:55** | **Slide 6** | **How Astrodynamics Errors Invalidate Network Metrics**<br/>*(Detailed 4-Pillar Cross-Domain Analysis, §5.5)* | (1) RF link margin collapse: $\Delta\text{FSPL} \approx 6.2$–$14.1$ dB causing false link status in physical blackout; (2) ModCod phantom throughput; (3) DTN custody timer storms ($\Delta\tau \approx 100$ ms); (4) Masked onboard buffer overflow and data loss. |
| **3:55 – 4:35** | **Slide 7** | **Three Architectural Blueprints for ns-3** | Concrete proposals: (1) In-flight iterative light-cone delay solver, (2) Predictive boundary event guard scheduler hooks, (3) Relativistic proper-time multi-clock framework. |
| **4:35 – 5:00** | **Slide 8** | **Conclusion, SIMPAT Review & Open-Source Code** | Review status at Elsevier SIMPAT; QR code and repository link for open-source engine code and benchmark artifacts. |

---

### Associated Work & Publication Status
- **Full Manuscript:** *"The Limits of Discrete-Event Synchronization in Interplanetary Network Simulation: A Critical Review of Co-Simulation Fidelity"*  
- **Authors:** Jason Pandian and Dr. I. Kala  
- **Journal:** Under active peer review at **Simulation Modelling Practice and Theory (Elsevier)**  
- **Open-Source Code & Benchmark Artifacts:** [GitHub Repository](https://github.com/PandiaJason/SPICE-ns-Project/tree/main/Adaptive-Multi-Rate-Co-Simulation-Engine)
