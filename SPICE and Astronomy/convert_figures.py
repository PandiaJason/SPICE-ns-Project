import os
import subprocess

# Define the 6 TikZ figures exactly as they are currently in paper.tex
figures = {
    1: r"""\begin{tikzpicture}[scale=1.2, >=stealth,
  lbl/.style={draw, fill=blue!5, rounded corners, font=\scriptsize, align=center, thick},
  title/.style={font=\bfseries}]

  % Draw Planet (P)
  \shade[ball color=blue!30!cyan!50, opacity=0.8] (5,0) circle (1.2cm);
  \draw[thick] (5,0) circle (1.2cm);
  \draw[dashed, thin] (5,0) ellipse (1.2cm and 0.4cm);
  \node[below, title] at (5,-1.3) {Planet / Target};
  
  % Draw Spacecraft (S)
  \coordinate (SC) at (0,2);
  \fill[gray!80] (SC) circle (6pt);
  \draw[thick] (SC) circle (6pt);
  % Solar panels
  \draw[thick, fill=blue!50] (-0.8, 1.9) rectangle (-0.2, 2.1);
  \draw[thick, fill=blue!50] (0.2, 1.9) rectangle (0.8, 2.1);
  % Antenna
  \draw[thick] (SC) -- (0, 2.4);
  \draw[thick] (-0.2, 2.4) arc (180:0:0.2);
  \node[above, title] at (0, 2.6) {Spacecraft};

  % Trajectory path (SPK)
  \draw[dashed, ->, orange, thick] (-2, 2.5) to[out=-20, in=180] (SC) to[out=0, in=120] (2, 1);
  \node[orange, above] at (-1.5, 2.3) {Trajectory};

  % Instrument (I) mounting & pointing cone
  \coordinate (Inst) at (0.1, 1.8);
  % Pointing vector / boresight to Planet surface
  \coordinate (TargetPt) at (4.2, 0.4);
  \draw[thick, ->, green!60!black] (SC) -- (TargetPt) node[midway, above right, black, font=\tiny] {Boresight};
  % Field of View (FOV) cone
  \fill[green!20, opacity=0.4] (SC) -- (3.9, 0.9) to[out=-45, in=45] (4.5, -0.1) -- cycle;
  \draw[green!60!black, thin] (SC) -- (3.9, 0.9);
  \draw[green!60!black, thin] (SC) -- (4.5, -0.1);
  \draw[green!60!black, thin] (3.9, 0.9) to[out=-45, in=45] (4.5, -0.1);

  % Acronym Blocks / Annotations
  \node[lbl, fill=red!10] (S_lbl) at (-1.5, 0.8) {{\bf S}pacecraft Position\\{\bf SPK} Kernels};
  \node[lbl, fill=orange!10] (C_lbl) at (-1.5, -0.3) {{\bf C}amera-matrix (Attitude)\\{\bf CK} Kernels};
  \node[lbl, fill=green!10] (I_lbl) at (1.5, 3.6) {{\bf I}nstrument FOV \& Mounting\\{\bf IK} Kernels};
  \node[lbl, fill=cyan!10] (P_lbl) at (5, 2.2) {{\bf P}lanet Position \& Shape\\{\bf SPK, PCK, DSK} Kernels};
  \node[lbl, fill=purple!10] (E_lbl) at (2.2, -1.2) {{\bf E}vents \& Time Support\\{\bf EK, LSK, SCLK} Kernels};

  % Connective lines from labels to graphics
  \draw[->, thin, gray] (S_lbl) to[out=90, in=210] (SC);
  \draw[->, thin, gray] (C_lbl) to[out=90, in=225] (SC);
  \draw[->, thin, gray] (I_lbl) to[out=180, in=45] (SC);
  \draw[->, thin, gray] (P_lbl) to[out=270, in=90] (5, 1.3);
  \draw[->, thin, gray] (E_lbl) to[out=180, in=315] (TargetPt);

\end{tikzpicture}""",

    2: r"""\begin{tikzpicture}[scale=2.5, >=stealth]
  % Draw axes
  \draw[->, gray, thin] (-1.5, 0) -- (1.5, 0) node[right, black] {$x$};
  \draw[->, gray, thin] (0, -1.2) -- (0, 1.2) node[above, black] {$z$};
  
  % Draw ellipse (spheroid outline) with a=1.2, b=0.8
  \draw[thick, blue] (0,0) ellipse (1.2cm and 0.8cm);
  
  % Define point P on the ellipse at angle 45 degrees in parameter t
  % x = a cos(t) = 1.2 * cos(45) = 0.8485
  % z = b sin(t) = 0.8 * sin(45) = 0.5657
  \coordinate (P) at (0.8485, 0.5657);
  
  % Draw position vector r
  \draw[thick, ->, red] (0,0) -- (P) node[midway, above left] {$\mathbf{r}$};
  \fill[red] (P) circle (0.8pt) node[above right, black] {$P(x,y,z)$};
  
  % Draw line for planetocentric latitude angle phi_c
  \draw[dashed, red] (P) -- (0.8485, 0);
  \draw[red, thin] (0.2, 0) arc (0:33.69:0.2);
  \node[red] at (0.35, 0.1) {$\phi_c$};
  
  % Calculate normal vector normal n at P
  % n_x = x/a^2 = 0.8485/1.44 = 0.589
  % n_z = z/b^2 = 0.5657/0.64 = 0.884
  % Normal starts at P and goes to P + (0.3, 0.45) = (1.15, 1.02)
  \coordinate (N_end) at (1.1485, 1.0157);
  \draw[thick, ->, green!60!black] (P) -- (N_end) node[above right] {$\mathbf{n}$};
  
  % Surface normal extended backwards to intersect x-axis
  % Equation of normal line: z - z_p = (n_z/n_x) * (x - x_p)
  % Slope = n_z/n_x = 0.884/0.589 = 1.5
  % Intersection with z=0: x_int = x_p - z_p/1.5 = 0.8485 - 0.5657/1.5 = 0.471
  \coordinate (X_int) at (0.471, 0);
  \draw[dashed, green!60!black] (P) -- (X_int);
  
  % Draw planetographic latitude angle phi_g
  \draw[green!60!black, thin] (0.571, 0) arc (0:56.30:0.1);
  \node[green!60!black] at (0.62, 0.15) {$\phi_g$};
  
  % Bounding box label
  \node[blue, below left] at (1.2, 0) {$a$};
  \node[blue, above left] at (0, 0.8) {$c$};
  
\end{tikzpicture}""",

    3: r"""\begin{tikzpicture}[node distance=1.0cm and 1.5cm, >=stealth, 
  block/.style={rectangle, draw, fill=blue!10, rounded corners, minimum width=2.6cm, minimum height=0.8cm, align=center, thick},
  font=\footnotesize]
  
  % Nodes
  \node[block, fill=yellow!25] (Inertial) at (0,0) {Inertial Frame\\(e.g., J2000, ICRF)};
  
  \node[block, fill=orange!20] (PCK) [above left=of Inertial] {Body-Fixed Frame\\(e.g., IAU\_MARS)};
  \node[block, fill=blue!15] (CK) [above right=of Inertial] {Spacecraft Bus Frame\\(e.g., MRO\_SC)};
  \node[block, fill=green!15] (Topo) [below=of PCK] {Topocentric Frame\\(e.g., DSN Antenna)};
  \node[block, fill=purple!15] (Inst) [above=of CK] {Instrument Frame\\(e.g., HiRISE\_BORESIGHT)};

  % Paths / Edges
  \draw[<->, thick, red] (PCK) -- (Inertial) node[midway, above right, black, font=\tiny, yshift=0.1cm] {PCK (IAU angles)};
  \draw[<->, thick, red] (CK) -- (Inertial) node[midway, above left, black, font=\tiny, yshift=0.1cm] {CK (Quaternions)};
  \draw[<->, thick, blue] (PCK) -- (Topo) node[midway, right, black, font=\tiny] {FK (Static)};
  \draw[<->, thick, blue] (CK) -- (Inst) node[midway, right, black, font=\tiny] {FK/IK (Mounting)};
  
\end{tikzpicture}""",

    4: r"""\begin{tikzpicture}[scale=1.4, >=stealth]

  % Draw background star field representing ICRF
  \foreach \p in {(2.5,2.1), (2.8,1.4), (2.2,0.8), (1.9,2.4), (-2.3,1.8), (-1.8,2.3), (-2.5,0.7), (0.5,2.6), (-0.8,2.5)} {
    \node[gray!40, font=\tiny] at \p {$\star$};
  }
  \foreach \q in {(2.4,1.8), (-2.0,1.2), (1.5,2.5)} {
    \draw[gray!30, fill=gray!30] \q circle (0.04); % Quasar representation
    \node[gray!50, above, font=\tiny] at \q {QSO};
  }

  % Draw Earth at origin
  \shade[ball color=blue!30!cyan!20, opacity=0.7] (0,0) circle (0.5cm);
  \draw[gray!80, thin] (0,0) circle (0.5cm);

  % Draw equatorial plane (slanted ellipse)
  \draw[thick, blue!80!black] (0,0) ellipse (2.2cm and 0.6cm);
  \node[blue!80!black, below, font=\scriptsize] at (1.6,-0.4) {Mean Equatorial Plane (J2000.0)};

  % Draw ecliptic plane (inclined by 23.44 deg)
  \begin{scope}[rotate=23.44]
    \draw[thick, green!60!black, dashed] (0,0) ellipse (2.2cm and 0.6cm);
    \node[green!60!black, above, font=\scriptsize] at (1.4,0.4) {Ecliptic Plane};
  \end{scope}

  % Draw Earth's obliquity angle arc
  \draw[<->, thin] (1.3, -0.15) to[out=60, in=-20] (1.2, 0.4);
  \node[right, font=\tiny] at (1.3, 0.15) {$\epsilon \approx 23.44^\circ$};

  % Reference Frame Axes
  % X-axis: pointing to vernal equinox
  \draw[->, ultra thick, red] (0,0) -- (2.6, 0) node[anchor=west, font=\scriptsize] {$X_{\text{J2000}} \equiv X_{\text{ICRF}}$ (Vernal Equinox $\Upsilon$)};

  % Z-axis: rigid kinematic axis (defined by quasar positions)
  \draw[->, ultra thick, red] (0,0) -- (0, 2.4) node[anchor=south, font=\scriptsize] {$Z_{\text{J2000}} \equiv Z_{\text{ICRF}}$ (Rotation Axis)};

  % Y-axis: completes right-handed system
  \draw[->, ultra thick, red] (0,0) -- (-0.8, -0.45) node[anchor=north east, font=\scriptsize] {$Y_{\text{J2000}} \equiv Y_{\text{ICRF}}$};

  % Illustrate the tiny difference between J2000 and ICRF (exaggerated for visibility)
  \draw[->, blue, thick] (0,0) -- (0.2, 2.36);
  \node[blue, right, font=\tiny] at (0.1, 2.1) {$Z_{\text{J2000}}$ (Actual Pole)};
  \draw[<->, thin, blue] (0,2.25) to[out=10, in=170] (0.19, 2.21);
  \node[above right, blue, font=\tiny] at (0.05, 2.23) {$< 0.1''$ (or $0.02''$)};

\end{tikzpicture}""",

    5: r"""\begin{tikzpicture}[scale=1.5, >=stealth,
  axis/.style={->,thick},
  vector/.style={->,thick,red},
  projection/.style={dashed,blue},
  angle/.style={->,thin,draw=black!70,font=\tiny}]

  % Draw coordinate axes
  \draw[axis] (0,0,0) -- (2.5,0,0) node[anchor=north]{$x$ (Prime Meridian)};
  \draw[axis] (0,0,0) -- (0,2.5,0) node[anchor=south]{$z$ (Rotation Axis)};
  \draw[axis] (0,0,0) -- (0,0,3.5) node[anchor=north east]{$y$};

  % Define Point P
  \coordinate (O) at (0,0,0);
  \coordinate (P) at (0.777, 1.555, 1.347);
  \coordinate (ProjXY) at (0.777, 0, 1.347); % Projection in equatorial plane

  % Draw vector OP
  \draw[vector] (O) -- (P) node[anchor=south west] {$P(x,y,z)$};

  % Draw projections
  \draw[projection] (P) -- (ProjXY);
  \draw[projection] (O) -- (ProjXY);
  \draw[projection] (P) -- (0, 1.555, 0) node[left, black, font=\tiny] {$z$};
  \draw[projection] (ProjXY) -- (0.777, 0, 0) node[below, black, font=\tiny] {$x$};
  \draw[projection] (ProjXY) -- (0, 0, 1.347) node[below left, black, font=\tiny] {$y$};

  % Label range (r)
  \node[red, above left, font=\scriptsize] at (0.35, 0.75, 0.6) {$r$};

  % Label cylindrical radius (rho)
  \node[blue, below right, font=\scriptsize] at (0.4, 0, 0.8) {$\rho$};

  % Draw Angles
  % Longitude (lambda) - in equatorial plane
  \draw[angle] (0.5,0,0) to[out=-20, in=120] (0.3,0,0.5);
  \node[below, font=\scriptsize] at (0.35, 0, 0.25) {$\lambda$};

  % Latitude (phi) - angle from ProjXY to OP
  \draw[angle] (0.6,0,1.0) to[out=90, in=-20] (0.5,0.8,0.8);
  \node[right, font=\scriptsize] at (0.55, 0.45, 0.85) {$\phi$};

  % Co-latitude (theta) - angle from Z axis to OP
  \draw[angle] (0,0.6,0) to[out=0, in=80] (0.3,0.5,0.2);
  \node[above right, font=\scriptsize] at (0.1, 0.65, 0.15) {$\theta$};

\end{tikzpicture}""",

    6: r"""\begin{tikzpicture}[scale=1.5, >=stealth]
  % Spacecraft / Observer at (0,0)
  \coordinate (Obs) at (0,0);
  \fill[gray!80] (Obs) circle (4pt);
  \draw[thick] (Obs) circle (4pt);
  % Solar panels of spacecraft
  \draw[thick, fill=blue!50] (-0.3, -0.05) rectangle (-0.1, 0.05);
  \draw[thick, fill=blue!50] (0.1, -0.05) rectangle (0.3, 0.05);
  \node[below] at (Obs) {Observer (Spacecraft)};
  
  % Observer velocity vector v_obs
  \draw[thick, ->, orange] (Obs) -- (1, 0) node[right] {$\mathbf{v}_{\text{obs}}$};
  
  % Target true position at t_recv
  \coordinate (T_recv) at (4, 2);
  \fill[red!80] (T_recv) circle (3pt);
  \node[above right] at (T_recv) {Target at reception $t_{\text{recv}}$};
  
  % Target true position at t_emit
  \coordinate (T_emit) at (3.5, 1.2);
  \fill[red] (T_emit) circle (3pt);
  \node[below right] at (T_emit) {Target at emission $t_{\text{emit}}$};
  
  % Target motion vector
  \draw[->, thick, red, dashed] (T_emit) -- (T_recv) node[midway, right] {Target Motion};
  
  % Light path from T_emit to Obs
  \draw[thick, ->, yellow!80!orange] (T_emit) -- (Obs) node[midway, above left, black] {Light path ($c$)};
  
  % Apparent direction shifted by Stellar Aberration
  % The velocity of observer is to the right (x direction), which tilts the incoming light vector forward (towards x)
  % Apparent target position is shifted in the direction of v_obs
  \coordinate (T_app) at (3.1, 1.8);
  \draw[thick, ->, green!70!black] (Obs) -- (T_app) node[midway, below right, black] {Apparent pointing $\mathbf{\hat{u}}'$};
  \fill[green!70!black] (T_app) circle (2pt) node[above left] {Apparent Position};
  
  % Pointing shift angle (aberration)
  \draw[green!70!black, thin] (1.5, 0.51) arc (19:35:1.5);
  \node[green!70!black] at (1.8, 0.8) {$\theta_{\text{ab}}$};

\end{tikzpicture}"""
}

