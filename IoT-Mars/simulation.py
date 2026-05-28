import os
import numpy as np
import pandas as pd

# Ensure results directory exists
os.makedirs("results", exist_ok=True)

# Number of Monte Carlo repetitions for statistical averaging
NUM_RUNS = 30

# --- PHYSICAL CONSTANTS & LORAWAN CONFIGURATIONS ---
from config import *


def get_mars_temperature(sol_hour):
    """Models diurnal temperature cycle on Mars (equatorial to mid-latitude)."""
    t_min = 140.0
    t_max = 280.0
    return t_min + (t_max - t_min) * 0.5 * (1.0 + np.sin((sol_hour - 9) * 2 * np.pi / 24))

def get_tcxo_drift_ppm(temp_k, compensated=False):
    """Models TCXO frequency drift in ppm as a function of temperature."""
    if compensated:
        return 0.5  # Stable < 0.5 ppm
    else:
        temp_c = temp_k - 273.15
        if temp_c < -40:
            return -1.5 - 0.05 * (temp_c + 40)**2
        else:
            return 0.12 * (temp_c - 25) - 0.0003 * (temp_c - 25)**3

def calculate_toa(payload_bytes, sf, bw=125e3, coding_rate=1, implicit_header=False, crc=True, low_data_rate_opt=False):
    """Calculates Time-on-Air (ToA) of a LoRa packet in seconds."""
    t_sym = (2**sf) / bw
    n_preamble = 8
    t_preamble = (n_preamble + 4.25) * t_sym
    
    ih = 1 if implicit_header else 0
    c = 1 if crc else 0
    de = 1 if (low_data_rate_opt or (sf in [11, 12] and bw == 125e3)) else 0
    cr = coding_rate  # 1 corresponding to 4/5 coding rate
    
    payload_terms = 8 * payload_bytes - 4 * sf + 28 + 16 * c - 20 * ih
    payload_sym_num = 8 + max(np.ceil(payload_terms / (4 * (sf - 2 * de))) * (cr + 4), 0)
    
    t_payload = payload_sym_num * t_sym
    return t_preamble + t_payload

class Node:
    def __init__(self, node_id, x, y, is_mars=True):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.distance_to_gw = np.sqrt(x**2 + y**2)
        self.is_mars = is_mars
        self.tx_power = 14.0  # dBm
        self.antenna_gain = 0.0  # dBi
        self.sf = 7
        self.bw = 125e3  # 125 kHz
        self.energy_consumed = 0.0
        self.packets_transmitted = 0
        self.packets_acked = 0
        
    def consume_energy(self, duration_s, mode="tx"):
        if mode == "tx":
            power = 0.120  # Watts (36mA @ 3.3V)
        elif mode == "rx":
            power = 0.036  # Watts (11mA @ 3.3V)
        else:
            power = 3e-6  # Watts (Sleep)
        self.energy_consumed += power * duration_s

class SatelliteConstellation:
    def __init__(self, orbit_alt_km=300):
        self.orbit_alt = orbit_alt_km * 1e3

    def get_path_loss(self, node_distance_surface, carrier_frequency=868e6):
        slant_range = np.sqrt(self.orbit_alt**2 + node_distance_surface**2)
        pl_0 = 20 * np.log10(4 * np.pi * carrier_frequency * 1 / C)
        pl = pl_0 + 20 * np.log10(slant_range) + 0.05
        return pl

