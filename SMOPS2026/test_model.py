import os
import gzip
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

# Create results directory
results_dir = "/home/jason/SPICE-ns-Project/SMOPS2026/results"
os.makedirs(results_dir, exist_ok=True)

# Define the Micro-Autoencoder
class MicroAutoencoder(nn.Module):
    def __init__(self, input_dim=31, latent_dim=4):
        super(MicroAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

def evaluate_testing(X_test, y_test, model_params, onsets):
    scaler = model_params['scaler']
    X_test_scaled = scaler.transform(X_test)
    tau = model_params['threshold']
    
    # Load model state
    model = MicroAutoencoder(input_dim=31, latent_dim=4)
    model.load_state_dict(model_params['state_dict'])
    model.eval()
    
    # Inference
    with torch.no_grad():
        test_recon = model(torch.FloatTensor(X_test_scaled))
        test_mse = torch.mean((torch.FloatTensor(X_test_scaled) - test_recon) ** 2, dim=1).numpy()
        
    predicted_anomalies = (test_mse > tau).astype(float)
    
    # 1. Anomaly Detection Delays (in minutes, at 30-second sampling interval)
    delays = {}
    sample_interval_secs = 30.0
    max_delay_samples = int(45.0 * 60.0 / sample_interval_secs)  # 90 samples
    for failure_type, onset_idx in onsets.items():
        if onset_idx < 0:
            delays[failure_type] = -1.0
            continue
            
        # Active window: inspect up to max_delay_samples post onset (45 mins)
        detected_indices = np.where(predicted_anomalies[onset_idx : onset_idx + max_delay_samples] == 1.0)[0]
        if len(detected_indices) > 0:
            delay_samples = detected_indices[0]
            delays[failure_type] = (delay_samples * sample_interval_secs) / 60.0  # in minutes
        else:
            delays[failure_type] = 45.0  # Penalty max duration
            
    # 2. False Alarm Rate (FAR) on nominal segments
    nominal_indices = np.where(y_test == 0)[0]
    false_alarms = np.sum(predicted_anomalies[nominal_indices])
    far = (false_alarms / len(nominal_indices)) * 100.0
    
    # 3. Precision, Recall, and F1-score Classification Metrics
    tp = np.sum((predicted_anomalies == 1.0) & (y_test == 1.0))
    fp = np.sum((predicted_anomalies == 1.0) & (y_test == 0.0))
    fn = np.sum((predicted_anomalies == 0.0) & (y_test == 1.0))
    
    precision = tp / (tp + fp + 1e-12)
    recall = tp / (tp + fn + 1e-12)
    f1 = 2.0 * precision * recall / (precision + recall + 1e-12)
    
    # 4. Telemetry Dual-Mode Compression
    packet_size_bytes = 132  # 31 features * 4 bytes + 8 bytes timestamp = 132 bytes
    baseline_bytes = len(X_test) * packet_size_bytes
    
    transmitted_bytes = 0
    heartbeat_interval = 10
    nominal_buffer_count = 0
    buffer_active_until = -1
    
    i = 0
    while i < len(X_test):
        if i <= buffer_active_until:
            i += 1
            continue
            
        if test_mse[i] > tau:
            # Trigger Mode B (anomalous capture window)
            # Clip start_idx to start after the previously active buffer to avoid duplicate transmission
            start_idx = int(max(buffer_active_until + 1, i - 20))
            end_idx = min(len(X_test), i + 10)
            buffer_data = X_test[start_idx:end_idx]
            
            # Lossless Compression via GZIP
            raw_bytes = buffer_data.astype(np.float32).tobytes()
            compressed_bytes = gzip.compress(raw_bytes)
            
            # Adding 10 bytes metadata
            transmitted_bytes += len(compressed_bytes) + 10
            buffer_active_until = end_idx - 1
            nominal_buffer_count = 0
            i = end_idx
        else:
            # Mode A (Nominal heartbeat)
            nominal_buffer_count += 1
            if nominal_buffer_count >= heartbeat_interval:
                transmitted_bytes += 10
                nominal_buffer_count = 0
            i += 1
            
    if nominal_buffer_count > 0:
        transmitted_bytes += 10
        
    reduction_ratio = (1.0 - (transmitted_bytes / baseline_bytes)) * 100.0
    bandwidth_factor = baseline_bytes / transmitted_bytes
    
    return test_mse, predicted_anomalies, delays, far, baseline_bytes, transmitted_bytes, reduction_ratio, bandwidth_factor, precision, recall, f1

# -------------------------------------------------------------------------
# Step 1: Evaluate Monte Carlo Trials
# -------------------------------------------------------------------------
num_trials = 50
print(f"--- Evaluating {num_trials} Monte Carlo Test Datasets (31 Telemetry Channels, 6 Anomalies) ---")

for trial in range(1, num_trials + 1):
    # Load dataset
    trial_data_path = f"/home/jason/SPICE-ns-Project/SMOPS2026/data/monte_carlo/trial_{trial}.npz"
    data = np.load(trial_data_path)
    X_test = data['X_test']
    y_test = data['y_test']
    onsets = {
        'volt_drop': data['volt_drop_onset'],
        'wheel_lock': data['wheel_lock_onset'],
        'cpu_leak': data['cpu_leak_onset'],
        'sensor_overheat': data['sensor_overheat_onset'],
        'magnetorquer_short': data['magnetorquer_short_onset'],
        'comms_drop': data['comms_drop_onset']
    }
    
    # Load model
    trial_model_path = f"/home/jason/SPICE-ns-Project/SMOPS2026/models/model_trial_{trial}.pth"
    model_params = torch.load(trial_model_path, weights_only=False)
    
    # Run evaluation
    test_mse, preds, delays, far, base_b, trans_b, reduction, b_factor, precision, recall, f1 = \
        evaluate_testing(X_test, y_test, model_params, onsets)
        
    # Save results
    results_path = os.path.join(results_dir, f"results_trial_{trial}.npz")
    np.savez(results_path,
             test_mse=test_mse,
             predicted_anomalies=preds,
             volt_drop_delay=delays['volt_drop'],
             wheel_lock_delay=delays['wheel_lock'],
             cpu_leak_delay=delays['cpu_leak'],
             sensor_overheat_delay=delays['sensor_overheat'],
             magnetorquer_short_delay=delays['magnetorquer_short'],
             comms_drop_delay=delays['comms_drop'],
             far=far,
             precision=precision,
             recall=recall,
             f1=f1,
             baseline_bytes=base_b,
             transmitted_bytes=trans_b,
             reduction_ratio=reduction,
             bandwidth_factor=b_factor)
             
    if trial % 10 == 0 or trial == 1:
        print(f"Test evaluated for Trial [{trial}/{num_trials}] | F1-Score: {f1*100.2:.2f}% | Savings: {reduction:.2f}% | FAR: {far:.2f}%")

# -------------------------------------------------------------------------
# Step 2: Evaluate Representative Model (for plotting)
# -------------------------------------------------------------------------
print("--- Evaluating Representative Test Dataset ---")
rep_data_path = "/home/jason/SPICE-ns-Project/SMOPS2026/data/representative.npz"
data_rep = np.load(rep_data_path)
X_test_rep = data_rep['X_test']
y_test_rep = data_rep['y_test']
onsets_rep = {
    'volt_drop': data_rep['volt_drop_onset'],
    'wheel_lock': data_rep['wheel_lock_onset'],
    'cpu_leak': data_rep['cpu_leak_onset'],
    'sensor_overheat': data_rep['sensor_overheat_onset'],
    'magnetorquer_short': data_rep['magnetorquer_short_onset'],
    'comms_drop': data_rep['comms_drop_onset']
}

rep_model_path = "/home/jfp" # Wait, let's keep the exact original representative model loading path!
rep_model_path = "/home/jason/SPICE-ns-Project/SMOPS2026/models/model_representative.pth"
model_params_rep = torch.load(rep_model_path, weights_only=False)

test_mse_rep, preds_rep, delays_rep, far_rep, base_b_rep, trans_b_rep, reduction_rep, b_factor_rep, prec_rep, rec_rep, f1_rep = \
    evaluate_testing(X_test_rep, y_test_rep, model_params_rep, onsets_rep)

rep_results_path = os.path.join(results_dir, "results_representative.npz")
np.savez(rep_results_path,
         test_mse=test_mse_rep,
         predicted_anomalies=preds_rep,
         volt_drop_delay=delays_rep['volt_drop'],
         wheel_lock_delay=delays_rep['wheel_lock'],
         cpu_leak_delay=delays_rep['cpu_leak'],
         sensor_overheat_delay=delays_rep['sensor_overheat'],
         magnetorquer_short_delay=delays_rep['magnetorquer_short'],
         comms_drop_delay=delays_rep['comms_drop'],
         far=far_rep,
         precision=prec_rep,
         recall=rec_rep,
         f1=f1_rep,
         baseline_bytes=base_b_rep,
         transmitted_bytes=trans_b_rep,
         reduction_ratio=reduction_rep,
         bandwidth_factor=b_factor_rep)

print("Testing phase complete. All predictions and metric logs saved.")
