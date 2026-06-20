#!/usr/bin/env python3
import os
import shutil
import subprocess

def create_tikz1_content():
    return r"""\documentclass[tikz,border=10pt]{standalone}
\usetikzlibrary{arrows.meta, positioning, calc}
\begin{document}
\begin{tikzpicture}[scale=0.85, >=Stealth,
    axis/.style={->, thick, gray!80},
    point/.style={circle, fill=black, inner sep=1.5pt},
    envpoint/.style={circle, fill=red!60!black, inner sep=2pt},
    agentpoint/.style={circle, fill=blue!60!black, inner sep=2pt},
    label/.style={font=\footnotesize}]

    % Timelines
    \draw[axis] (0, 2) -- (12.0, 2) node[right, black] {Environment Timeline};
    \draw[axis] (0, 0) -- (12.0, 0) node[right, black] {Agent Timeline};

    % Time Marks
    \draw[dashed, gray!60] (1.5, 2.5) -- (1.5, -0.6) node[below=2pt, black] {$t - \tau_t$ (Past)};
    \draw[dashed, gray!60] (6.5, 2.5) -- (6.5, -0.6) node[below=2pt, black] {$t$ (Present)};
    \draw[dashed, gray!60] (10.5, 2.5) -- (10.5, -0.6) node[below=2pt, black] {$t + \tau_t$ (Future)};

    % Environment State points
    \node[envpoint] (s_past) at (1.5, 2) {};
    \node[above=2pt of s_past, label] {State $s_{t-\tau_t}$};

    \node[envpoint] (s_curr) at (6.5, 2) {};
    \node[above=2pt of s_curr, label] {True State $s_t$, $r_t$};

    \node[envpoint] (s_future) at (10.5, 2) {};
    \node[above=2pt of s_future, label] {State $s_{t+\tau_t}$};

    % Agent point
    \node[agentpoint] (obs_t) at (6.5, 0) {};
    \node[above left=2pt of obs_t, label] {Observe $s_{t-\tau_t}$};

    \node[agentpoint] (obs_future) at (10.5, 0) {};
    \node[above left=2pt of obs_future, label] {Receive $r_t$, $s_t$};

    % Delay Arrows (Past to Present)
    \draw[->, ultra thick, orange, dashed] (1.5, 2) -- node[midway, above right, label, text=orange!80!black] {Past Delay $\tau_t$} (6.5, 0);

    % Delay Arrows (Present to Future)
    \draw[->, ultra thick, orange, dashed] (6.5, 2) -- node[midway, above right, label, text=orange!80!black] {Future Delay $\tau_t$} (10.5, 0);

    % Actions in-flight
    \draw[<->, thick, blue!70!black] (1.5, -1.4) -- node[below=2pt, font=\scriptsize, align=center] {Past In-Flight Actions\\$\mathcal{H}_{past} = \{a_{t-\tau_t}, \dots, a_{t-1}\}$} (6.5, -1.4);
    \draw[<->, thick, blue!70!black] (6.5, -1.4) -- node[below=2pt, font=\scriptsize, align=center] {Future In-Flight Actions\\$\mathcal{H}_{future} = \{a_t, \dots, a_{t+\tau_t-1}\}$} (10.5, -1.4);

    % Action execution flow
    \draw[->, thick, blue!60!black, dashed] (6.5, 0) .. controls (7.2, 0.7) and (7.2, 1.3) .. (6.5, 2) node[midway, right, label] {Action $a_t$};
    
\end{tikzpicture}
\end{document}
"""