class NetworkSimulator:
    def __init__(self, num_nodes, max_distance_km, is_mars=True, scenario="baseline"):
        self.num_nodes = num_nodes
        self.max_distance = max_distance_km * 1e3
        self.is_mars = is_mars
        self.scenario = scenario
        if "proposed" in scenario:
            self.gw_antenna_gain = PROPOSED_SAT_ANTENNA_GAIN if "satellite" in scenario else 4.5
        else:
            self.gw_antenna_gain = 6.0 if "satellite" in scenario else 2.15
        self.dust_storm = False
        self.sol_hour = 12.0
        
        self.nodes = []
        for i in range(num_nodes):
            angle = np.random.uniform(0, 2 * np.pi)
            r = self.max_distance * np.sqrt(np.random.uniform(0.01, 1.0))
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            self.nodes.append(Node(i, x, y, is_mars))
            
        self.sat_constellation = SatelliteConstellation(orbit_alt_km=300)
        
    def set_dust_storm(self, active):
        self.dust_storm = active

    def set_sol_hour(self, hour):
        self.sol_hour = hour

    def run_adr(self):
        temp_k = get_mars_temperature(self.sol_hour) if self.is_mars else EARTH_TEMP
        
        if self.is_mars:
            thermal_noise_density = 10 * np.log10(BOLTZMANN * temp_k * 1000)
        else:
            thermal_noise_density = -174.0
            
        for node in self.nodes:
            bw_val = node.bw
            if "proposed" in self.scenario:
                nf = PROPOSED_NOISE_FIGURE
            else:
                nf = MARS_NOISE_FIGURE if self.is_mars else EARTH_NOISE_FIGURE
            noise_floor = thermal_noise_density + 10 * np.log10(bw_val) + nf
            
            d = node.distance_to_gw
            fc = PROPOSED_FC if "proposed" in self.scenario else (MARS_FC if self.is_mars else EARTH_FC)
            
            if "satellite" in self.scenario:
                pl = self.sat_constellation.get_path_loss(d, carrier_frequency=fc)
            elif self.is_mars:
                pl_0 = 20 * np.log10(4 * np.pi * fc * 1 / C)
                exp = PROPOSED_PATH_LOSS_EXP if "proposed" in self.scenario else MARS_PATH_LOSS_EXP
                pl = pl_0 + 10 * exp * np.log10(max(d, 1.0))
                if self.dust_storm:
                    att = PROPOSED_DUST_ATTENUATION if "proposed" in self.scenario else DUST_STORM_ATTENUATION
                    pl += att * (d / 1000)
            else:
                pl_0 = 20 * np.log10(4 * np.pi * fc * 1 / C)
                pl = pl_0 + 10 * EARTH_PATH_LOSS_EXP * np.log10(max(d, 1.0))
                
            g_node = node.antenna_gain
            g_gw = self.gw_antenna_gain
            if self.is_mars and self.dust_storm:
                loss = PROPOSED_DUST_ANTENNA_LOSS if "proposed" in self.scenario else DUST_STORM_ANTENNA_LOSS
                g_node -= loss
                if "satellite" not in self.scenario:
                    g_gw -= loss
                
            rx_power = node.tx_power - pl + g_node + g_gw
            estimated_snr = rx_power - noise_floor
            
            snr_boost = PROPOSED_THRESHOLD_BOOST if "proposed" in self.scenario else 0.0
            safety_margin = 12.0 if ("optimized" in self.scenario or "surface" in self.scenario or "satellite" in self.scenario or "proposed" in self.scenario) else 3.0
            
            assigned_sf = 12
            for sf in sorted(SF_THRESHOLDS.keys(), reverse=True):
                threshold = SF_THRESHOLDS[sf] - snr_boost
                if estimated_snr >= (threshold + safety_margin):
                    assigned_sf = sf
                    
            node.sf = assigned_sf

    def simulate_transmission_period(self, duration_hours=2):
        self.run_adr()
        
        avg_tx_interval = 300.0  # seconds
        total_time_s = duration_hours * 3600.0
        
        temp_k = get_mars_temperature(self.sol_hour) if self.is_mars else EARTH_TEMP
        thermal_noise_density = 10 * np.log10(BOLTZMANN * temp_k * 1000) if self.is_mars else -174.0
        
        events = []
        for node in self.nodes:
            num_tx = np.random.poisson(total_time_s / avg_tx_interval)
            tx_times = np.random.uniform(0, total_time_s, num_tx)
            toa = calculate_toa(payload_bytes=20, sf=node.sf, bw=node.bw)
            
            for t in tx_times:
                events.append({
                    'node': node,
                    'start_time': t,
                    'end_time': t + toa,
                    'sf': node.sf,
                    'bw': node.bw,
                    'toa': toa
                })
                
        events.sort(key=lambda x: x['start_time'])
        for idx, ev in enumerate(events):
            ev['index'] = idx
            
        total_packets_sent = len(events)
        total_packets_received = 0
        total_collisions = 0
        total_noise_failures = 0
        total_drift_failures = 0
        
        # Precompute path losses
        node_rx_power = {}
        node_snr = {}
        node_drift_fail = {}
        
        if "proposed" in self.scenario:
            nf = PROPOSED_NOISE_FIGURE
        else:
            nf = MARS_NOISE_FIGURE if self.is_mars else EARTH_NOISE_FIGURE
        noise_floor = thermal_noise_density + 10 * np.log10(125e3) + nf
        
        is_comp = ("optimized" in self.scenario or "surface" in self.scenario or "satellite" in self.scenario or "proposed" in self.scenario)
        drift_ppm = get_tcxo_drift_ppm(temp_k, compensated=is_comp) if self.is_mars else 0.0
        fc = PROPOSED_FC if "proposed" in self.scenario else (MARS_FC if self.is_mars else EARTH_FC)
        freq_drift = fc * drift_ppm * 1e-6 if self.is_mars else 0.0
        
        for node in self.nodes:
            d = node.distance_to_gw
            if "satellite" in self.scenario:
                pl = self.sat_constellation.get_path_loss(d, carrier_frequency=fc)
            elif self.is_mars:
                pl_0 = 20 * np.log10(4 * np.pi * fc * 1 / C)
                exp = PROPOSED_PATH_LOSS_EXP if "proposed" in self.scenario else MARS_PATH_LOSS_EXP
                std = MARS_SHADOWING_STD
                pl = pl_0 + 10 * exp * np.log10(max(d, 1.0)) + np.random.normal(0, std)
                if self.dust_storm:
                    att = PROPOSED_DUST_ATTENUATION if "proposed" in self.scenario else DUST_STORM_ATTENUATION
                    pl += att * (d / 1000)
            else:
                pl_0 = 20 * np.log10(4 * np.pi * fc * 1 / C)
                pl = pl_0 + 10 * EARTH_PATH_LOSS_EXP * np.log10(max(d, 1.0)) + np.random.normal(0, EARTH_SHADOWING_STD)
                
            g_node = node.antenna_gain
            g_gw = self.gw_antenna_gain
            if self.is_mars and self.dust_storm:
                loss = PROPOSED_DUST_ANTENNA_LOSS if "proposed" in self.scenario else DUST_STORM_ANTENNA_LOSS
                g_node -= loss
                if "satellite" not in self.scenario:
                    g_gw -= loss
                
            rx_power = node.tx_power - pl + g_node + g_gw
            node_rx_power[node.node_id] = rx_power
            node_snr[node.node_id] = rx_power - noise_floor
            
            if self.is_mars:
                node_drift_fail[node.node_id] = abs(freq_drift) > 0.25 * node.bw
            else:
                node_drift_fail[node.node_id] = False

        # Evaluate events
        for ev in events:
            node = ev['node']
            sf = ev['sf']
            toa = ev['toa']
            
            node.packets_transmitted += 1
            node.consume_energy(toa, "tx")
            
            rx_power = node_rx_power[node.node_id]
            snr = node_snr[node.node_id]
            drift_fail = node_drift_fail[node.node_id]
            
            snr_boost = PROPOSED_THRESHOLD_BOOST if "proposed" in self.scenario else 0.0
            demod_threshold = SF_THRESHOLDS[sf] - snr_boost
            
            if drift_fail:
                total_drift_failures += 1
                node.consume_energy(toa, "rx")
            elif snr < demod_threshold:
                total_noise_failures += 1
                node.consume_energy(toa, "rx")
            else:
                # Collision Check
                collision = False
                idx = ev['index']
                
                # Check backward
                bwd = idx - 1
                while bwd >= 0:
                    other = events[bwd]
                    if ev['start_time'] - other['start_time'] > 5.0:
                        break
                    
                    overlap = not (ev['end_time'] <= other['start_time'] or ev['start_time'] >= other['end_time'])
                    if overlap and other['sf'] == sf:
                        o_node = other['node']
                        o_rx_power = node_rx_power[o_node.node_id]
                        if rx_power - o_rx_power < 6.0:
                            collision = True
                            break
                    bwd -= 1
                    
                if not collision:
                    # Check forward
                    fwd = idx + 1
                    while fwd < len(events):
                        other = events[fwd]
                        if other['start_time'] >= ev['end_time']:
                            break
                        
                        overlap = not (ev['end_time'] <= other['start_time'] or ev['start_time'] >= other['end_time'])
                        if overlap and other['sf'] == sf:
                            o_node = other['node']
                            o_rx_power = node_rx_power[o_node.node_id]
                            if rx_power - o_rx_power < 6.0:
                                collision = True
                                break
                        fwd += 1
                        
                if collision:
                    total_collisions += 1
                    node.consume_energy(toa, "rx")
                else:
                    total_packets_received += 1
                    node.packets_acked += 1
                    node.consume_energy(toa, "rx")

        pdr = (total_packets_received / total_packets_sent * 100) if total_packets_sent > 0 else 0.0
        return {
            'sent': total_packets_sent,
            'received': total_packets_received,
            'collisions': total_collisions,
            'noise_failures': total_noise_failures,
            'drift_failures': total_drift_failures,
            'pdr': pdr,
            'avg_energy_j_per_packet': sum(n.energy_consumed for n in self.nodes) / max(total_packets_received, 1)
        }

