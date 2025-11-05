import cv2
import imutils
import numpy as np

# --- Configuración ---
PROTOTXT = "MobileNetSSD_deploy.prototxt"
MODEL = "MobileNetSSD_deploy.caffemodel"
CONF_THRESHOLD = 0.5  # Umbral de confianza
CAM_INDEX = 0         # Índice de cámara

# Clases del modelo
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

# Cargar el modelo
print("[INFO] Cargando modelo...")
net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)

# Iniciar cámara
cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise IOError("No se pudo acceder a la cámara.")

print("[INFO] Detección iniciada. Presiona 'q' para salir.")
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Redimensionar para mejorar rendimiento
    frame = imutils.resize(frame, width=600)
    (h, w) = frame.shape[:2]

    # Crear blob y pasar por la red
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    # Iterar sobre las detecciones
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < CONF_THRESHOLD:
            continue

        idx = int(detections[0, 0, i, 1])
        if CLASSES[idx] != "person":
            continue

        # Dibujar rectángulo en la persona
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")

        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        label = f"Persona: {confidence:.2f}"
        cv2.putText(frame, label, (startX, startY - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Detección de Personas", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
print("[INFO] Finalizado.")
