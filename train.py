import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
import torch.onnx
import random

# --- 0. Reproductibilité (Seed 42) ---
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

set_seed(42)

# --- 1. Définition du Modèle (Architecture conservée) ---
class VesteCNN(nn.Module):
    def __init__(self):
        super(VesteCNN, self).__init__()
        # Batch Norm pour stabiliser l'entrée (dérivée)
        self.bn = nn.BatchNorm1d(1)
        
        # Conv 1
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3)
        self.pool = nn.MaxPool1d(kernel_size=2)
        
        # Conv 2
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=32, kernel_size=3)
        
        # Global Average Pooling
        self.gap = nn.AdaptiveAvgPool1d(1)
        
        # Sortie
        self.fc = nn.Linear(32, 4) # 4 classes

    def forward(self, x):
        x = self.bn(x)
        x = torch.relu(self.conv1(x))
        x = self.pool(x)
        x = torch.relu(self.conv2(x))
        x = self.gap(x)
        x = x.squeeze(-1) # Aplatir (Batch, 32, 1) -> (Batch, 32)
        x = self.fc(x)
        return x 

# --- 2. Préparation des Données ---
print("Chargement des données...")
# Assure-toi que le fichier existe, sinon le script plantera
try:
    df = pd.read_csv("dataset_touch.csv")
except FileNotFoundError:
    # Génération de fausses données juste pour que le script tourne si tu n'as pas le csv sous la main
    # A SUPPRIMER si tu as ton vrai fichier
    print("Fichier non trouvé, génération de données aléatoires pour l'exemple...")
    data = np.random.randn(150, 101)
    df = pd.DataFrame(data)
    df.columns = [str(i) for i in range(100)] + ['label']
    df['label'] = np.random.randint(0, 4, 150)

X_raw = df.iloc[:, :-1].values.astype(np.float32) # Les 100 points bruts
y = df['label'].values.astype(np.longlong)

# *** CRUCIAL : CALCUL DE LA DÉRIVÉE (Logique conservée) ***
X_diff = np.diff(X_raw, axis=1)
X_diff = np.hstack((np.zeros((X_diff.shape[0], 1), dtype=np.float32), X_diff))

# Reshape pour PyTorch : (Batch, Channels, Length) -> (N, 1, 100)
X_diff = X_diff.reshape(-1, 1, 100)

# Split Train/Test 80% / 20%
# AJOUT : stratify=y permet de garder la même proportion de classes dans le train et le test
X_train, X_test, y_train, y_test = train_test_split(
    X_diff, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Taille Train: {len(X_train)}, Taille Test: {len(X_test)}")

# Création des DataLoaders
train_dataset = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
test_dataset = TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_test))

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# --- 3. Entraînement ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = VesteCNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

print(f"Début de l'entraînement sur {device} pour 750 époques...")

EPOCHS = 300
train_losses = []
val_losses = []

for epoch in range(EPOCHS):
    # -- Phase d'entraînement --
    model.train()
    running_loss = 0.0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
    
    avg_train_loss = running_loss / len(train_loader)
    train_losses.append(avg_train_loss)
    
    # -- Phase de validation (sur le jeu de test) --
    model.eval()
    running_val_loss = 0.0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_val_loss += loss.item()
            
    avg_val_loss = running_val_loss / len(test_loader)
    val_losses.append(avg_val_loss)
    
    if (epoch + 1) % 50 == 0:
        print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

# --- 4. Évaluation & Visualisation ---

# A. Courbes de Loss
plt.figure(figsize=(10, 5))
plt.plot(train_losses, label='Train Loss')
plt.plot(val_losses, label='Validation Loss', linestyle='--')
plt.title('Courbe de Loss (Entraînement vs Validation)')
plt.xlabel('Époques')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.savefig('loss_curve.png') # Sauvegarde du graphe
plt.show()

# B. Calcul Précision et Matrice de Confusion
model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for inputs, labels in test_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

# Calcul précision globale
correct = sum([p == l for p, l in zip(all_preds, all_labels)])
accuracy = 100 * correct / len(all_labels)
print(f"Précision finale sur le test set : {accuracy:.2f}%")

# C. Matrice de Confusion
cm = confusion_matrix(all_labels, all_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=[0,1,2,3], yticklabels=[0,1,2,3])
plt.title('Matrice de Confusion')
plt.xlabel('Prédictions')
plt.ylabel('Vérité Terrain')
plt.savefig('confusion_matrix.png')
plt.show()

# --- 5. Export ONNX ---
print("Exportation en ONNX...")
dummy_input = torch.randn(1, 1, 100).to(device)
torch.onnx.export(model, 
                  dummy_input, 
                  "veste_model.onnx", 
                  input_names=['input'], 
                  output_names=['output'],
                  dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})

print("Modèle sauvegardé sous 'veste_model.onnx' !")