def _run_scenario(count, radius_km, scenario, dust, sol_hour):
    """Run one scenario once; return pdr and energy."""
    sim = NetworkSimulator(count, radius_km, is_mars=True, scenario=scenario)
    sim.set_dust_storm(dust)
    sim.set_sol_hour(sol_hour)
    r = sim.simulate_transmission_period(2)
    return r['pdr'], r['avg_energy_j_per_packet']

def _mc_mean_ci(values):
    """Return (mean, 95% half-CI) for a list of scalar values."""
    arr = np.array(values)
    mean = arr.mean()
    ci   = 1.96 * arr.std(ddof=1) / np.sqrt(len(arr))
    return float(mean), float(ci)

def _run_paired(count, radius_km, scenario_base, sol_hour, run_idx, ni):
    """
    Run one clear and one storm replication with IDENTICAL node placement
    and packet-timing seed. Only dust_storm flag differs.
    Returns (pdr_clear, energy_clear, pdr_dust, energy_dust).
    """
    sub_seed = run_idx * 10000 + ni * 100
    np.random.seed(sub_seed)
    sim = NetworkSimulator(count, radius_km, is_mars=True,
                           scenario=scenario_base + '_clear')
    sim.set_sol_hour(sol_hour)

    # --- Clear run ---
    sim.set_dust_storm(False)
    np.random.seed(sub_seed + 1)
    r_clear = sim.simulate_transmission_period(2)

    # Reset per-node energy counters before storm run
    for node in sim.nodes:
        node.energy_consumed = 0.0
        node.packets_transmitted = 0
        node.packets_acked = 0

    # --- Storm run: SAME topology, different dust flag ---
    sim.set_dust_storm(True)
    np.random.seed(sub_seed + 1)          # identical packet timing
    r_dust = sim.simulate_transmission_period(2)

    return (r_clear['pdr'], r_clear['avg_energy_j_per_packet'],
            r_dust['pdr'],  r_dust['avg_energy_j_per_packet'])


