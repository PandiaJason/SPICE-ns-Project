"""
generate_data.py  –  Mission profile and ground-truth data generation.
Writes JSON files to ./simulation/data/.
"""

import json, os, numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Physical constants (never hardcoded in simulation classes) ────────────────
MU_MARS   = 4.2828e13          # m³/s²
MU_EARTH  = 3.986004418e14     # m³/s²
MU_MOON   = 4.9048695e12       # m³/s²
R_MARS    = 3_389_500.0        # m
R_EARTH   = 6_371_000.0        # m
C_LIGHT   = 299_792_458.0      # m/s
FREQ_X    = 8.4e9              # Hz
BOLTZMANN = 1.380649e-23       # J/K
DSN_DIAM  = 34.0               # m
TX_POWER  = 25.0               # W

def _kepler_solve(M, e, iterations=60):
    E = M.copy()
    for _ in range(iterations):
        E = M + e * np.sin(E)
    return E

def _true_anomaly(E, e):
    return 2 * np.arctan2(np.sqrt(1+e)*np.sin(E/2), np.sqrt(1-e)*np.cos(E/2))


# ── Profile 1: Mars occultation / MRO-like ───────────────────────────────────
def gen_mars():
    a = R_MARS + 317_000.0
    e = 0.0093
    T = 2*np.pi*np.sqrt(a**3/MU_MARS)
    t = np.linspace(0, 3*T, 3000)
    nu = 2*np.pi*t/T                          # nearly circular → M≈nu
    r  = a*(1-e**2)/(1+e*np.cos(nu))
    x, y = r*np.cos(nu), r*np.sin(nu)

    occ_ha = np.arcsin(R_MARS/a)
    delta  = np.abs(np.mod(nu-np.pi+np.pi,2*np.pi)-np.pi)
    los    = (delta > occ_ha*1.15).astype(int)
    atten  = np.where((delta>occ_ha)&(delta<occ_ha*1.25),
                      10*(1-(delta-occ_ha)/(0.25*occ_ha)), 0.0)

    em = 1.5*1.496e11
    fspl = 20*np.log10(4*np.pi*em*FREQ_X/C_LIGHT)

    events = []
    in_occ = False
    for i,f in enumerate(los):
        if f==0 and not in_occ: events.append({"type":"ingress","time_s":float(t[i]),"r_m":float(r[i])}); in_occ=True
        elif f==1 and in_occ:   events.append({"type":"egress","time_s":float(t[i]),"r_m":float(r[i])}); in_occ=False

    return {
        "mission":"MRO-like Mars Polar Orbiter",
        "constants":{"mu_mars":MU_MARS,"R_mars":R_MARS,"a_m":a,"e":e,"period_s":T,
                     "c_light":C_LIGHT,"freq_x":FREQ_X,"dsn_diam":DSN_DIAM,"tx_power":TX_POWER,
                     "earth_mars_m":em,"fspl_xband_dB":fspl},
        "simulation":{"t_span_s":3*T,"n_truth":3000,"occ_ha_rad":occ_ha},
        "ground_truth":{"t_s":t.tolist(),"r_m":r.tolist(),"x_m":x.tolist(),"y_m":y.tolist(),
                        "los":los.tolist(),"atmo_dB":atten.tolist(),"events":events},
        "network":{"bitrate_nominal":2_000_000,"bitrate_degraded":100_000,
                   "mtu_bytes":1024,"buffer_bytes":50_000_000,"protocol":"CCSDS/SLE",
                   "rtt_s":2*em/C_LIGHT}
    }


# ── Profile 2: Eccentric Doppler/SNR ────────────────────────────────────────
def gen_elliptical():
    a, e = 26_560_000.0, 0.72
    T = 2*np.pi*np.sqrt(a**3/MU_EARTH)
    t = np.linspace(0, 1.5*T, 4000)
    E = _kepler_solve(2*np.pi*t/T, e)
    nu = _true_anomaly(E, e)
    r  = a*(1-e**2)/(1+e*np.cos(nu))
    x, y = r*np.cos(nu), r*np.sin(nu)
    v  = np.sqrt(MU_EARTH*(2/r-1/a))
    vr = np.sqrt(MU_EARTH/(a*(1-e**2)))*e*np.sin(nu)
    dop = -FREQ_X*vr/C_LIGHT
    fspl= 20*np.log10(4*np.pi*r*FREQ_X/C_LIGHT)
    rx  = 10*np.log10(TX_POWER)-fspl+20*np.log10(np.pi*DSN_DIAM/(C_LIGHT/FREQ_X))
    noise = 10*np.log10(BOLTZMANN*30.0*20e6)
    snr = rx-noise
    br  = np.clip(20e6*np.log2(1+10**(snr/10))/40, 1e3, 20e6)
    return {
        "mission":"Highly Eccentric Relay (Molniya-class)",
        "constants":{"mu_earth":MU_EARTH,"a_m":a,"e":e,"period_s":T,
                     "freq_x":FREQ_X,"dsn_diam":DSN_DIAM,"tx_power":TX_POWER},
        "simulation":{"t_span_s":1.5*T,"n_truth":4000},
        "ground_truth":{"t_s":t.tolist(),"r_m":r.tolist(),"x_m":x.tolist(),"y_m":y.tolist(),
                        "v_ms":v.tolist(),"vr_ms":vr.tolist(),"doppler_hz":dop.tolist(),
                        "snr_dB":snr.tolist(),"bitrate_bps":br.tolist()},
        "network":{"bitrate_nominal":10_000_000,"bitrate_min":1_000,"bitrate_max":20_000_000,
                   "mtu_bytes":4096,"buffer_bytes":200_000_000,"protocol":"CCSDS/DTN-BP"}
    }