def create_tikz2_content():
    return r"""\documentclass[tikz,border=10pt]{standalone}
\usetikzlibrary{arrows.meta, positioning, calc}
\begin{document}
\begin{tikzpicture}[
    node distance=1.8cm and 3.0cm,
    box/.style={draw, fill=blue!5, rectangle, rounded corners, minimum width=3.0cm, minimum height=1.2cm, align=center, font=\small\bfseries},
    env/.style={draw, fill=green!5, rectangle, rounded corners, minimum width=3.0cm, minimum height=1.2cm, align=center, font=\small\bfseries},
    arrow/.style={-Latex, thick, draw=black!70},
    label/.style={font=\footnotesize, align=center}
]
    % Nodes
    \node[env] (env) {Delayed Environment\\(Latency $\tau_t(s)$)};
    \node[box, right=of env, fill=orange!10] (predictive) {Predictive Layer\\(Continuous-Time\\Neural ODE)};
    \node[box, right=of predictive, fill=blue!10] (present) {Present Layer\\(Actor-Critic Agent\\with $\mathcal{G}_\psi$)};
    \node[box, below=1.8cm of present, fill=red!10] (retrospective) {Retrospective Layer\\(Non-Local Attention)};

    % Arrows
    \draw[arrow] (env) -- node[above=4pt, font=\footnotesize, align=center] {Delayed State\\$s_{t-\tau_t}$} (predictive);
    \draw[arrow] (predictive) -- node[above=4pt, font=\footnotesize, align=center] {Estimated State\\$\hat{s}_t$} (present);
    \draw[arrow] (present.east) -- ++(0.6,0) |- node[pos=0.25, right=4pt, font=\footnotesize, align=left] {Pseudo-Reward\\$\hat{r}_t$} (retrospective.east);
    
    % Action feedback path
    \draw[arrow] (present.north) -- ++(0,0.5) -| node[pos=0.25, above=2pt, font=\footnotesize] {Action $a_t$} (env.north);
    
    % Retrospective inputs and feedback
    \draw[arrow] (env.south) |- node[pos=0.4, right=4pt, font=\footnotesize] {Delayed Return $R_t$} (retrospective.west);
    
    \draw[arrow, dashed, draw=red!80] (retrospective.north) -- node[left=6pt, font=\footnotesize, align=right] {Update $\mathcal{G}_\psi$ parameters $\psi$\\and correct $Q^\pi - \mathbf{E}_{align}$} (present.south);
    
\end{tikzpicture}
\end{document}
"""

def create_tikz3_content():
    return r"""\documentclass[tikz,border=10pt]{standalone}
\usetikzlibrary{arrows.meta, positioning, calc}
\begin{document}
\begin{tikzpicture}[
    scale=0.9, >=Stealth,
    node distance=1.5cm and 2.5cm,
    robot/.style={draw, fill=green!10, rectangle, rounded corners, minimum width=2.5cm, minimum height=1.2cm, align=center, font=\small\bfseries},
    delay/.style={draw, fill=orange!10, circle, minimum size=1.8cm, align=center, font=\scriptsize\bfseries},
    controller/.style={draw, fill=blue!10, rectangle, rounded corners, minimum width=2.8cm, minimum height=1.2cm, align=center, font=\small\bfseries},
    arrow/.style={-Latex, thick, draw=black!70},
    label/.style={font=\footnotesize, align=center}
]
    % Nodes
    \node[robot] (robot) {HalfCheetah\\Robot Body};
    \node[delay, right=2.2cm of robot] (delay) {Variable\\Latency\\$\tau_t \propto v_x^2$};
    \node[controller, below=1.8cm of delay] (agent) {TTAC Agent\\(Neural ODE +\\Actor-Critic)};
    
    % Feedback loop
    \draw[arrow] (robot.east) -- node[above, label] {Physical State\\$s(t)$, Velocity $v_x$} (delay.west);
    \draw[arrow] (delay.south) -- node[right, label] {Delayed Observation\\$s(t-\tau_t)$} (agent.north);
    
    % Command path
    \draw[arrow] (agent.west) -| node[pos=0.3, above, label] {Action Torques $a(t)$\\(Cubic Spline Interpolation)} (robot.south);
    
\end{tikzpicture}
\end{document}
"""

