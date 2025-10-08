import cv2
import os
import time
from datetime import datetime
import uuid
import imutils
import numpy as np

# --- Configuración ---
PROTOTXT = "MobileNetSSD_deploy.prototxt"   # ruta al prototxt
MODEL    = "MobileNetSSD_deploy.caffemodel" # ruta al caffemodel
CONF_THRESHOLD = 0.5   # umbral de confianza para considerar detección como persona

OUT_DIR_WITH_PERSON = "with_person"
OUT_DIR_NO_PERSON   = "no_person"
SAVE_CROPS = True     # si True guarda solo el recorte de la persona; si False guarda el fotograma completo en with_person
MAX_SAVE_RATE = 1.0   # segundos entre guardados para evitar demasiados archivos (por persona)
CAM_INDEX = 0         # índice de la cámara (0 por defecto)

# clases del MobileNet-SSD (orden del modelo)
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

# Crear carpetas si no existen
os.makedirs(OUT_DIR_WITH_PERSON, exist_ok=True)
os.makedirs(OUT_DIR_NO_PERSON, exist_ok=True)

# Cargar modelo
print("[INFO] Cargando modelo...")
net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)

# Abrir cámara
vs = cv2.VideoCapture(CAM_INDEX)
if not vs.isOpened():
    raise IOError(f"No se pudo abrir la cámara con índice {CAM_INDEX}")

last_save_time = 0.0

print("[INFO] Iniciando captura. Presiona 'q' para salir, 'c' para guardar manualmente el frame actual.")
while True:
    ret, frame = vs.read()
    if not ret:
        print("[WARN] No se recibió frame de la cámara, intentando de nuevo...")
        time.sleep(0.1)
        continue

    # Redimensionar (opcional) para acelerar
    frame = imutils.resize(frame, width=600)
    (h, w) = frame.shape[:2]

    # Crear blob y hacer forward
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    found_person = False
    person_crops = []

    # Iterar detecciones
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < CONF_THRESHOLD:
            continue

        idx = int(detections[0, 0, i, 1])
        if CLASSES[idx] != "person":
            continue

        # Encontramos una persona
        found_person = True
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")

        # Ajustar límites
        startX = max(0, startX)
        startY = max(0, startY)
        endX = min(w - 1, endX)
        endY = min(h - 1, endY)

        # Dibujar caja y confianza
        label = f"Person: {confidence:.2f}"
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        y = startY - 10 if startY - 10 > 10 else startY + 10
        cv2.putText(frame, label, (startX, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

        # recortar persona
        crop = frame[startY:endY, startX:endX].copy()
        person_crops.append((crop, confidence))

    # Mostrar frame
    cv2.imshow("Detector de Personas", frame)

    now = time.time()
    # Guardado automático respetando MAX_SAVE_RATE
    if found_person and (now - last_save_time) >= MAX_SAVE_RATE:
        # Guardar cada recorte de persona
        for crop, confidence in person_crops:
            if SAVE_CROPS and crop.size != 0:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{int(confidence*100)}.jpg"
                path = os.path.join(OUT_DIR_WITH_PERSON, filename)
                cv2.imwrite(path, crop)
            else:
                # guardar frame completo con marca
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{int(confidence*100)}.jpg"
                path = os.path.join(OUT_DIR_WITH_PERSON, filename)
                cv2.imwrite(path, frame)
        last_save_time = now
    elif not found_person and (now - last_save_time) >= MAX_SAVE_RATE:
        # guardar frame completo en carpeta de no_person
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
        path = os.path.join(OUT_DIR_NO_PERSON, filename)
        cv2.imwrite(path, frame)
        last_save_time = now

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("c"):
        # Guardado manual del frame actual (en with_person o no_person según detección)
        if found_person:
            for crop, confidence in person_crops:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_manual_{int(confidence*100)}.jpg"
                path = os.path.join(OUT_DIR_WITH_PERSON, filename) if SAVE_CROPS else os.path.join(OUT_DIR_WITH_PERSON, filename)
                cv2.imwrite(path, crop if SAVE_CROPS else frame)
        else:
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_manual.jpg"
            path = os.path.join(OUT_DIR_NO_PERSON, filename)
            cv2.imwrite(path, frame)

# Liberar recursos
vs.release()
cv2.destroyAllWindows()
print("[INFO] Finalizado.")