# ── Profile 3: Cislunar NRHO / DTN ──────────────────────────────────────────
def gen_cislunar():
    T, a, e = 6.5628*86400, 70_000_000.0, 0.823
    t = np.linspace(0, 2*T, 5000)
    E = _kepler_solve(2*np.pi*t/T, e)
    nu= _true_anomaly(E, e)
    r = a*(1-e**2)/(1+e*np.cos(nu))
    x, y = r*np.cos(nu), r*np.sin(nu)
    d_moon = 384_400_000.0
    dist_e = np.sqrt((x-d_moon)**2+y**2)
    owlt   = dist_e/C_LIGHT

    rng = np.random.default_rng(42)
    contact = np.ones(5000,dtype=int)
    for orb in range(2):
        for _ in range(4):
            s=int((orb*2500)+rng.uniform(0.05,0.85)*2500)
            l=int(rng.uniform(0.03,0.09)*2500)
            contact[s:min(5000,s+l)]=0

    dt_s = 2*T/5000
    buf  = np.zeros(5000)
    for i in range(1,5000):
        inf = 500_000*dt_s/8
        out = 2_000_000*dt_s/8 if contact[i] else 0.0
        buf[i] = max(0.0, buf[i-1]+inf-out)

    custody=[]
    for i in range(1,5000):
        if contact[i]==1 and contact[i-1]==0 and buf[i]>1e6:
            custody.append({"time_s":float(t[i]),"buffer_bytes":float(buf[i]),"owlt_s":float(owlt[i])})

    nodes = list(range(3,31,3))
    return {
        "mission":"Lunar Gateway NRHO – DTN Bundle Protocol",
        "constants":{"mu_moon":MU_MOON,"mu_earth":MU_EARTH,"d_moon_m":d_moon,
                     "a_nrho_m":a,"e_nrho":e,"T_nrho_s":T,"c_light":C_LIGHT},
        "simulation":{"t_span_s":2*T,"n_truth":5000,"node_counts":nodes},
        "ground_truth":{"t_s":t.tolist(),"r_m":r.tolist(),"x_m":x.tolist(),"y_m":y.tolist(),
                        "dist_earth_m":dist_e.tolist(),"contact":contact.tolist(),
                        "owlt_s":owlt.tolist(),"buffer_bytes":buf.tolist(),"custody":custody},
        "network":{"bitrate_nominal":2_000_000,"buffer_bytes":500_000_000,
                   "protocol":"DTN-BP (RFC 5050)","custody_timeout_s":3600,"nodes":nodes}
    }


# ── Horizons-style reference ─────────────────────────────────────────────────
def gen_horizons_ref():
    a, e, mu = R_MARS+317_000.0, 0.0093, MU_MARS
    T = 2*np.pi*np.sqrt(a**3/mu)
    t = np.linspace(0, 3*T, 500)
    E = _kepler_solve(2*np.pi*t/T, e)
    nu= _true_anomaly(E, e)
    r = a*(1-e**2)/(1+e*np.cos(nu))
    return {"source":"Simulated NASA Horizons Reference (two-body Kepler)",
            "units":{"t":"s","r":"m","x":"m","y":"m"},
            "data":{"t_s":t.tolist(),"r_m":r.tolist(),
                    "x_m":(r*np.cos(nu)).tolist(),"y_m":(r*np.sin(nu)).tolist()}}


if __name__ == "__main__":
    for name, fn in [("mars_occultation_profile.json", gen_mars),
                     ("elliptical_doppler_profile.json", gen_elliptical),
                     ("cislunar_nrho_profile.json", gen_cislunar),
                     ("horizons_reference.json", gen_horizons_ref)]:
        data = fn()
        path = os.path.join(DATA_DIR, name)
        with open(path,"w") as f: json.dump(data, f, indent=2)
        print(f"  ✓ {name}")
    print("Done – all profiles written to ./simulation/data/")