# Standard template for standalone compilation of TikZ figures
latex_template = r"""\documentclass[tikz]{{standalone}}
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\usetikzlibrary{{positioning}}
\begin{{document}}
{content}
\end{{document}}
"""

for num, code in figures.items():
    tex_filename = f"fig{num}_standalone.tex"
    pdf_filename = f"fig{num}_standalone.pdf"
    ps_filename = f"fig{num}.ps"
    
    print(f"Creating standalone TeX file for Figure {num}...")
    with open(tex_filename, "w") as f:
        f.write(latex_template.format(content=code))
        
    print(f"Compiling Figure {num} to PDF...")
    # Compile using Tectonic
    result = subprocess.run(["tectonic", tex_filename], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error compiling Figure {num}:")
        print(result.stderr)
        continue
        
    print(f"Converting Figure {num} PDF to PostScript (.ps)...")
    # Convert PDF to high-quality vector PostScript using pdftops -eps
    ps_result = subprocess.run(["pdftops", "-eps", pdf_filename, ps_filename], capture_output=True, text=True)
    if ps_result.returncode != 0:
        print(f"Error converting Figure {num} to PS:")
        print(ps_result.stderr)
        continue
        
    # Save PDF and clean up standalone temp files
    print(f"Saving PDF and cleaning up temp files for Figure {num}...")
    if os.path.exists(pdf_filename):
        os.rename(pdf_filename, f"fig{num}.pdf")
    if os.path.exists(tex_filename):
        os.remove(tex_filename)
            
    print(f"Figure {num} successfully generated as {ps_filename} and fig{num}.pdf!\n")

print("All figures successfully converted to vector PostScript (.ps) format!")
