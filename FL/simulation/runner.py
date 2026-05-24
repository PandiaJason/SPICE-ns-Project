"""
Space-FL Simulation Runner.
Simulates 5 SmallSats and 1 Master Orbiter in Mars orbit.
Integrates orbital mechanics (visibility, eclipse), energy models, DTN queues,
and Federated Learning algorithms.
"""
import os
import json
import time
import copy
import numpy as np
import torch

from simulation.config import (
    NUM_SATELLITES, MASTER_ORBITER_ID, TOTAL_STEPS, CONTACT_LIFETIME, OCCLUSION_PROB,
    BATTERY_CAPACITY_WH, INITIAL_BATTERY_PCT, PRUNING_THRESHOLD_PCT, CRITICAL_BATTERY_PCT,
    POWER_RECHARGE_W, POWER_IDLE_W, POWER_TRAINING_FULL_W, POWER_TRAINING_PRUNED_W, POWER_TX_W,
    INPUT_DIM, HIDDEN_DIM_1, HIDDEN_DIM_2, NUM_CLASSES,
    PRUNED_HIDDEN_DIM_1, PRUNED_HIDDEN_DIM_2, BATCH_SIZE, LOCAL_EPOCHS, LEARNING_RATE, FEDPROX_MU,
    STALENESS_BETA, DTN_MAX_DELAY, SEED, EXPERIMENTS, RESULTS_DIR
)
from simulation.dataset import get_loaders
from simulation.model import SpaceModel, local_train, evaluate

# -------------------------------------------------------------------
# Orbital Mechanics / Link Visibility Model
# -------------------------------------------------------------------
def get_visibility(sat_id, step):
    """
    Simulates periodic visibility windows between satellite and Master Orbiter
    due to orbital occlusion.
    Each satellite has a 20-step contact window followed by a 40-step blackout,
    with a phase shift of 12 steps between consecutive satellites.
    """
    phase_shift = sat_id * 12
    cycle_position = (step + phase_shift) % 60
    is_visible_orbitally = cycle_position < 20
    
    # Introduce random channel blockages (e.g. atmospheric effects, dust)
    np.random.seed(SEED + sat_id * 1000 + step)
    channel_ok = np.random.rand() > OCCLUSION_PROB
    
    # Visible if both orbitally clear and channel is not randomly blocked
    # (But for CGR, we assume CGR predictable contacts, we can make orbitally clear deterministic)
    return is_visible_orbitally and channel_ok

def get_sunlit(sat_id, step):
    """
    Simulates periodic sunlit/eclipse periods for solar power harvesting.
    Satellites enter eclipse behind Mars for 30 steps every 80 steps.
    """
    phase_shift = sat_id * 8
    cycle_position = (step + phase_shift) % 80
    return cycle_position < 50

# -------------------------------------------------------------------
# Satellite Client Class
# -------------------------------------------------------------------
class SpaceSatellite:
    def __init__(self, sat_id, train_loader):
        self.id = sat_id
        self.train_loader = train_loader
        
        # Initialize battery state (in Watt-hours)
        self.battery_capacity = BATTERY_CAPACITY_WH
        self.battery_energy = BATTERY_CAPACITY_WH * (INITIAL_BATTERY_PCT / 100.0)
        self.is_sleeping = False
        
        # DTN Bundle Queue: contains dicts with {weights, created_step, mode}
        self.dtn_queue = []
        
        # Local model state
        self.local_model = SpaceModel()
        
        # Stats
        self.updates_sent = 0
        self.steps_trained = 0
        
    def get_battery_pct(self):
        return (self.battery_energy / self.battery_capacity) * 100.0

    def update_energy(self, step, is_training, is_transmitting, training_mode):
        """
        Updates the satellite battery energy level based on solar input and consumption.
        Step interval delta_t = 0.1 hours (6 minutes).
        """
        dt = 0.1 # hours
        
        # Power Input
        is_sun = get_sunlit(self.id, step)
        p_in = POWER_RECHARGE_W if is_sun else 0.0
        
        # Power Output
        p_out = POWER_IDLE_W
        if self.is_sleeping:
            # Low power sleep mode
            p_out = 0.2
        else:
            if is_training:
                p_out += POWER_TRAINING_PRUNED_W if training_mode == 'pruned' else POWER_TRAINING_FULL_W
            if is_transmitting:
                p_out += POWER_TX_W
                
        # Net energy change
        dE = (p_in - p_out) * dt
        self.battery_energy = max(0.0, min(self.battery_energy + dE, self.battery_capacity))
        
        # State transitions based on battery thresholds
        pct = self.get_battery_pct()
        if self.is_sleeping:
            if pct > 15.0:
                self.is_sleeping = False # Wake up with hysteresis
        else:
            if pct <= CRITICAL_BATTERY_PCT:
                self.is_sleeping = True # Go to sleep
                self.dtn_queue.clear() # Clear queue (power loss data drop)

