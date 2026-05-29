import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import MinMaxScaler

# Set random seed for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Create models directory
models_dir = "/home/jason/SPICE-ns-Project/SMOPS2026/models"
os.makedirs(models_dir, exist_ok=True)

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

def train_autoencoder(X_train, X_val, epochs=60, batch_size=64):
    # Fit scaler
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Convert to Tensor
    X_train_tensor = torch.FloatTensor(X_train_scaled)
    
    # Define model
    model = MicroAutoencoder(input_dim=31, latent_dim=4)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    # Data loader
    dataset = TensorDataset(X_train_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Train
    model.train()
    for epoch in range(epochs):
        for batch in loader:
            inputs = batch[0]
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, inputs)
            loss.backward()
            optimizer.step()
            
    # Calibration of threshold tau (using validation set)
    # Target False Alarm Rate (FAR) = 1.0% (99th percentile)
    model.eval()
    with torch.no_grad():
        val_recon = model(torch.FloatTensor(X_val_scaled))
        val_mse = torch.mean((torch.FloatTensor(X_val_scaled) - val_recon) ** 2, dim=1).numpy()
    tau = np.percentile(val_mse, 99.0)
    
    return model, scaler, tau

# -------------------------------------------------------------------------
# Step 1: Train Models for Monte Carlo Trials
# -------------------------------------------------------------------------
num_trials = 50
print(f"--- Training {num_trials} Monte Carlo Autoencoder Models ---")

for trial in range(1, num_trials + 1):
    trial_data_path = f"/home/jason/SPICE-ns-Project/SMOPS2026/data/monte_carlo/trial_{trial}.npz"
    data = np.load(trial_data_path)
    X_train = data['X_train']
    X_val = data['X_val']
    
    model, scaler, tau = train_autoencoder(X_train, X_val)
    
    # Save model weights, scaling parameters and threshold
    trial_model_path = os.path.join(models_dir, f"model_trial_{trial}.pth")
    torch.save({
        'state_dict': model.state_dict(),
        'scaler': scaler,
        'threshold': tau
    }, trial_model_path)
    
    if trial % 10 == 0 or trial == 1:
        print(f"Model for Trial [{trial}/{num_trials}] trained and saved (Threshold tau = {tau:.6f})")

# -------------------------------------------------------------------------
# Step 2: Train Representative Model (for plotting)
# -------------------------------------------------------------------------
print("--- Training Representative Autoencoder Model ---")
rep_data_path = "/home/jason/SPICE-ns-Project/SMOPS2026/data/representative.npz"
data_rep = np.load(rep_data_path)
X_train_rep = data_rep['X_train']
X_val_rep = data_rep['X_val']

model_rep, scaler_rep, tau_rep = train_autoencoder(X_train_rep, X_val_rep)

rep_model_path = os.path.join(models_dir, "model_representative.pth")
torch.save({
    'state_dict': model_rep.state_dict(),
    'scaler': scaler_rep,
    'threshold': tau_rep
}, rep_model_path)

print("Training phase complete. All models and calibration parameters saved.")
