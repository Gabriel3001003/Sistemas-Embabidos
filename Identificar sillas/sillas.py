from ultralytics import YOLO
import cv2

# Carga el modelo YOLO (preentrenado)
model = YOLO("yolov8n.pt")

# Captura desde la cámara
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detecta objetos
    results = model(frame)

    # Lista de detecciones
    chairs = []
    persons = []

    for r in results[0].boxes:
        cls = model.names[int(r.cls)]
        x1, y1, x2, y2 = map(int, r.xyxy[0])
        if cls == "chair":
            chairs.append((x1, y1, x2, y2))
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        elif cls == "person":
            persons.append((x1, y1, x2, y2))
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Determinar sillas ocupadas (si una persona se superpone)
    ocupadas = 0
    for cx1, cy1, cx2, cy2 in chairs:
        chair_box = (cx1, cy1, cx2, cy2)
        for px1, py1, px2, py2 in persons:
            if px1 < cx2 and px2 > cx1 and py1 < cy2 and py2 > cy1:
                ocupadas += 1
                break

    libres = len(chairs) - ocupadas

    cv2.putText(frame, f"Sillas libres: {libres}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Deteccion de Sillas", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
