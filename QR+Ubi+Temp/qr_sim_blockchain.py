#!/usr/bin/env python3
"""
qr_blockchain_full.py

Versión todo-en-uno para:
 - Generar 2 QRs de ejemplo: qr_simple.png (JSON puro) y qr_firmado.png (HMAC-SHA256)
 - Leer QR real con la cámara (pyzbar + OpenCV)
 - Verificar firma HMAC (si existe) o aceptar JSON simple
 - Generar datos simulados (temp, humedad, lat/lon)
 - Registrar el evento en una blockchain local simple (chain.json)
 - **Generar automáticamente el siguiente QR firmado** que contiene el hash del bloque recién agregado

Uso:
  - Generar QRs de ejemplo:
      python3 qr_blockchain_full.py --generate-qrs

  - Ejecutar el lector y registrar lecturas (usa la cámara por defecto):
      python3 qr_blockchain_full.py

  - Opciones adicionales:
      --timeout N    tiempo de espera en segundos para detectar QR (por defecto 60)
      --secret KEY   clave HMAC en texto (si no se especifica, se usa la incluida)
      --camera IDX   índice de la cámara

Dependencias:
  sudo apt install python3-opencv libzbar0 -y    # (Debian/Ubuntu) si falta
  pip3 install pyzbar qrcode

Notas:
 - Mantén SECRET_KEY fuera de produc-ción; aquí está para pruebas.
 - El QR firmado contiene: base64url(payload_json).base64url(hmac_sha256(payload_json, SECRET_KEY))
 - Después de cada lectura válida y registro, el script crea un nuevo QR firmado llamado qr_next_<index>.png

"""

import os
import sys
import cv2
import json
import time
import random
import argparse
import hashlib
import base64
import hmac
from datetime import datetime
from pyzbar import pyzbar
import qrcode

CHAIN_FILE = "chain.json"
# Clave por defecto (solo para pruebas). En produccion usar variable de entorno o archivo seguro.
DEFAULT_SECRET = b"mi_clave_secreta_32bytes"

# ----------------- Utilidades QR -----------------

def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

# ----------------- Generar QRs de ejemplo -----------------

def generar_qr_ejemplos(secret_key: bytes, out_dir: str = '.'):
    payload = {
        "sku": "ABC123",
        "serial": "0001",
        "batch": "2025-11-01",
        "issuer": "FABRICA_X"
    }

    # QR simple (JSON)
    qr_simple_text = json.dumps(payload, separators=(',', ':'))
    img_simple = qrcode.make(qr_simple_text)
    path_simple = os.path.join(out_dir, 'qr_simple.png')
    img_simple.save(path_simple)

    # QR firmado (HMAC-SHA256, payload ordenado)
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    sig = hmac.new(secret_key, payload_json, hashlib.sha256).digest()
    qr_text = f"{b64url_encode(payload_json)}.{b64url_encode(sig)}"
    img_signed = qrcode.make(qr_text)
    path_signed = os.path.join(out_dir, 'qr_firmado.png')
    img_signed.save(path_signed)

    print(f"QR simple guardado en: {path_simple}")
    print(f"QR firmado guardado en: {path_signed}")
    print("\nContenido QR simple (JSON):")
    print(qr_simple_text)
    print("\nContenido QR firmado (texto dentro del QR):")
    print(qr_text)

# ----------------- Generar siguiente QR firmado (por prev_hash) -----------------

def generar_qr_next_from_hash(prev_hash: str, secret_key: bytes, index: int, out_dir: str = '.'):
    payload = {
        'prev_hash': prev_hash,
        'index': index,
        'issued_at': datetime.utcnow().isoformat() + 'Z'
    }
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    sig = hmac.new(secret_key, payload_json, hashlib.sha256).digest()
    qr_text = f"{b64url_encode(payload_json)}.{b64url_encode(sig)}"
    filename = os.path.join(out_dir, f'qr_next_{index}.png')
    img = qrcode.make(qr_text)
    img.save(filename)
    return filename, qr_text

# ----------------- Lectura de QR por cámara -----------------

def leer_qr_camera(timeout_seconds: int = 60, camera_index: int = 0):
    cam = cv2.VideoCapture(camera_index)
    if not cam.isOpened():
        print("Error: No se pudo abrir la cámara. Verifica el ", camera_index)
        return None

    inicio = time.time()
    print('Abriendo cámara... apunta un QR (ESC para salir)')

    resultado = None
    while True:
        ret, frame = cam.read()
        if not ret:
            print('No se pudo leer frame de la cámara.')
            break

        codigos = pyzbar.decode(frame)
        for c in codigos:
            try:
                data = c.data.decode('utf-8')
            except Exception:
                data = c.data
            print('\nQR detectado:')
            print(data)
            resultado = data
            break

        cv2.imshow('Escaneo QR - presiona ESC para salir', frame)
        if cv2.waitKey(1) == 27:  # ESC
            break
        if resultado is not None:
            break
        if time.time() - inicio > timeout_seconds:
            print(f'Tiempo de espera ({timeout_seconds}s) agotado sin detectar QR.')
            break

    cam.release()
    cv2.destroyAllWindows()
    return resultado

# ----------------- Verificación del texto del QR -----------------

