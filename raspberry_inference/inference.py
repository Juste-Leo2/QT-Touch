from gpiozero import MCP3008
import onnxruntime as ort
import numpy as np
import time
import collections
from collections import Counter

# --- 1. CONFIGURATION MATÉRIELLE ---
adc = MCP3008(channel=0, clock_pin=12, mosi_pin=20, miso_pin=16, select_pin=21)

# --- 2. CONFIGURATION SYSTÈME ---
ACQUISITION_FREQ = 1000  # Fréquence de la boucle principale (1 kHz)
DOWNSAMPLING = 10        # On prend 10 échantillons à 1kHz pour faire 1 point à 100Hz
# Fréquence effective pour l'IA = 1000 / 10 = 100 Hz (Celle du modèle)

# --- 3. CONFIGURATION IA ---
MODEL_PATH = "veste_model.onnx"
CLASSES = ["Rien", "Tape", "Pincement", "Frottement"]
WINDOW_SIZE = 100        # Fenêtre de l'IA (100 points à 100Hz = 1 seconde)

# --- 4. CONFIGURATION DÉCISION & VOTE ---
INFERENCE_STRIDE = 5     # On ne lance l'IA que tous les 5 points "utiles" (donc à 20Hz)
VOTE_WINDOW_SIZE = 5     # Taille du vote majoritaire
SCORE_THRESHOLD = 0.80   
SEUIL_STABILITE = 0.008  

# --- CHARGEMENT ---
print(f"Chargement du modèle {MODEL_PATH}...")
try:
    session = ort.InferenceSession(MODEL_PATH)
    input_name = session.get_inputs()[0].name
except Exception as e:
    print(f"Erreur : {e}")
    exit()

# Buffers
raw_buffer = collections.deque(maxlen=WINDOW_SIZE)  # Buffer 100Hz pour l'IA
vote_buffer = collections.deque(maxlen=VOTE_WINDOW_SIZE)
accumulator = [] # Petit buffer temporaire pour stocker les 10 échantillons du 1kHz

# Remplissage initial (pour éviter les erreurs au démarrage)
for _ in range(WINDOW_SIZE):
    raw_buffer.append(0.0)
for _ in range(VOTE_WINDOW_SIZE):
    vote_buffer.append(0)

print("\n--- SYSTÈME CADENCÉ À 1 KHz ---")
print(f"Boucle acquisition : {ACQUISITION_FREQ} Hz (1ms)")
print(f"Signal traité (Moyenne) : {ACQUISITION_FREQ/DOWNSAMPLING:.0f} Hz")
print(f"Analyse IA : 1 fois tous les {INFERENCE_STRIDE} points traités")
print("CTRL+C pour arrêter\n")

try:
    last_print_time = 0
    points_processed_counter = 0 # Compteur de points 100Hz générés
    
    while True:
        loop_start = time.time()
        
        # --- A. LECTURE (1 kHz) ---
        val = adc.value
        accumulator.append(val)
        
        # --- B. TRAITEMENT (Seulement si on a accumulé 10 valeurs) ---
        if len(accumulator) >= DOWNSAMPLING:
            
            # 1. Calcul de la moyenne (Downsampling 1kHz -> 100Hz)
            avg_val = sum(accumulator) / len(accumulator)
            accumulator = [] # On vide l'accumulateur pour le prochain cycle
            
            # 2. Ajout au buffer de l'IA
            raw_buffer.append(avg_val)
            points_processed_counter += 1
            
            # --- C. INTELLIGENCE ARTIFICIELLE (Cadencée par le STRIDE) ---
            # On ne lance l'IA que si on est sur un "temps fort" (ex: tous les 5 points 100Hz)
            if points_processed_counter % INFERENCE_STRIDE == 0:
                
                raw_signal = np.array(raw_buffer, dtype=np.float32)
                ecart_type = np.std(raw_signal)
                
                instant_pred = 0
                
                # Check Stabilité (Anti-blocage)
                if ecart_type >= SEUIL_STABILITE:
                    derivative = np.diff(raw_signal)
                    derivative = np.insert(derivative, 0, 0)
                    input_data = derivative.reshape(1, 1, 100)
                    
                    outputs = session.run(None, {input_name: input_data})
                    logits = outputs[0][0]
                    probs = np.exp(logits) / np.sum(np.exp(logits))
                    
                    if np.max(probs) > SCORE_THRESHOLD:
                        instant_pred = np.argmax(probs)
                
                # --- D. VOTE ---
                vote_buffer.append(instant_pred)
                winner_class, winner_count = Counter(vote_buffer).most_common(1)[0]
                
                # --- E. AFFICHAGE ---
                if winner_class != 0:
                    if time.time() - last_print_time > 0.15:
                        nom = CLASSES[winner_class]
                        sym = "!" if winner_class == 1 else ("~" if winner_class == 3 else "=")
                        print(f"{sym*3} {nom} ({winner_count}/{VOTE_WINDOW_SIZE}) [Std:{ecart_type:.4f}]")
                        last_print_time = time.time()

        # --- F. CADENCEMENT STRICT 1 kHz ---
        # On calcule combien de temps le CPU a travaillé
        elapsed = time.time() - loop_start
        # On dort juste ce qu'il faut pour compléter la milliseconde
        sleep_time = (1.0 / ACQUISITION_FREQ) - elapsed
        
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\nArrêt.")
