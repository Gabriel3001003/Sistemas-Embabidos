import cv2
import numpy as np
import time

# --- Configuración ---
PROTOTXT = "MobileNetSSD_deploy.prototxt"
MODEL = "MobileNetSSD_deploy.caffemodel"
CONF_THRESHOLD = 0.5
CAM_INDEX = 0  # índice de cámara USB o CSI

# Clases del modelo
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

# Cargar modelo
print("[INFO] Cargando modelo...")
net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# Iniciar cámara
vs = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
vs.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not vs.isOpened():
    raise IOError(f"No se pudo abrir la cámara con índice {CAM_INDEX}")

print("[INFO] Iniciando seguimiento de personas. Presiona 'q' para salir.")
time.sleep(1.0)

while True:
    ret, frame = vs.read()
    if not ret:
        print("[WARN] No se recibió frame de la cámara.")
        time.sleep(0.1)
        continue

    target_width = 600
    scale = target_width / frame.shape[1]
    frame = cv2.resize(frame, (target_width, int(frame.shape[0] * scale)))
    (h, w) = frame.shape[:2]

    # Crear blob y pasar por la red
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    person_center = None

    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < CONF_THRESHOLD:
            continue

        idx = int(detections[0, 0, i, 1])
        if CLASSES[idx] != "person":
            continue

        # Dibujar caja
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")

        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
        label = f"Person: {confidence:.2f}"
        cv2.putText(frame, label, (startX, startY - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Calcular el centro de la persona
        person_center = ((startX + endX) // 2, (startY + endY) // 2)
        cv2.circle(frame, person_center, 5, (0, 0, 255), -1)

        break  # Solo seguir a la primera persona detectada

    # Dibujar centro del frame
    frame_center = (w // 2, h // 2)
    cv2.circle(frame, frame_center, 5, (255, 0, 0), -1)

    if person_center:
        # Calcular desplazamiento (x,y)
        dx = person_center[0] - frame_center[0]
        dy = person_center[1] - frame_center[1]

        # Dibujar flecha de seguimiento
        cv2.arrowedLine(frame, frame_center, person_center, (0, 0, 255), 2)
        direction = ""

        # Mostrar dirección (simulación de movimiento)
        if abs(dx) > 30:
            if dx > 0:
                direction += "➡️ Derecha "
            else:
                direction += "⬅️ Izquierda "
        if abs(dy) > 30:
            if dy > 0:
                direction += "⬇️ Abajo"
            else:
                direction += "⬆️ Arriba"

        if direction == "":
            direction = "🟢 Centrado"

        cv2.putText(frame, f"Seguir: {direction}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    else:
        cv2.putText(frame, "No hay persona detectada", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow("Seguidor de Personas", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vs.release()
cv2.destroyAllWindows()
print("[INFO] Finalizado.")
