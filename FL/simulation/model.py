"""
SpaceModel and Training Utilities for Federated Learning on SmallSats.
Supports dynamic layer-based structured pruning and proximal regularization (FedProx).
"""
import copy
import torch
import torch.nn as nn
import torch.nn.functional as F
from simulation.config import (
    INPUT_DIM, HIDDEN_DIM_1, HIDDEN_DIM_2, NUM_CLASSES,
    PRUNED_HIDDEN_DIM_1, PRUNED_HIDDEN_DIM_2, LEARNING_RATE
)

class SpaceModel(nn.Module):
    """
    Multi-layer Perceptron (MLP) for spectral feature classification.
    Supports dynamic sub-network extraction (structured pruning) when battery is low.
    """
    def __init__(self, input_dim=INPUT_DIM, h1=HIDDEN_DIM_1, h2=HIDDEN_DIM_2, 
                 num_classes=NUM_CLASSES, pruned_h1=PRUNED_HIDDEN_DIM_1, pruned_h2=PRUNED_HIDDEN_DIM_2):
        super(SpaceModel, self).__init__()
        self.input_dim = input_dim
        self.h1 = h1
        self.h2 = h2
        self.num_classes = num_classes
        self.pruned_h1 = pruned_h1
        self.pruned_h2 = pruned_h2
        
        # Define the full network parameters as standard layers
        self.fc1 = nn.Linear(input_dim, h1)
        self.fc2 = nn.Linear(h1, h2)
        self.fc3 = nn.Linear(h2, num_classes)
        
    def forward(self, x, mode='full'):
        """
        Forward pass.
        If mode is 'full', uses the entire model.
        If mode is 'pruned', extracts sub-tensors of weights/biases representing a smaller model.
        """
        if mode == 'full':
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            return self.fc3(x)
        elif mode == 'pruned':
            # Sliced weights and biases
            w1 = self.fc1.weight[:self.pruned_h1, :]
            b1 = self.fc1.bias[:self.pruned_h1]
            x = F.relu(F.linear(x, w1, b1))
            
            w2 = self.fc2.weight[:self.pruned_h2, :self.pruned_h1]
            b2 = self.fc2.bias[:self.pruned_h2]
            x = F.relu(F.linear(x, w2, b2))
            
            w3 = self.fc3.weight[:, :self.pruned_h2]
            b3 = self.fc3.bias
            return F.linear(x, w3, b3)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def get_weights(self, mode='full'):
        """
        Returns a dict of state tensors. If mode is pruned, returns only the sliced parameters
        to simulate smaller transmission size.
        """
        if mode == 'full':
            return {name: param.data.clone() for name, param in self.named_parameters()}
        elif mode == 'pruned':
            return {
                'fc1.weight': self.fc1.weight.data[:self.pruned_h1, :].clone(),
                'fc1.bias': self.fc1.bias.data[:self.pruned_h1].clone(),
                'fc2.weight': self.fc2.weight.data[:self.pruned_h2, :self.pruned_h1].clone(),
                'fc2.bias': self.fc2.bias.data[:self.pruned_h2].clone(),
                'fc3.weight': self.fc3.weight.data[:, :self.pruned_h2].clone(),
                'fc3.bias': self.fc3.bias.data.clone()  # bias size is same as output size
            }
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def load_weights(self, weights_dict, mode='full'):
        """
        Loads weights from a dict. If mode is pruned, only writes to the sub-tensor slice.
        """
        with torch.no_grad():
            if mode == 'full':
                for name, param in self.named_parameters():
                    if name in weights_dict:
                        param.copy_(weights_dict[name])
            elif mode == 'pruned':
                self.fc1.weight.data[:self.pruned_h1, :].copy_(weights_dict['fc1.weight'])
                self.fc1.bias.data[:self.pruned_h1].copy_(weights_dict['fc1.bias'])
                self.fc2.weight.data[:self.pruned_h2, :self.pruned_h1].copy_(weights_dict['fc2.weight'])
                self.fc2.bias.data[:self.pruned_h2].copy_(weights_dict['fc2.bias'])
                self.fc3.weight.data[:, :self.pruned_h2].copy_(weights_dict['fc3.weight'])
                self.fc3.bias.data.copy_(weights_dict['fc3.bias'])
            else:
                raise ValueError(f"Unknown mode: {mode}")