def run_node_density_study():
    node_counts = [50, 100, 150, 200, 250, 300, 400, 500]
    radius_km   = 12.0

    unpaired_scenarios = [
        ('baseline',           False, 4.0, False),
        ('mars_surface',       4.0,   True),   # paired: clear + dust
        ('mars_satellite',     4.0,   True),   # paired: clear + dust
    ]

    all_pdr    = {tag: [[] for _ in node_counts] for tag in [
        'baseline',
        'mars_surface_clear', 'mars_surface_dust',
        'mars_satellite_clear', 'mars_satellite_dust',
        'mars_proposed_surface_clear', 'mars_proposed_surface_dust',
        'mars_proposed_satellite_clear', 'mars_proposed_satellite_dust',
    ]}
    all_energy = {tag: [[] for _ in node_counts] for tag in all_pdr}

    for run_idx in range(NUM_RUNS):
        np.random.seed(run_idx * 7 + 13)
        for ni, count in enumerate(node_counts):
            print(f"  Run {run_idx+1}/{NUM_RUNS} | {count} nodes")

            # Earth baseline (unpaired)
            sim_e = NetworkSimulator(count, radius_km, is_mars=False,
                                     scenario='baseline')
            r_e = sim_e.simulate_transmission_period(2)
            all_pdr['baseline'][ni].append(r_e['pdr'])
            all_energy['baseline'][ni].append(r_e['avg_energy_j_per_packet'])

            # Paired surface clear/dust
            pc, ec, pd_, ed = _run_paired(
                count, radius_km, 'mars_surface', 4.0, run_idx, ni)
            all_pdr['mars_surface_clear'][ni].append(pc)
            all_energy['mars_surface_clear'][ni].append(ec)
            all_pdr['mars_surface_dust'][ni].append(pd_)
            all_energy['mars_surface_dust'][ni].append(ed)

            # Paired satellite clear/dust
            pc, ec, pd_, ed = _run_paired(
                count, radius_km, 'mars_satellite', 4.0, run_idx, ni)
            all_pdr['mars_satellite_clear'][ni].append(pc)
            all_energy['mars_satellite_clear'][ni].append(ec)
            all_pdr['mars_satellite_dust'][ni].append(pd_)
            all_energy['mars_satellite_dust'][ni].append(ed)

            # Paired proposed SURFACE clear/dust
            pc, ec, pd_, ed = _run_paired(
                count, radius_km, 'mars_proposed_surface', 4.0, run_idx, ni + 100)
            all_pdr['mars_proposed_surface_clear'][ni].append(pc)
            all_energy['mars_proposed_surface_clear'][ni].append(ec)
            all_pdr['mars_proposed_surface_dust'][ni].append(pd_)
            all_energy['mars_proposed_surface_dust'][ni].append(ed)

            # Paired proposed satellite clear/dust
            pc, ec, pd_, ed = _run_paired(
                count, radius_km, 'mars_proposed_satellite', 4.0, run_idx, ni)
            all_pdr['mars_proposed_satellite_clear'][ni].append(pc)
            all_energy['mars_proposed_satellite_clear'][ni].append(ec)
            all_pdr['mars_proposed_satellite_dust'][ni].append(pd_)
            all_energy['mars_proposed_satellite_dust'][ni].append(ed)

    # Build averaged CSV
    rows = {'Nodes': node_counts}
    labels = [
        ('baseline',                       'Earth'),
        ('mars_surface_clear',             'Mars Surf Clear'),
        ('mars_surface_dust',              'Mars Surf Dust'),
        ('mars_satellite_clear',           'Mars Sat Clear'),
        ('mars_satellite_dust',            'Mars Sat Dust'),
        ('mars_proposed_surface_clear',    'Mars Prop Surf Clear'),
        ('mars_proposed_surface_dust',     'Mars Prop Surf Dust'),
        ('mars_proposed_satellite_clear',  'Mars Prop Clear'),
        ('mars_proposed_satellite_dust',   'Mars Prop Dust'),
    ]
    for (tag, lbl) in labels:
        means_p = []; cis_p = []; means_e = []; cis_e = []
        for ni in range(len(node_counts)):
            mp, cp = _mc_mean_ci(all_pdr[tag][ni])
            me, ce = _mc_mean_ci(all_energy[tag][ni])
            means_p.append(mp); cis_p.append(cp)
            means_e.append(me); cis_e.append(ce)
        rows[f'{lbl} PDR (%)']    = means_p
        rows[f'{lbl} PDR CI']     = cis_p
        rows[f'{lbl} Energy (J)'] = means_e
        rows[f'{lbl} Energy CI']  = cis_e

    df_pdr = pd.DataFrame(rows)
    df_pdr.to_csv("results/pdr_summary.csv", index=False)
    print("Saved results/pdr_summary.csv")