# -------------------------------------------------------------------
# Simulation Runner
# -------------------------------------------------------------------
def run_experiment(exp_config, train_loaders, test_loader):
    """
    Runs a single federated learning experiment under orbital and battery constraints.
    """
    print(f"\nRunning Experiment: {exp_config['label']}")
    print(exp_config['desc'])
    
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    
    # Initialize Master Orbiter global model
    global_model = SpaceModel()
    
    # Initialize Satellites
    satellites = [SpaceSatellite(i, train_loaders[i]) for i in range(NUM_SATELLITES)]
    
    # Master Orbiter synchronization buffers
    # For synchronous FL
    synced_round_buffer = {i: None for i in range(NUM_SATELLITES)}
    sync_round = 0
    
    # Metrics logger
    history = []
    
    # Track statistics
    global_updates_received = 0
    stale_updates_dropped = 0
    total_staleness = 0
    updates_aggregated = 0
    
    # Send initial global model to all satellites
    initial_weights = global_model.get_weights(mode='full')
    for sat in satellites:
        sat.local_model.load_weights(initial_weights, mode='full')
        
    for step in range(TOTAL_STEPS):
        # 1. Update environments
        is_visible = [get_visibility(sat.id, step) for sat in satellites]
        
        # 2. Local Satellite Training & Power management
        training_triggered = [False] * NUM_SATELLITES
        training_modes = ['full'] * NUM_SATELLITES
        
        for sat in satellites:
            if sat.is_sleeping:
                # Update energy (sleeping, not training, not transmitting)
                sat.update_energy(step, is_training=False, is_transmitting=False, training_mode='full')
                continue
                
            # Decision to train: in our simulation, a satellite trains if it has no updates in its queue,
            # which keeps the queue load reasonable. Or it trains every 10 steps.
            # Let's say it trains if its DTN queue size is < 3 bundles.
            should_train = len(sat.dtn_queue) < 3
            
            # Check battery to decide pruning mode
            bat_pct = sat.get_battery_pct()
            if bat_pct <= PRUNING_THRESHOLD_PCT:
                mode = 'pruned' if exp_config['pruning'] else 'full'
            else:
                mode = 'full'
                
            # Perform training if decided
            if should_train:
                training_triggered[sat.id] = True
                training_modes[sat.id] = mode
                
                # Fetch current global model if we can (or use what we have in buffer)
                # In async, we train on the last model we successfully downloaded.
                # In sync, we train on the model distributed at the start of the round.
                
                # Run local training
                mu_val = FEDPROX_MU if 'FedProx' in exp_config['label'] else 0.0
                g_weights = global_model.get_weights(mode=mode)
                
                local_w = local_train(
                    sat.local_model, sat.train_loader, epochs=LOCAL_EPOCHS,
                    mode=mode, mu=mu_val, global_weights=g_weights, lr=LEARNING_RATE
                )
                
                # Package weight update into a DTN bundle
                bundle = {
                    'weights': local_w,
                    'created_step': step,
                    'mode': mode,
                    'sat_id': sat.id
                }
                sat.dtn_queue.append(bundle)
                sat.steps_trained += 1
                
        # 3. DTN Transmission & Routing
        transmission_triggered = [False] * NUM_SATELLITES
        received_bundles = []
        
        for sat in satellites:
            if sat.is_sleeping:
                continue
                
            # If visible to Master Orbiter and has bundles to send
            if is_visible[sat.id] and len(sat.dtn_queue) > 0:
                # Transmit one bundle per step (DTN link capacity simulation)
                bundle = sat.dtn_queue.pop(0)
                
                # Check TTL / Max Delay
                delay = step - bundle['created_step']
                if exp_config['dtn_routing'] and delay > DTN_MAX_DELAY:
                    stale_updates_dropped += 1
                else:
                    # Successful transmission
                    received_bundles.append(bundle)
                    sat.updates_sent += 1
                    transmission_triggered[sat.id] = True
                    
            # Update battery energy for this step
            sat.update_energy(
                step, 
                is_training=training_triggered[sat.id], 
                is_transmitting=transmission_triggered[sat.id], 
                training_mode=training_modes[sat.id]
            )
            
        # 4. Master Orbiter Weight Aggregation
        global_updated = False
        
        if len(received_bundles) > 0:
            global_weights = global_model.get_weights(mode='full')
            
            for bundle in received_bundles:
                global_updates_received += 1
                tau = step - bundle['created_step']
                total_staleness += tau
                
                # --- ASYNCHRONOUS FL ---
                if exp_config['async_fl']:
                    # Base aggregation weight (e.g. eta = 0.40)
                    eta_0 = 0.40
                    
                    # Apply staleness scaling
                    if exp_config['staleness_compensation']:
                        alpha = (1.0 + tau) ** (-STALENESS_BETA)
                        eta = eta_0 * alpha
                    else:
                        eta = eta_0
                        
                    # Merge weights
                    client_w = bundle['weights']
                    client_mode = bundle['mode']
                    
                    with torch.no_grad():
                        if client_mode == 'full':
                            for name in global_weights.keys():
                                global_weights[name] = (1.0 - eta) * global_weights[name] + eta * client_w[name]
                        elif client_mode == 'pruned':
                            # Dynamic merge into global sub-tensors
                            h1_p, h2_p = PRUNED_HIDDEN_DIM_1, PRUNED_HIDDEN_DIM_2
                            
                            global_weights['fc1.weight'][:h1_p, :] = (1.0 - eta) * global_weights['fc1.weight'][:h1_p, :] + eta * client_w['fc1.weight']
                            global_weights['fc1.bias'][:h1_p] = (1.0 - eta) * global_weights['fc1.bias'][:h1_p] + eta * client_w['fc1.bias']
                            
                            global_weights['fc2.weight'][:h2_p, :h1_p] = (1.0 - eta) * global_weights['fc2.weight'][:h2_p, :h1_p] + eta * client_w['fc2.weight']
                            global_weights['fc2.bias'][:h2_p] = (1.0 - eta) * global_weights['fc2.bias'][:h2_p] + eta * client_w['fc2.bias']
                            
                            global_weights['fc3.weight'][:, :h2_p] = (1.0 - eta) * global_weights['fc3.weight'][:, :h2_p] + eta * client_w['fc3.weight']
                            global_weights['fc3.bias'] = (1.0 - eta) * global_weights['fc3.bias'] + eta * client_w['fc3.bias']
                            
                    global_model.load_weights(global_weights, mode='full')
                    global_updated = True
                    updates_aggregated += 1
                    
                # --- SYNCHRONOUS FL ---
                else:
                    # In synchronous FL, store in synchronization round buffer
                    # If satellite is asleep, we might skip it or wait forever.
                    # Standard FedAvg/FedProx waits for all active clients.
                    # Let's say it waits for updates from all satellites that are not permanently dead.
                    # To model standard sync FL, the Master waits until it has received updates from all 5 nodes
                    # for the current sync round.
                    sat_id = bundle['sat_id']
                    if synced_round_buffer[sat_id] is None:
                        synced_round_buffer[sat_id] = bundle['weights']
                        
            # Check if synchronous round is complete (all 5 satellites have sent an update)
            if not exp_config['async_fl']:
                received_all = all(synced_round_buffer[i] is not None for i in range(NUM_SATELLITES))
                if received_all:
                    # FedAvg / FedProx average aggregation
                    mean_weights = copy.deepcopy(synced_round_buffer[0])
                    for name in mean_weights.keys():
                        for i in range(1, NUM_SATELLITES):
                            mean_weights[name] += synced_round_buffer[i][name]
                        mean_weights[name] /= NUM_SATELLITES
                        
                    global_model.load_weights(mean_weights, mode='full')
                    global_updated = True
                    updates_aggregated += 1
                    sync_round += 1
                    
                    # Clear round buffer
                    synced_round_buffer = {i: None for i in range(NUM_SATELLITES)}
                    
        # 5. Broadcast Updated Global Model (if any updates occurred)
        if global_updated:
            latest_global_w = global_model.get_weights(mode='full')
            for sat in satellites:
                # Satellites only receive the model update if they are visible
                if is_visible[sat.id] and not sat.is_sleeping:
                    sat.local_model.load_weights(latest_global_w, mode='full')
                    
        # 6. Evaluate Global Model Accuracy and Loss
        test_acc, test_loss = evaluate(global_model, test_loader)
        
        # 7. Record History
        sat_states = {}
        for sat in satellites:
            sat_states[sat.id] = {
                'battery_pct': sat.get_battery_pct(),
                'is_sleeping': sat.is_sleeping,
                'is_visible': is_visible[sat.id],
                'mode': 'asleep' if sat.is_sleeping else ('pruned' if sat.get_battery_pct() <= PRUNING_THRESHOLD_PCT and exp_config['pruning'] else 'full'),
                'queue_size': len(sat.dtn_queue),
                'is_sunlit': get_sunlit(sat.id, step),
                'updates_sent': sat.updates_sent
            }
            
        step_log = {
            'step': step,
            'test_accuracy': test_acc,
            'test_loss': test_loss,
            'satellites': sat_states,
            'global_updates_received': global_updates_received,
            'stale_updates_dropped': stale_updates_dropped,
            'updates_aggregated': updates_aggregated,
            'mean_staleness': total_staleness / max(1, global_updates_received)
        }
        history.append(step_log)
        
        # Printing logs
        if step % 20 == 0 or step == TOTAL_STEPS - 1:
            bat_str = ", ".join([f"S{i}:{satellites[i].get_battery_pct():.0f}%({sat_states[i]['mode'][0].upper()})" for i in range(NUM_SATELLITES)])
            print(f"  Step {step:03d} | Acc: {test_acc:.4f} | Loss: {test_loss:.4f} | Batteries: {bat_str} | Received: {global_updates_received} | Dropped: {stale_updates_dropped}")
            
    # Save results to file
    out_file = os.path.join(RESULTS_DIR, f"{exp_config['label']}.json")
    with open(out_file, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"Experiment complete. Saved -> {out_file}")
    
    return history

def run_all():
    print("="*60)
    print("  Starting Space Federated Learning Simulation")
    print("="*60)
    
    t0 = time.time()
    train_loaders, test_loader = get_loaders(batch_size=BATCH_SIZE)
    print(f"Dataset generated. {NUM_SATELLITES} local train loaders and 1 global test loader prepared.")
    
    for exp in EXPERIMENTS:
        run_experiment(exp, train_loaders, test_loader)
        
    print("="*60)
    print(f"Simulation Suite Completed in {time.time() - t0:.1f} seconds.")
    print("="*60)

if __name__ == '__main__':
    run_all()
