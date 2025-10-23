# yes_no_detector.py
import os
import numpy as np
import librosa
import tensorflow as tf
from sklearn.model_selection import train_test_split

# -------------------------------
# 1️⃣ Configuración
# -------------------------------
DATASET_PATH = r"C:\Users\elgab\Downloads\speech_commands"  # carpeta con 'yes' y 'no'
SAMPLE_RATE = 16000
DURATION = 1  # segundos
SAMPLES_PER_FILE = SAMPLE_RATE * DURATION
MFCC_FEATURES = 13
MFCC_MAX_LEN = 32  # número de columnas fijas

# -------------------------------
# 2️⃣ Función para extraer MFCC con tamaño fijo
# -------------------------------
def extract_mfcc(file_path):
    audio, sr = librosa.load(file_path, sr=SAMPLE_RATE)
    if len(audio) < SAMPLES_PER_FILE:
        audio = np.pad(audio, (0, SAMPLES_PER_FILE - len(audio)))
    else:
        audio = audio[:SAMPLES_PER_FILE]

    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=MFCC_FEATURES)
    # Ajustar columnas a MFCC_MAX_LEN
    if mfcc.shape[1] < MFCC_MAX_LEN:
        mfcc = np.pad(mfcc, ((0,0),(0, MFCC_MAX_LEN - mfcc.shape[1])), mode='constant')
    else:
        mfcc = mfcc[:, :MFCC_MAX_LEN]
    return mfcc

# -------------------------------
# 3️⃣ Cargar dataset
# -------------------------------
print("Cargando dataset...")
labels_dict = {'yes':0, 'no':1}
X, y = [], []

for label, idx in labels_dict.items():
    folder = os.path.join(DATASET_PATH, label)
    for file in os.listdir(folder):
        if file.endswith(".wav"):
            file_path = os.path.join(folder, file)
            mfcc = extract_mfcc(file_path)
            X.append(mfcc)
            y.append(idx)

X = np.array(X)
y = np.array(y)
X = X[..., np.newaxis]  # Añadir canal para CNN

# -------------------------------
# 4️⃣ Separar train/test
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# -------------------------------
# 5️⃣ Crear CNN
# -------------------------------
model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(16, (3,3), activation='relu', input_shape=(MFCC_FEATURES, MFCC_MAX_LEN,1)),
    tf.keras.layers.MaxPooling2D((2,2)),
    tf.keras.layers.Conv2D(32, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D((2,2)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(2, activation='softmax')  # 2 clases: yes/no
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.summary()

# -------------------------------
# 6️⃣ Entrenar
# -------------------------------
print("Entrenando modelo...")
history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=15, batch_size=16)

# -------------------------------
# 7️⃣ Guardar modelo
# -------------------------------
model.save("yes_no_model.h5")
print("Modelo guardado como yes_no_model.h5")

# -------------------------------
# 8️⃣ (Opcional) Prueba con un archivo
# -------------------------------
def predict_file(file_path):
    mfcc = extract_mfcc(file_path)
    mfcc = mfcc[np.newaxis, ..., np.newaxis]
    pred = model.predict(mfcc)
    labels = ['yes', 'no']
    return labels[np.argmax(pred)]

# Ejemplo:
# print(predict_file(r"C:\Users\elgab\Downloads\yes_no_dataset\yes\0a7c2a8d_nohash_0.wav"))