def run_distance_reliability_study():
    distances_km = np.linspace(1.0, 20.0, 10)
    num_nodes    = 100

    all_pdr = {tag: [[] for _ in distances_km] for tag in [
        'baseline',
        'mars_surface_clear', 'mars_surface_dust',
        'mars_satellite_clear', 'mars_satellite_dust',
        'mars_proposed_surface_clear', 'mars_proposed_surface_dust',
        'mars_proposed_satellite_clear', 'mars_proposed_satellite_dust',
    ]}

    for run_idx in range(NUM_RUNS):
        np.random.seed(run_idx * 11 + 5)
        for di, dist in enumerate(distances_km):
            print(f"  Run {run_idx+1}/{NUM_RUNS} | dist {dist:.1f} km")

            # Earth baseline
            sim_e = NetworkSimulator(num_nodes, dist, is_mars=False,
                                     scenario='baseline')
            r_e = sim_e.simulate_transmission_period(2)
            all_pdr['baseline'][di].append(r_e['pdr'])

            # Paired surface
            pc, _, pd_, _ = _run_paired(
                num_nodes, dist, 'mars_surface', 4.0, run_idx, di)
            all_pdr['mars_surface_clear'][di].append(pc)
            all_pdr['mars_surface_dust'][di].append(pd_)

            # Paired satellite
            pc, _, pd_, _ = _run_paired(
                num_nodes, dist, 'mars_satellite', 4.0, run_idx, di)
            all_pdr['mars_satellite_clear'][di].append(pc)
            all_pdr['mars_satellite_dust'][di].append(pd_)

            # Paired proposed surface
            pc, _, pd_, _ = _run_paired(
                num_nodes, dist, 'mars_proposed_surface', 4.0, run_idx, di + 100)
            all_pdr['mars_proposed_surface_clear'][di].append(pc)
            all_pdr['mars_proposed_surface_dust'][di].append(pd_)

            # Paired proposed satellite
            pc, _, pd_, _ = _run_paired(
                num_nodes, dist, 'mars_proposed_satellite', 4.0, run_idx, di)
            all_pdr['mars_proposed_satellite_clear'][di].append(pc)
            all_pdr['mars_proposed_satellite_dust'][di].append(pd_)

    col_map = [
        ('baseline',                       'Earth_PDR'),
        ('mars_surface_clear',             'Mars_Surf_Clear_PDR'),
        ('mars_surface_dust',              'Mars_Surf_Dust_PDR'),
        ('mars_satellite_clear',           'Mars_Sat_Clear_PDR'),
        ('mars_satellite_dust',            'Mars_Sat_Dust_PDR'),
        ('mars_proposed_surface_clear',    'Mars_Prop_Surf_Clear_PDR'),
        ('mars_proposed_surface_dust',     'Mars_Prop_Surf_Dust_PDR'),
        ('mars_proposed_satellite_clear',  'Mars_Prop_Clear_PDR'),
        ('mars_proposed_satellite_dust',   'Mars_Prop_Dust_PDR'),
    ]
    rows = {'Distance_km': distances_km}
    for (tag, col) in col_map:
        rows[col]         = [_mc_mean_ci(all_pdr[tag][di])[0] for di in range(len(distances_km))]
        rows[col + '_CI'] = [_mc_mean_ci(all_pdr[tag][di])[1] for di in range(len(distances_km))]

    df_dist = pd.DataFrame(rows)
    df_dist.to_csv("results/pdr_vs_distance.csv", index=False)
    print("Saved results/pdr_vs_distance.csv")


