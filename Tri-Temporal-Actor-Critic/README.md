# Tri-Temporal Actor-Critic (TTAC)

An advanced Reinforcement Learning framework designed to solve **State-Dependent, Non-Uniform, and Unbounded Delayed Markov Decision Processes (SD-NU-UDMDPs)**. In real-world environments (such as remote robotic control, aerospace communication, and decentralized edge computing), feedback signals (observations and rewards) are delayed through noisy, state-dependent communication channels. TTAC addresses these issues by decoupling learning and execution across three distinct timescales.

---

## 🌟 Key Architecture & Timescales

The TTAC framework coordinates three layers operating concurrently:

1. **Predictive Layer (Past $\rightarrow$ Present)**: 
   * Leverages a **Neural Ordinary Differential Equation (Neural ODE)** solver to integrate latent trajectories.
   * Reconstructs the true, unobserved current environment state $s_t$ by projecting forward from the oldest unconfirmed observation $s_{t-\tau_t}$ using the history of in-flight actions $\mathcal{H}_{past} = \{a_{t-\tau_t}, \dots, a_{t-1}\}$.
2. **Present Layer (Present)**:
   * Selects action $a_t$ based on the reconstructed state estimate.
   * Calculates immediate policy updates using local, generative pseudo-rewards to maintain smooth gradient propagation without waiting for delayed environmental signals.
3. **Retrospective Layer (Future $\rightarrow$ Present)**:
   * When delayed physical rewards $r_t$ eventually arrive in the future at step $t + \tau_t$, this layer performs causal credit assignment.
   * Utilizes a retrospective attention mechanism to align delayed reward feedback to the past actions that caused them across the history window $\mathcal{H}_{future} = \{a_t, \dots, a_{t+\tau_t-1}\}$.

---

## 🛠️ Repository Structure

* `run_framework.py`: The unified simulation and evaluation pipeline containing environments, agent definitions, training loops, profiling suites, and publication-grade figure generation.
* `simulation/`: Stores generated configuration profiles, training outputs, and metric databases.
  * `simulation/data/`: Configuration parameters for continuous control and edge network benchmarks.
  * `simulation/outputs/`: Convergence metrics, policy gradient logs, and attention weights.
  * `simulation/graphs/`: Generated visualization figures.

*(Note: The manuscript LaTeX directory `paper/` is excluded from the repository).*

---

## 🎮 Simulation Benchmarks

TTAC is evaluated on two highly delayed testbeds:

1. **Delayed Continuous Control**:
   * A state-dependent continuous control task where mechanical delay increases non-linearly with joint velocity ($\tau_t \propto \|v_t\|^2$).
2. **Asynchronous Edge Network**:
   * A high-throughput routing benchmark simulating packet queuing delay. Delays become unbounded ($\tau_t \rightarrow \infty$) near channel capacities, forcing observations to arrive out-of-order.

---

## 🚀 Getting Started

### Prerequisites

Ensure you have a modern Python 3 installation along with the following libraries:
```bash
pip install torch numpy pandas matplotlib seaborn scipy
```

### Execution

To run the full simulation pipeline, training benchmarks, scaling profiles, and figure regeneration:
```bash
python3 run_framework.py
```
Upon completion, metrics will be saved in `simulation/outputs/` and final visual assets will be rendered under `simulation/graphs/`.

---

## 📄 License

This repository is licensed under the **Apache License 2.0**. For details, please see the [LICENSE](LICENSE) file or visit the [Apache License website](http://www.apache.org/licenses/LICENSE-2.0).