def local_train(model, dataloader, epochs, mode='full', mu=0.0, global_weights=None, lr=LEARNING_RATE):
    """
    Trains a model locally on client data.
    - mode: 'full' or 'pruned' (determines architecture complexity)
    - mu: FedProx regularization parameter. If mu > 0 and global_weights is provided,
          adds proximal term to penalize divergence from the global model.
    """
    model.train()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    
    # Store global parameters if FedProx is active
    if mu > 0.0 and global_weights is not None:
        global_tensors = {}
        for name, param in model.named_parameters():
            if name in global_weights:
                global_tensors[name] = global_weights[name].to(param.device)
    else:
        mu = 0.0
        
    for epoch in range(epochs):
        for inputs, targets in dataloader:
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(inputs, mode=mode)
            loss = criterion(outputs, targets)
            
            # FedProx Proximal Regularization
            if mu > 0.0:
                prox_loss = 0.0
                if mode == 'full':
                    for name, param in model.named_parameters():
                        if name in global_tensors:
                            prox_loss += torch.sum((param - global_tensors[name]) ** 2)
                elif mode == 'pruned':
                    # Only regularize the pruned active parameters
                    w1_diff = model.fc1.weight[:model.pruned_h1, :] - global_tensors['fc1.weight']
                    b1_diff = model.fc1.bias[:model.pruned_h1] - global_tensors['fc1.bias']
                    w2_diff = model.fc2.weight[:model.pruned_h2, :model.pruned_h1] - global_tensors['fc2.weight']
                    b2_diff = model.fc2.bias[:model.pruned_h2] - global_tensors['fc2.bias']
                    w3_diff = model.fc3.weight[:, :model.pruned_h2] - global_tensors['fc3.weight']
                    b3_diff = model.fc3.bias - global_tensors['fc3.bias']
                    
                    prox_loss += torch.sum(w1_diff ** 2) + torch.sum(b1_diff ** 2)
                    prox_loss += torch.sum(w2_diff ** 2) + torch.sum(b2_diff ** 2)
                    prox_loss += torch.sum(w3_diff ** 2) + torch.sum(b3_diff ** 2)
                    
                loss += (mu / 2.0) * prox_loss
                
            loss.backward()
            
            # If pruned mode, zero out gradients for inactive weights
            # to make sure we don't update them during SGD step
            if mode == 'pruned':
                with torch.no_grad():
                    # Gradients outside the slices are set to 0
                    if model.fc1.weight.grad is not None:
                        model.fc1.weight.grad[model.pruned_h1:, :] = 0.0
                    if model.fc1.bias.grad is not None:
                        model.fc1.bias.grad[model.pruned_h1:] = 0.0
                    if model.fc2.weight.grad is not None:
                        model.fc2.weight.grad[model.pruned_h2:, :] = 0.0
                        model.fc2.weight.grad[:, model.pruned_h1:] = 0.0
                    if model.fc2.bias.grad is not None:
                        model.fc2.bias.grad[model.pruned_h2:] = 0.0
                    if model.fc3.weight.grad is not None:
                        model.fc3.weight.grad[:, model.pruned_h2:] = 0.0
                        
            optimizer.step()
            
    return model.get_weights(mode=mode)

def evaluate(model, dataloader):
    """
    Evaluates model on global test dataset.
    Returns: accuracy (float, 0-1) and loss (float).
    """
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, targets in dataloader:
            outputs = model(inputs, mode='full')  # Always evaluate on full model
            loss = criterion(outputs, targets)
            total_loss += loss.item() * inputs.size(0)
            
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
    accuracy = correct / total if total > 0 else 0.0
    avg_loss = total_loss / total if total > 0 else 0.0
    return accuracy, avg_loss