def create_tikz4_content():
    return r"""\documentclass[tikz,border=10pt]{standalone}
\usetikzlibrary{arrows.meta, positioning, calc, shapes.geometric}
\begin{document}
\begin{tikzpicture}[
    scale=0.9, >=Stealth,
    node distance=1.5cm and 2.5cm,
    client/.style={draw, fill=blue!10, circle, minimum size=1.2cm, align=center, font=\footnotesize\bfseries},
    router/.style={draw, fill=orange!10, rectangle, rounded corners, minimum width=1.8cm, minimum height=1.0cm, align=center, font=\footnotesize\bfseries},
    agent/.style={draw, fill=red!10, ellipse, minimum width=2.5cm, minimum height=1.2cm, align=center, font=\footnotesize\bfseries},
    arrow/.style={-Latex, thick, draw=black!70},
    label/.style={font=\tiny, align=center}
]
    % Nodes
    \node[client] (src) {Client\\(Source)};
    \node[router, right=2.2cm of src] (r1) {Router A\\Queue $Q_1$};
    \node[router, above right=1.0cm and 2.2cm of src] (r0) {Router B\\Queue $Q_2$};
    \node[router, below right=1.0cm and 2.2cm of src] (r2) {Router C\\Queue $Q_3$};
    \node[client, right=6.5cm of src] (dst) {Server\\(Sink)};
    
    % TTAC Agent Controller
    \node[agent, below=1.8cm of r2] (ctrl) {TTAC Routing\\Controller};

    % Paths
    \draw[arrow] (src) -- node[above left, label] {Packets} (r0);
    \draw[arrow] (src) -- node[above, label] {Packets} (r1);
    \draw[arrow] (src) -- node[below left, label] {Packets} (r2);
    
    \draw[arrow] (r0) -- node[above right, label] {Delayed $\tau_2(Q_2)$} (dst);
    \draw[arrow] (r1) -- node[above, label] {Delayed $\tau_1(Q_1)$} (dst);
    \draw[arrow] (r2) -- node[below right, label] {Delayed $\tau_3(Q_3)$} (dst);
    
    % Feedback loop
    \coordinate (bus) at ([xshift=-1.5cm]r0.west);
    \draw[arrow, dashed, draw=red!80] (r0.west) -- (bus) |- node[pos=0.85, left, label] {Delayed State\\$Q_2(t-\tau_t)$} (ctrl.west);
    \draw[dashed, draw=red!80] ([yshift=0.15cm]r1.west) -- ([yshift=0.15cm]r1.west -| bus);
    \draw[dashed, draw=red!80] (r2.west) -- (r2.west -| bus);
    
    \draw[arrow, draw=blue!80] (ctrl.east) -| ++(1.0, 1.5) |- node[pos=0.8, above right, label] {Action $a_t$\\Routing Weights} (src.south);
    
\end{tikzpicture}
\end{document}
"""

def build_pdf(name, content):
    build_dir = "./tikz_build"
    os.makedirs(build_dir, exist_ok=True)
    tex_path = os.path.join(build_dir, f"{name}.tex")
    
    with open(tex_path, "w") as f:
        f.write(content)
        
    print(f"Compiling {name}.tex with tectonic...")
    try:
        subprocess.run(["tectonic", f"{name}.tex"], check=True, cwd=build_dir)
        pdf_src = os.path.join(build_dir, f"{name}.pdf")
        
        pdf_dest_paper = f"./paper/images/{name}.pdf"
        os.makedirs("./paper/images", exist_ok=True)
        shutil.copy(pdf_src, pdf_dest_paper)
        
        pdf_dest_jair = f"./JAIR_Manuscript/images/{name}.pdf"
        os.makedirs("./JAIR_Manuscript/images", exist_ok=True)
        shutil.copy(pdf_src, pdf_dest_jair)
        
        print(f"Successfully compiled and copied to destinations")
    except Exception as e:
        print(f"Error compiling {name}.tex: {e}")

if __name__ == "__main__":
    build_pdf("tikz_timeline", create_tikz1_content())
    build_pdf("tikz_architecture", create_tikz2_content())
    build_pdf("tikz_locomotion_loop", create_tikz3_content())
    build_pdf("tikz_network_topology", create_tikz4_content())