def run_diurnal_performance_study():
    sol_hours = np.linspace(0.0, 24.0, 13)
    num_nodes = 150
    radius_km = 10.0
    
    results = {
        'mars_surf_clear': [],
        'mars_surf_dust': [],
        'mars_sat_clear': [],
        'mars_sat_dust': [],
        'mars_prop_clear': [],
        'mars_prop_dust': []
    }
    temps = []
    noise_floors = []
    
    for hour in sol_hours:
        t = get_mars_temperature(hour)
        temps.append(t)
        
        bw_val = 125e3
        thermal_noise_density = 10 * np.log10(BOLTZMANN * t * 1000)
        noise_floor = thermal_noise_density + 10 * np.log10(bw_val) + MARS_NOISE_FIGURE
        noise_floors.append(noise_floor)
        
        # 1. Surf Clear
        sim_surf_clear = NetworkSimulator(num_nodes, radius_km, is_mars=True, scenario="mars_surface_clear")
        sim_surf_clear.set_dust_storm(False)
        sim_surf_clear.set_sol_hour(hour)
        res_sc = sim_surf_clear.simulate_transmission_period(1)
        results['mars_surf_clear'].append(res_sc['pdr'])
        
        # 2. Surf Dust
        sim_surf_dust = NetworkSimulator(num_nodes, radius_km, is_mars=True, scenario="mars_surface_dust")
        sim_surf_dust.set_dust_storm(True)
        sim_surf_dust.set_sol_hour(hour)
        res_sd = sim_surf_dust.simulate_transmission_period(1)
        results['mars_surf_dust'].append(res_sd['pdr'])
        
        # 3. Sat Clear
        sim_sat_clear = NetworkSimulator(num_nodes, radius_km, is_mars=True, scenario="mars_satellite_clear")
        sim_sat_clear.set_dust_storm(False)
        sim_sat_clear.set_sol_hour(hour)
        res_stc = sim_sat_clear.simulate_transmission_period(1)
        results['mars_sat_clear'].append(res_stc['pdr'])
        
        # 4. Sat Dust
        sim_sat_dust = NetworkSimulator(num_nodes, radius_km, is_mars=True, scenario="mars_satellite_dust")
        sim_sat_dust.set_dust_storm(True)
        sim_sat_dust.set_sol_hour(hour)
        res_std = sim_sat_dust.simulate_transmission_period(1)
        results['mars_sat_dust'].append(res_std['pdr'])

        # 5. Prop Clear
        sim_prop_clear = NetworkSimulator(num_nodes, radius_km, is_mars=True, scenario="mars_proposed_satellite_clear")
        sim_prop_clear.set_dust_storm(False)
        sim_prop_clear.set_sol_hour(hour)
        res_prc = sim_prop_clear.simulate_transmission_period(1)
        results['mars_prop_clear'].append(res_prc['pdr'])

        # 6. Prop Dust
        sim_prop_dust = NetworkSimulator(num_nodes, radius_km, is_mars=True, scenario="mars_proposed_satellite_dust")
        sim_prop_dust.set_dust_storm(True)
        sim_prop_dust.set_sol_hour(hour)
        res_prd = sim_prop_dust.simulate_transmission_period(1)
        results['mars_prop_dust'].append(res_prd['pdr'])

    df_diurnal = pd.DataFrame({
        'Sol_Hour': sol_hours,
        'Temperature_K': temps,
        'Noise_Floor_dBm': noise_floors,
        'Surf_Clear_PDR': results['mars_surf_clear'],
        'Surf_Dust_PDR': results['mars_surf_dust'],
        'Sat_Clear_PDR': results['mars_sat_clear'],
        'Sat_Dust_PDR': results['mars_sat_dust'],
        'Prop_Clear_PDR': results['mars_prop_clear'],
        'Prop_Dust_PDR': results['mars_prop_dust']
    })
    df_diurnal.to_csv("results/diurnal_performance.csv", index=False)
    print("Saved results/diurnal_performance.csv")