def verificar_qr_text(qr_text: str, secret_key: bytes):
    """
    Si qr_text tiene formato firmado (payload_b64.sig_b64) verifica HMAC.
    Si es JSON puro, lo parsea y lo devuelve.
    Devuelve: (ok: bool, data: dict or None, reason:str)
    """
    if qr_text is None:
        return False, None, 'Sin dato'

    # Intentar formato firmado
    if '.' in qr_text:
        try:
            payload_b64, sig_b64 = qr_text.split('.')
            payload_json = b64url_decode(payload_b64)
            sig = b64url_decode(sig_b64)
            expected = hmac.new(secret_key, payload_json, hashlib.sha256).digest()
            if hmac.compare_digest(expected, sig):
                data = json.loads(payload_json.decode('utf-8'))
                return True, data, 'firma_valida'
            else:
                return False, None, 'firma_invalida'
        except Exception as e:
            return False, None, f'error_verificacion:{e}'

    # Intentar JSON directo
    try:
        data = json.loads(qr_text)
        return True, data, 'json_simple'
    except Exception as e:
        return False, None, f'formato_desconocido:{e}'

# ----------------- Datos simulados -----------------

def generar_datos_simulados():
    temperatura = round(random.uniform(2.0, 30.0), 2)
    humedad = round(random.uniform(20.0, 95.0), 2)
    # Coordenadas ejemplo (rango en México) - modifica si deseas otro rango
    lat = round(random.uniform(19.0, 20.5), 6)
    lon = round(random.uniform(-101.5, -99.5), 6)
    return temperatura, humedad, lat, lon

# ----------------- Blockchain simple (archivo JSON) -----------------

def calcular_hash(bloque: dict) -> str:
    copia = dict(bloque)
    copia.pop('hash', None)
    texto = json.dumps(copia, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(texto).hexdigest()

def inicializar_chain_si_no_existe():
    if not os.path.exists(CHAIN_FILE):
        genesis = {
            'index': 0,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data': 'GENESIS',
            'prev_hash': '0'*64,
            'hash': ''
        }
        genesis['hash'] = calcular_hash(genesis)
        with open(CHAIN_FILE, 'w', encoding='utf-8') as f:
            json.dump([genesis], f, indent=4, ensure_ascii=False)
        print('Blockchain inicializada con bloque genesis.')

def agregar_bloque(data_str: str) -> dict:
    with open(CHAIN_FILE, 'r', encoding='utf-8') as f:
        chain = json.load(f)
    ultimo = chain[-1]
    nuevo = {
        'index': ultimo['index'] + 1,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data': data_str,
        'prev_hash': ultimo['hash'],
        'hash': ''
    }
    nuevo['hash'] = calcular_hash(nuevo)
    chain.append(nuevo)
    with open(CHAIN_FILE, 'w', encoding='utf-8') as f:
        json.dump(chain, f, indent=4, ensure_ascii=False)
    return nuevo

# ----------------- Flujo principal -----------------

def main(argv=None):
    parser = argparse.ArgumentParser(description='QR -> datos simulados -> blockchain local (con QR siguiente firmado)')
    parser.add_argument('--generate-qrs', action='store_true', help='Generar qr_simple.png y qr_firmado.png')
    parser.add_argument('--timeout', type=int, default=60, help='Tiempo de espera para escanear el QR (s)')
    parser.add_argument('--secret', type=str, default=None, help='Clave HMAC en texto (reemplaza la default)')
    parser.add_argument('--camera', type=int, default=0, help='Indice de la camara (por defecto 0)')
    args = parser.parse_args(argv)

    secret_key = DEFAULT_SECRET if args.secret is None else args.secret.encode('utf-8')

    if args.generate_qrs:
        generar_qr_ejemplos(secret_key)
        return

    # Ejecutar flujo de lectura
    inicializar_chain_si_no_existe()
    while True:
        print('\n--- Esperando QR (Ctrl+C para salir) ---')
        qr_text = leer_qr_camera(timeout_seconds=args.timeout, camera_index=args.camera)
        if qr_text is None:
            print('No se leyó ningún QR. Intentar de nuevo...')
            continue

        ok, data, reason = verificar_qr_text(qr_text, secret_key)
        if not ok:
            print('QR no verificado:', reason)
            print('No se registrará en la blockchain. Intenta con otro QR.')
            continue

        print('QR verificado. Motivo:', reason)

        # Construir registro
        registro = {
            'qr_payload': data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        temp, hum, lat, lon = generar_datos_simulados()
        registro.update({
            'temperatura_C': temp,
            'humedad_%': hum,
            'lat': lat,
            'lon': lon
        })

        data_str = json.dumps(registro, sort_keys=True, ensure_ascii=False)
        bloque = agregar_bloque(data_str)

        print('\n--- Datos recopilados (simulados) ---')
        print(json.dumps(registro, indent=4, ensure_ascii=False))
        print('\nBloque agregado a la blockchain simulada:')
        print(json.dumps(bloque, indent=4, ensure_ascii=False))
        print(f'Archivo de cadena: {os.path.abspath(CHAIN_FILE)}')

        # Generar siguiente QR firmado que contiene el hash del bloque recién creado
        nuevo_hash = bloque.get('hash')
        nuevo_index = bloque.get('index')
        qr_path, qr_text_next = generar_qr_next_from_hash(nuevo_hash, secret_key, nuevo_index)
        print(f"\n➡️ Siguiente QR generado: {qr_path}")
        print("Texto dentro del siguiente QR (para pruebas):")
        print(qr_text_next)

        print('\nEscanea ahora el siguiente QR para continuar la cadena.')
        # loop continuará esperando el siguiente QR y el sistema será reiterativo


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nSaliendo...')
