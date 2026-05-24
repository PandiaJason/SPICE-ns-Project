"""
Synthetic Mars Surface Feature Dataset Generator and Partitioning.
Generates non-IID local datasets for SmallSats.
"""
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from simulation.config import (
    INPUT_DIM, NUM_CLASSES, DATA_DIR, SEED, NUM_SATELLITES, BATCH_SIZE
)

class MarsSpectralDataset(Dataset):
    """
    Synthetic dataset representing raw multispectral/spectrometric signatures
    captured by Mars orbiting SmallSats.
    """
    def __init__(self, data, labels):
        self.data = torch.tensor(data, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

def generate_mars_data(num_samples=6000, seed=SEED):
    """
    Generates synthetic spectral observations of 5 different Mars surface features:
    0: Background plains
    1: Crater boundaries (high frequency variations)
    2: Dust storms (broadband attenuation at shorter wavelengths)
    3: Subsurface water ice (specific absorption bands)
    4: Volcanic venting / hydrothermal anomalies (thermal peak at long wavelengths)
    """
    np.random.seed(seed)
    data = []
    labels = []
    
    samples_per_class = num_samples // NUM_CLASSES
    w = np.linspace(0, 1, INPUT_DIM)
    
    for c in range(NUM_CLASSES):
        for _ in range(samples_per_class):
            # Base background
            noise = np.random.normal(0.2, 0.05, INPUT_DIM)
            
            if c == 0:
                # Background plains: mostly quiet
                sig = noise + 0.1 * w
            elif c == 1:
                # Crater boundaries: high frequency fluctuations
                sig = noise + 0.3 * np.sin(20 * np.pi * w) * np.exp(-3 * (w - 0.5)**2)
            elif c == 2:
                # Dust storms: broadband attenuation (dust scattering)
                # Lower wavelengths (low indices) are highly attenuated, higher ones less
                sig = noise + 0.5 * (1.0 - np.exp(-3 * w))
            elif c == 3:
                # Subsurface water ice: specific absorption dips at 0.25, 0.5, 0.75
                dips = 1.0 - 0.4 * (
                    np.exp(-100 * (w - 0.25)**2) + 
                    np.exp(-100 * (w - 0.50)**2) + 
                    np.exp(-100 * (w - 0.75)**2)
                )
                sig = (noise + 0.3) * dips
            elif c == 4:
                # Volcanic/hydrothermal anomaly: thermal radiation peak
                sig = noise + 0.6 * np.exp(4 * (w - 0.8)) / np.exp(4)
                
            # Add absolute normalization to make features distinct
            sig = (sig - np.min(sig)) / (np.max(sig) - np.min(sig) + 1e-6)
            data.append(sig)
            labels.append(c)
            
    data = np.array(data)
    labels = np.array(labels)
    
    # Shuffle
    indices = np.arange(len(data))
    np.random.shuffle(indices)
    return data[indices], labels[indices]

def partition_non_iid(data, labels, num_satellites=NUM_SATELLITES, seed=SEED):
    """
    Partitions the dataset in a highly non-IID fashion across the satellites.
    To simulate orbital geography:
    - Sat A orbits polar region: sees mostly background and water ice (Class 0 and 3)
    - Sat B orbits equatorial crater fields: sees mostly craters (Class 1)
    - Sat C orbits dusty plains: sees mostly dust storms (Class 2)
    - Sat D orbits volcanic Tharsis region: sees volcanic anomalies (Class 4)
    - Sat E is in a general orbit: has a mix of classes but mostly background (Class 0)
    """
    np.random.seed(seed)
    sat_data = {i: [] for i in range(num_satellites)}
    sat_labels = {i: [] for i in range(num_satellites)}
    
    # Group samples by class
    class_indices = {c: np.where(labels == c)[0] for c in range(NUM_CLASSES)}
    for c in range(NUM_CLASSES):
        np.random.shuffle(class_indices[c])
        
    # Distribution matrix (rows = satellites, columns = classes)
    # The value represents the fraction of that class assigned to the satellite
    dist_matrix = np.array([
        [0.45, 0.05, 0.05, 0.40, 0.05], # Sat A (Polar: Background + Ice)
        [0.10, 0.60, 0.10, 0.10, 0.10], # Sat B (Crater field)
        [0.10, 0.10, 0.60, 0.10, 0.10], # Sat C (Dust storms)
        [0.05, 0.05, 0.05, 0.05, 0.80], # Sat D (Volcanic region)
        [0.30, 0.20, 0.20, 0.35, 0.15]  # Sat E (Mixed/General)
    ])
    
    # Normalize matrix rows just in case
    dist_matrix = dist_matrix / dist_matrix.sum(axis=0)
    
    class_ptrs = {c: 0 for c in range(NUM_CLASSES)}
    
    for c in range(NUM_CLASSES):
        indices = class_indices[c]
        num_samples_class = len(indices)
        
        for sat in range(num_satellites):
            frac = dist_matrix[sat, c]
            count = int(np.floor(frac * num_samples_class))
            start = class_ptrs[c]
            end = start + count
            
            selected_indices = indices[start:end]
            sat_data[sat].extend(data[selected_indices])
            sat_labels[sat].extend(labels[selected_indices])
            class_ptrs[c] = end
            
    # Convert list to array
    for sat in range(num_satellites):
        sat_data[sat] = np.array(sat_data[sat])
        sat_labels[sat] = np.array(sat_labels[sat])
        
        # Shuffle local data
        idx = np.arange(len(sat_data[sat]))
        np.random.shuffle(idx)
        sat_data[sat] = sat_data[sat][idx]
        sat_labels[sat] = sat_labels[sat][idx]
        
    return sat_data, sat_labels

def get_loaders(batch_size=BATCH_SIZE, num_samples=6000, test_ratio=0.2):
    """
    Generates, partitions, and packages local train loaders and a global test loader.
    """
    data, labels = generate_mars_data(num_samples=num_samples)
    
    # Split train/test
    split_idx = int(len(data) * (1 - test_ratio))
    train_data, train_labels = data[:split_idx], labels[:split_idx]
    test_data, test_labels = data[split_idx:], labels[split_idx:]
    
    # Partition train data
    sat_train_data, sat_train_labels = partition_non_iid(train_data, train_labels)
    
    # Create loaders
    train_loaders = {}
    for sat_id, s_data in sat_train_data.items():
        dataset = MarsSpectralDataset(s_data, sat_train_labels[sat_id])
        train_loaders[sat_id] = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
    test_dataset = MarsSpectralDataset(test_data, test_labels)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loaders, test_loader