def generate_link_budget_data():
    distances_m = np.logspace(1.0, 4.5, 100)
    tx_power = 14.0
    
    pl_0_e = 20 * np.log10(4 * np.pi * EARTH_FC * 1 / C)
    pl_earth = pl_0_e + 10 * EARTH_PATH_LOSS_EXP * np.log10(distances_m)
    
    pl_0_m = 20 * np.log10(4 * np.pi * MARS_FC * 1 / C)
    pl_mars_clear = pl_0_m + 10 * MARS_PATH_LOSS_EXP * np.log10(distances_m)
    pl_mars_dust = pl_mars_clear + DUST_STORM_ATTENUATION * (distances_m / 1000)
    
    slant_ranges = np.sqrt((300e3)**2 + distances_m**2)
    pl_sat = 20 * np.log10(4 * np.pi * MARS_FC * 1 / C) + 20 * np.log10(slant_ranges) + 0.05
    
    pl_prop = 20 * np.log10(4 * np.pi * PROPOSED_FC * 1 / C) + 20 * np.log10(slant_ranges) + 0.05
    
    g_gw_surface = 2.15
    g_gw_sat = 6.0
    g_gw_prop = PROPOSED_SAT_ANTENNA_GAIN
    
    rx_earth = tx_power - pl_earth + 0.0 + g_gw_surface
    rx_mars_clear = tx_power - pl_mars_clear + 0.0 + g_gw_surface
    rx_mars_dust = tx_power - pl_mars_dust + 0.0 + g_gw_surface - 2 * DUST_STORM_ANTENNA_LOSS
    rx_mars_sat_clear = tx_power - pl_sat + 0.0 + g_gw_sat
    rx_mars_sat_dust = tx_power - pl_sat + (0.0 - DUST_STORM_ANTENNA_LOSS) + g_gw_sat
    
    rx_prop_clear = tx_power - pl_prop + 0.0 + g_gw_prop
    rx_prop_dust = tx_power - pl_prop + (0.0 - PROPOSED_DUST_ANTENNA_LOSS) + g_gw_prop
    
    df_link = pd.DataFrame({
        'Distance_m': distances_m,
        'RX_Earth': rx_earth,
        'RX_Mars_Clear': rx_mars_clear,
        'RX_Mars_Dust': rx_mars_dust,
        'RX_Mars_Sat_Clear': rx_mars_sat_clear,
        'RX_Mars_Sat_Dust': rx_mars_sat_dust,
        'RX_Prop_Clear': rx_prop_clear,
        'RX_Prop_Dust': rx_prop_dust
    })
    df_link.to_csv("results/link_budget_analysis.csv", index=False)
    print("Saved results/link_budget_analysis.csv")

if __name__ == "__main__":
    print("====================================================")
    print("STARTING MARTIAN LORAWAN RAW DATA GENERATOR")
    print("====================================================")
    
    run_node_density_study()
    run_distance_reliability_study()
    run_diurnal_performance_study()
    generate_link_budget_data()
    
    print("====================================================")
    print("SIMULATION DATA GENERATION COMPLETED successfully.")
    print("====================================================")
