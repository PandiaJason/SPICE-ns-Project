"""
generate_figures.py  –  Publication-quality grouped figure generation (300 DPI).
9 individual plots consolidated into 6 grouped panels.

Panel layout:
  fig1_perf_panel.png      → CPU time (bar) | Scalability (line)          [1×2]
  fig2_temporal_panel.png  → DT adaptation  | DTN buffer (2-row)          [GridSpec]
  fig3_accuracy_panel.png  → Pareto         | Error breakdown (bar)       [1×2]
  fig4_error_timeseries.png→ Per-step ε_pos across 3 profiles             [1×3]
  fig5_cumulative_error.png→ Cumulative error growth across 3 profiles     [1×3]
  fig6_error_heatmap.png   → Relative error | Speedup heatmaps            [1×2]
"""

import os, shutil, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.abspath(__file__))
OUT_DIR   = os.path.join(ROOT, "outputs")
GRAPH_DIR = os.path.join(ROOT, "graphs")
IMG_DIR   = os.path.join(ROOT, "..", "paper", "images")
DATA_DIR  = os.path.join(ROOT, "data")
os.makedirs(GRAPH_DIR, exist_ok=True)
os.makedirs(IMG_DIR,   exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
PALETTE = {
    "Fixed":       "#E63946",
    "EventDriven": "#457B9D",
    "Adaptive":    "#2A9D8F",
}
LINES    = {"Fixed": "-",  "EventDriven": "--", "Adaptive": "-."}
MARKERS  = {"Fixed": "o",  "EventDriven": "s",  "Adaptive": "^"}
PROFILES = ["Mars", "Elliptical", "Cislunar"]
ENGINES  = ["Fixed", "EventDriven", "Adaptive"]
COLORS_P = {"Mars": "#264653", "Elliptical": "#E9C46A", "Cislunar": "#E76F51"}

plt.rcParams.update({
    "font.family":       "DejaVu Serif",
    "font.size":         10,
    "axes.titlesize":    11,
    "axes.labelsize":    10,
    "legend.fontsize":   8,
    "xtick.labelsize":   8.5,
    "ytick.labelsize":   8.5,
    "axes.grid":         True,
    "grid.alpha":        0.30,
    "grid.linestyle":    ":",
    "figure.dpi":        100,
    "savefig.dpi":       300,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

DPI = 300


def save(fig, name_base):
    for ext in [".png", ".pdf"]:
        name = name_base + ext
        path_g = os.path.join(GRAPH_DIR, name)
        path_p = os.path.join(IMG_DIR,   name)
        fig.savefig(path_g, dpi=DPI, bbox_inches="tight")
        shutil.copy(path_g, path_p)
    plt.close(fig)
    print(f"  ✓ {name_base} (.png, .pdf)")


# ─── Panel helpers ─────────────────────────────────────────────────────────────
def _engine_legend(ax, loc="upper right"):
    handles = [Line2D([0], [0], color=PALETTE[e], ls=LINES[e], lw=2,
                      marker=MARKERS[e], ms=6, label=e) for e in ENGINES]
    ax.legend(handles=handles, title="Engine", loc=loc, framealpha=0.85)


def _label(ax, letter, x=-0.12, y=1.04):
    """Panel letter label (a), (b), (c)…"""
    ax.text(x, y, letter, transform=ax.transAxes,
            fontsize=13, fontweight="bold", va="top")


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 1 — Computational Performance Panel  [1×2]
#   Left:  CPU wall-clock time grouped bar chart
#   Right: Scalability (wall time vs. node count)
# ═══════════════════════════════════════════════════════════════════════════════
def fig_perf_panel():
    df_m = pd.read_csv(os.path.join(OUT_DIR, "simulation_metrics.csv"))
    df_s = pd.read_csv(os.path.join(OUT_DIR, "scalability_metrics.csv"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Figure 1 — Computational Performance: CPU Execution Time and Scalability",
        fontsize=12, fontweight="bold", y=1.01)

    # ── (a) CPU Time grouped bar ──────────────────────────────────────────────
    x = np.arange(len(PROFILES))
    w = 0.25
    for i, eng in enumerate(ENGINES):
        vals = [df_m[(df_m.Profile == p) & (df_m.Engine == eng)]["WallTime_s"].values[0]
                for p in PROFILES]
        bars = ax1.bar(x + (i - 1) * w, vals, w, label=eng,
                       color=PALETTE[eng], edgecolor="white", lw=0.7, alpha=0.88)
        for bar, v in zip(bars, vals):
            ax1.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.002,
                     f"{v:.3f}s", ha="center", va="bottom", fontsize=7)
    ax1.set_xticks(x); ax1.set_xticklabels(PROFILES)
    ax1.set_xlabel("Mission Profile")
    ax1.set_ylabel("Wall-Clock CPU Time (s)")
    ax1.set_title("(a) CPU Execution Time by Engine and Profile")
    ax1.legend(title="Engine", framealpha=0.85, fontsize=8)
    _label(ax1, "(a)")

    # ── (b) Scalability ───────────────────────────────────────────────────────
    nodes   = df_s["Nodes"].values
    times   = df_s["WallTime_s"].values
    t0, n0  = times[0], nodes[0]
    ax2.plot(nodes, times, "^-", color=PALETTE["Adaptive"], lw=2,
             ms=7, label="Adaptive engine (measured)")
    ax2.plot(nodes, t0 * nodes / n0, "--", color="#457B9D",
             lw=1.5, alpha=0.75, label=r"$O(N)$ reference")
    ax2.plot(nodes, t0 * (nodes / n0) ** 2, ":", color="#E63946",
             lw=1.5, alpha=0.75, label=r"$O(N^2)$ reference")
    ax2.set_xlabel("Number of Spacecraft Nodes")
    ax2.set_ylabel("Wall-Clock CPU Time (s)")
    ax2.set_title("(b) Scalability: CPU Time vs. Node Count")
    ax2.legend(framealpha=0.85, fontsize=8)
    _label(ax2, "(b)")

    fig.tight_layout()
    save(fig, "fig1_perf_panel")


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 2 — Temporal Dynamics Panel  [GridSpec 2×2]
#   Left (full height):  Adaptive dt sequence vs. orbital range (Mars)
#   Right-top:           DTN buffer occupancy (Cislunar)
#   Right-bottom:        Link availability timeline
# ═══════════════════════════════════════════════════════════════════════════════
def fig_temporal_panel():
    dt_df  = pd.read_csv(os.path.join(OUT_DIR, "adaptive_dt_sequence_mars.csv"))
    buf_df = pd.read_csv(os.path.join(OUT_DIR, "buffer_sequence_cislunar.csv"))

    with open(os.path.join(DATA_DIR, "mars_occultation_profile.json")) as f:
        mars_prof = json.load(f)
    with open(os.path.join(DATA_DIR, "cislunar_nrho_profile.json")) as f:
        cis_prof  = json.load(f)

    gt_m = mars_prof["ground_truth"]
    t_m  = np.array(gt_m["t_s"])
    r_m  = np.array(gt_m["r_m"]) / 1e6   # Mm
    evts = gt_m["events"]

    gt_c      = cis_prof["ground_truth"]
    t_c       = np.array(gt_c["t_s"]) / 86400
    contact   = np.array(gt_c["contact"])
    buf_gt    = np.array(gt_c["buffer_bytes"]) / 1e6
    custody   = gt_c["custody"]
    t_buf     = buf_df["t_s"].values / 86400
    b_buf     = buf_df["buf_bytes"].values / 1e6

    fig = plt.figure(figsize=(15, 8))
    fig.suptitle(
        "Figure 2 — Temporal Dynamics: Adaptive Step Sizing (Mars) and DTN Buffer Evolution (Cislunar)",
        fontsize=12, fontweight="bold", y=0.96)

    gs = gridspec.GridSpec(2, 2, figure=fig,
                           height_ratios=[1.2, 1], hspace=0.35, wspace=0.25)

    # ── (a) DT adaptation (top row, spans both columns for long x scale) ──────
    ax_dt  = fig.add_subplot(gs[0, :])
    ax_dt2 = ax_dt.twinx()

    ax_dt.plot(t_m / 3600, r_m, color="#264653", lw=1.8, label="Orbital Range (Mm)")
    ax_dt2.semilogy(dt_df["t_s"] / 3600, dt_df["dt_s"],
                    color=PALETTE["Adaptive"], lw=1.2, ls="-.", alpha=0.85,
                    label="Adaptive dt (s)")

    in_occ = False; t_in = 0; first_occ = True
    for ev in evts:
        if ev["type"] == "ingress":
            t_in = ev["time_s"] / 3600; in_occ = True
        elif ev["type"] == "egress" and in_occ:
            lbl = "Occultation" if first_occ else ""
            ax_dt.axvspan(t_in, ev["time_s"] / 3600,
                          alpha=0.13, color="#E63946", label=lbl)
            in_occ = False; first_occ = False

    ax_dt.set_xlabel("Simulation Time (h)")
    ax_dt.set_ylabel("Spacecraft Range from Mars (Mm)", color="#264653")
    ax_dt2.set_ylabel("Adaptive Step Size dt (s)  [log]", color=PALETTE["Adaptive"])
    ax_dt.tick_params(axis="y", labelcolor="#264653")
    ax_dt2.tick_params(axis="y", labelcolor=PALETTE["Adaptive"])
    ax_dt.set_title("(a) Adaptive dt Sequence — Mars Occultation Profile")
    lines1, lbl1 = ax_dt.get_legend_handles_labels()
    lines2, lbl2 = ax_dt2.get_legend_handles_labels()
    ax_dt.legend(lines1 + lines2, lbl1 + lbl2, loc="upper right",
                 framealpha=0.85, fontsize=8)
    _label(ax_dt, "(a)", x=-0.15)

    # ── (b) DTN buffer occupancy (bottom-left) ────────────────────────────────
    ax_buf = fig.add_subplot(gs[1, 0])
    ax_buf.fill_between(t_buf, b_buf, alpha=0.30, color=PALETTE["Adaptive"])
    ax_buf.plot(t_buf, b_buf, color=PALETTE["Adaptive"], lw=1.5,
                label="Buffer (Adaptive sim)")
    ax_buf.plot(t_c, buf_gt, color="#264653", lw=1.2, ls="--",
                alpha=0.7, label="Buffer (Ground truth)")
    for ev in custody:
        ax_buf.axvline(ev["time_s"] / 86400, color="#E63946",
                       lw=0.9, ls=":", alpha=0.7)
    ax_buf.axvline(custody[0]["time_s"] / 86400, color="#E63946",
                   lw=0.9, ls=":", label="Custody transfer")
    ax_buf.set_ylabel("Buffer Occupancy (MB)")
    ax_buf.set_xlabel("Simulation Time (days)")
    ax_buf.set_title("(b) DTN Buffer Dynamics — Cislunar NRHO")
    ax_buf.legend(loc="upper right", framealpha=0.85, fontsize=8)
    _label(ax_buf, "(b)", x=-0.15)

    # ── (c) Link timeline (bottom-right) ──────────────────────────────────────
    ax_lnk = fig.add_subplot(gs[1, 1])
    ax_lnk.fill_between(t_c, contact, step="post",
                         alpha=0.55, color=PALETTE["EventDriven"])
    ax_lnk.set_ylabel("Link Up")
    ax_lnk.set_yticks([0, 1]); ax_lnk.set_yticklabels(["No", "Yes"])
    ax_lnk.set_xlabel("Simulation Time (days)")

    save(fig, "fig2_temporal_panel")


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 3 — Accuracy–Efficiency Panel  [1×2]
#   Left:  Pareto frontier (steps vs. position error)
#   Right: Normalised error breakdown (stacked bar)
# ═══════════════════════════════════════════════════════════════════════════════
def fig_accuracy_panel():
    df_m = pd.read_csv(os.path.join(OUT_DIR, "simulation_metrics.csv"))
    df_p = pd.read_csv(os.path.join(OUT_DIR, "pareto_data.csv"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Figure 3 — Accuracy–Efficiency Trade-offs: Pareto Frontier and Normalised Error Breakdown",
        fontsize=12, fontweight="bold", y=1.01)

    # ── (a) Pareto frontier ───────────────────────────────────────────────────
    for eng in ENGINES:
        sub = df_p[df_p.Engine == eng].sort_values("Steps")
        ax1.plot(sub["Steps"], sub["PosError_m"],
                 LINES[eng], color=PALETTE[eng], lw=1.6, alpha=0.75, label=eng)
        for _, row in df_p[df_p.Engine == eng].iterrows():
            ax1.scatter(row["Steps"], row["PosError_m"],
                        marker=MARKERS[eng], s=80,
                        color=COLORS_P[row["Profile"]],
                        edgecolors=PALETTE[eng], linewidth=1.4, zorder=5)

    legend_eng  = [Line2D([0], [0], color=PALETTE[e], ls=LINES[e],
                          lw=2, marker=MARKERS[e], ms=6) for e in ENGINES]
    legend_prof = [Line2D([0], [0], marker="o", color="w",
                          markerfacecolor=COLORS_P[p],
                          markersize=9) for p in PROFILES]
    leg1 = ax1.legend(legend_eng, ENGINES, title="Engine",
                      loc="upper left", framealpha=0.85, fontsize=8)
    ax1.add_artist(leg1)
    ax1.legend(legend_prof, PROFILES, title="Profile",
               loc="lower right", framealpha=0.85, fontsize=8)
    ax1.set_xlabel("Total Simulation Steps")
    ax1.set_ylabel(r"Cumulative Position Error $\epsilon_{pos}$ (m)")
    ax1.set_title("(a) Pareto Frontier: Accuracy vs. Computational Cost")
    _label(ax1, "(a)")

    # ── (b) Normalised error breakdown stacked bar ────────────────────────────
    def norm_col(col):
        vals = []
        for prof in PROFILES:
            base = df_m[(df_m.Profile == prof) &
                        (df_m.Engine == "Fixed")][col].values[0]
            for eng in ENGINES:
                row = df_m[(df_m.Profile == prof) & (df_m.Engine == eng)]
                v   = row[col].values[0] if not row.empty else 0
                vals.append(v / max(base, 1e-12))
        return vals

    n_pos  = norm_col("PosError_m")
    n_evt  = norm_col("EventError_ms")
    
    # Introduce a gap between the profile groups
    # Group 1 (Mars): 0, 1, 2 | Group 2 (Elliptical): 4, 5, 6 | Group 3 (Cislunar): 8, 9, 10
    x      = [0, 1, 2, 4, 5, 6, 8, 9, 10]
    cols   = [PALETTE[e] for _ in PROFILES for e in ENGINES]

    ax2.bar(x, n_pos, color=cols, alpha=0.78, edgecolor="white", lw=0.6)
    ax2.bar(x, n_evt, bottom=n_pos, color=cols, alpha=0.42,
            edgecolor="white", lw=0.6, hatch="//")
    ax2.axhline(1.0, color="gray", lw=1.2, ls="--", alpha=0.7)
    
    # Place a single group label in the middle of each profile's bars
    ax2.set_xticks([1, 5, 9])
    ax2.set_xticklabels(PROFILES, fontsize=9, rotation=0, ha="center")
    ax2.set_ylabel("Error normalised to Fixed-Step = 1.0")
    ax2.set_title("(b) Normalised Error Breakdown by Engine and Profile")
    patches = [Patch(facecolor=PALETTE[e], label=e) for e in ENGINES]
    patches += [Patch(facecolor="gray", alpha=0.4, hatch="//",
                      label="Event timestamp error")]
    ax2.legend(handles=patches, fontsize=8, framealpha=0.85, loc="upper right")
    ax2.text(len(x) * 0.35, 1.05, "Fixed baseline", fontsize=7.5,
             color="gray", style="italic")
    _label(ax2, "(b)")

    fig.tight_layout()
    save(fig, "fig3_accuracy_panel")


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 4 — Per-Step Position Error Time Series  [1×3]
# ═══════════════════════════════════════════════════════════════════════════════
def fig_error_timeseries():
    t_divs  = [3600, 3600, 86400]
    t_units = ["h",  "h",  "days"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        r"Figure 4 — Per-Step Position Error $\epsilon_{pos}(t)$ vs. Simulation Time",
        fontsize=12, fontweight="bold", y=1.01)

    for ax, prof, tdiv, tunit in zip(axes, PROFILES, t_divs, t_units):
        for eng in ENGINES:
            fpath = os.path.join(OUT_DIR,
                        f"error_seq_{prof.lower()}_{eng.lower()}.csv")
            if not os.path.exists(fpath):
                continue
            df = pd.read_csv(fpath)
            ax.semilogy(df["t_s"].values / tdiv,
                        df["pos_err_m"].values + 1.0,
                        color=PALETTE[eng], ls=LINES[eng],
                        lw=1.4, alpha=0.85, label=eng)
        ax.set_title(f"({chr(96 + PROFILES.index(prof) + 1)}) {prof}")
        ax.set_xlabel(f"Time ({tunit})")
        ax.set_ylabel("Position Error (m) — log scale")
        _engine_legend(ax, loc="upper right")
        _label(ax, f"({chr(96 + PROFILES.index(prof) + 1)})")

    fig.tight_layout()
    save(fig, "fig4_error_timeseries")


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 5 — Cumulative Position Error Growth  [1×3]
# ═══════════════════════════════════════════════════════════════════════════════
def fig_cumulative_error():
    t_divs  = [3600, 3600, 86400]
    t_units = ["h",  "h",  "days"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        "Figure 5 — Cumulative Integrated Position Error Growth",
        fontsize=12, fontweight="bold", y=1.01)

    for ax, prof, tdiv, tunit in zip(axes, PROFILES, t_divs, t_units):
        for eng in ENGINES:
            fpath = os.path.join(OUT_DIR,
                        f"error_seq_{prof.lower()}_{eng.lower()}.csv")
            if not os.path.exists(fpath):
                continue
            df = pd.read_csv(fpath)
            t  = df["t_s"].values / tdiv
            c  = df["cum_err_m"].values
            ax.plot(t, c / 1e3, color=PALETTE[eng], ls=LINES[eng],
                    lw=1.8, alpha=0.88, label=eng)
            ax.annotate(f"{c[-1]/1e3:.0f} km",
                        xy=(t[-1], c[-1] / 1e3),
                        xytext=(-32, 8), textcoords="offset points",
                        fontsize=6.5, color=PALETTE[eng],
                        arrowprops=dict(arrowstyle="-", color=PALETTE[eng],
                                        lw=0.6))
        ax.set_title(f"({chr(96 + PROFILES.index(prof) + 1)}) {prof}")
        ax.set_xlabel(f"Time ({tunit})")
        ax.set_ylabel("Cumulative Error (km)")
        _engine_legend(ax, loc="upper left")
        _label(ax, f"({chr(96 + PROFILES.index(prof) + 1)})")

    fig.tight_layout()
    save(fig, "fig5_cumulative_error")


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 6 — Summary Error & Speedup Heatmap  [1×2]
# ═══════════════════════════════════════════════════════════════════════════════
def fig_error_heatmap():
    df = pd.read_csv(os.path.join(OUT_DIR, "simulation_metrics.csv"))

    pos_mat = np.zeros((len(ENGINES), len(PROFILES)))
    spd_mat = np.zeros((len(ENGINES), len(PROFILES)))

    for j, prof in enumerate(PROFILES):
        base_err = df[(df.Profile == prof) &
                      (df.Engine == "Fixed")]["PosError_m"].values[0]
        for i, eng in enumerate(ENGINES):
            row = df[(df.Profile == prof) & (df.Engine == eng)]
            if row.empty: continue
            pos_mat[i, j] = row["PosError_m"].values[0] / max(base_err, 1)
            spd_mat[i, j] = row["Speedup"].values[0]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle(
        "Figure 6 — Error and Speedup Heatmap: Engine × Profile Summary",
        fontsize=12, fontweight="bold")

    for ax, mat, cmap, title, fmt in [
        (ax1, pos_mat, "YlOrRd",
         "(a) Relative Position Error\n(normalised to Fixed-Step)",
         "{:.2f}"),
        (ax2, spd_mat, "YlGn",
         "(b) Speedup Factor\n(vs. Fixed-Step baseline)",
         "{:.1f}×"),
    ]:
        im = ax.imshow(mat, cmap=cmap, aspect="auto",
                       vmin=0, vmax=mat.max())
        ax.set_xticks(range(len(PROFILES)))
        ax.set_xticklabels(PROFILES)
        ax.set_yticks(range(len(ENGINES)))
        ax.set_yticklabels(ENGINES)
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        thresh = 0.6 * mat.max()
        for i in range(len(ENGINES)):
            for j in range(len(PROFILES)):
                ax.text(j, i, fmt.format(mat[i, j]),
                        ha="center", va="center", fontsize=10,
                        color="white" if mat[i, j] > thresh else "black")

    fig.tight_layout()
    save(fig, "fig6_error_heatmap")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating publication figures …")
    fig_perf_panel()
    fig_temporal_panel()
    fig_accuracy_panel()
    fig_error_timeseries()
    fig_cumulative_error()
    fig_error_heatmap()
    print(f"\nAll figures saved to {GRAPH_DIR}  and  {IMG_DIR}")
