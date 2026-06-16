import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configure matplotlib
plt.rcParams.update({
    'mathtext.fontset': 'stix',
    'font.family': 'STIXGeneral',
    'font.size': 11
})

fig, ax = plt.subplots(figsize=(10.5, 7.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis('off')

# 1. Mothership Block
rect_mother = patches.FancyBboxPatch((3.0, 6.8), 4.0, 0.9, boxstyle="round,pad=0.1",
                                    facecolor='#e1e8f5', edgecolor='#1f77b4', linewidth=2)
ax.add_patch(rect_mother)
ax.text(5.0, 7.25, "MOTHERSHIP SEGMENT\nHigh-Altitude Master Orbiter\n(Rubidium Atomic Clock Standard)", 
        ha='center', va='center', fontweight='bold', color='#1f77b4', fontsize=11)

# 2. Swarm Block
rect_swarm = patches.FancyBboxPatch((3.0, 4.5), 4.0, 1.2, boxstyle="round,pad=0.1",
                                   facecolor='#e2f0d9', edgecolor='#385723', linewidth=2)
ax.add_patch(rect_swarm)
ax.text(5.0, 5.1, "LMO SMALLSAT SWARM\n6x SmallSats in 3 Planes (350 km)\nOnboard Chip-Scale Atomic Clocks (CSAC)\nDual-Band Software-Defined Radios (SDR)", 
        ha='center', va='center', fontweight='bold', color='#385723', fontsize=10)

# 3. Dust Storm Block (Martian Atmosphere)
rect_dust = patches.Rectangle((1.0, 2.3), 8.0, 1.4, hatch='//', 
                             facecolor='#fce4d6', edgecolor='#c65911', alpha=0.75, linewidth=1.5)
ax.add_patch(rect_dust)
ax.text(5.0, 3.0, "MARTIAN DUST STORM ENVIRONMENT\nSuspended Iron-Oxide ($Fe_2O_3$) Dust Particles ($1-5 \ \mu$m)\nSevere S-Band (2.4 GHz) Scattering / UHF (433 MHz) Penetration", 
        ha='center', va='center', color='#c65911', fontweight='bold', fontsize=11)

# 4. Surface Segment Block
rect_rover = patches.FancyBboxPatch((3.0, 0.3), 4.0, 1.1, boxstyle="round,pad=0.1",
                                   facecolor='#fff2cc', edgecolor='#b25900', linewidth=2)
ax.add_patch(rect_rover)
ax.text(5.0, 0.85, "SURFACE EXPLORATION SEGMENT\nMartian Rover (7-State EKF PNT Receiver)\nDistributed IoT Sensor Node Grid", 
        ha='center', va='center', fontweight='bold', color='#b25900', fontsize=11)

# --- CONNECTIONS & ANNOTATIONS ---

# Arrow 1: Mothership to Swarm (MARS Sync)
ax.annotate("", xy=(5.0, 5.8), xytext=(5.0, 6.7),
            arrowprops=dict(arrowstyle="->", color='#1f77b4', lw=2, ls='--'))
ax.text(5.1, 6.25, "Mothership Asymmetric Relational Sync (MARS)\n[Periodic 1-ns Time Calibration Beacons]", 
        ha='left', va='center', color='#1f77b4', fontsize=9)

# Arrow 2: Swarm to Ground (Clear Weather - S-band)
ax.annotate("", xy=(2.0, 1.5), xytext=(3.0, 4.6),
            arrowprops=dict(arrowstyle="->", color='#2ca02c', lw=2))
ax.text(1.2, 2.1, "Clear Weather Link\nS-Band (2.4 GHz)\nHigh-Precision Tracking\n(RMSE < 8 m)", 
        ha='center', va='center', color='#2ca02c', fontsize=9)

# Arrow 3: Swarm to Storm (S-band Attenuated)
ax.annotate("", xy=(4.2, 2.8), xytext=(4.2, 4.4),
            arrowprops=dict(arrowstyle="-|>", color='red', lw=2, ls=':'))
ax.text(4.1, 3.8, "S-Band (2.4 GHz)\nBlocked / Attenuated\n(-18.5 dB Loss)", 
        ha='right', va='center', color='red', fontsize=9)

# Arrow 4: Swarm to Ground through Storm (UHF LoRa Fallback)
ax.annotate("", xy=(5.8, 1.5), xytext=(5.8, 4.4),
            arrowprops=dict(arrowstyle="->", color='#7030a0', lw=2.5))
ax.text(5.9, 1.9, "UHF LoRa Fallback (433 MHz)\nChirp Spread Spectrum (CSS)\nPenetrates Dust Storm\n(RMSE < 15 m)", 
        ha='left', va='center', color='#7030a0', fontsize=9)

plt.tight_layout()
os.makedirs('../paper', exist_ok=True)
plt.savefig('../paper/system_diagram.png', dpi=300, bbox_inches='tight')
plt.close()
print("System diagram saved successfully to paper/system_diagram.png")
