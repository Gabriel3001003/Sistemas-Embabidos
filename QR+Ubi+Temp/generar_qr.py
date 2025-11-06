import json, hmac, hashlib, base64
import qrcode

# --- Clave secreta compartida ---
SECRET_KEY = b"mi_clave_secreta_32bytes"  # mantener privada

# --- Payload básico del artículo ---
payload = {
    "sku": "ABC123",
    "serial": "0001",
    "batch": "2025-11-01",
    "issuer": "FABRICA_X"
}

# --- Generar QR 1: JSON simple ---
qr_simple = json.dumps(payload, separators=(',',':'))
img_simple = qrcode.make(qr_simple)
img_simple.save("qr_simple.png")
print("✅ QR simple generado: qr_simple.png")
print(qr_simple, "\n")

# --- Generar QR 2: JSON firmado (payload + firma) ---
payload_json = json.dumps(payload, separators=(',',':'), sort_keys=True).encode('utf-8')
sig = hmac.new(SECRET_KEY, payload_json, hashlib.sha256).digest()
b64_payload = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip("=")
b64_sig = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip("=")
qr_text = f"{b64_payload}.{b64_sig}"

img_signed = qrcode.make(qr_text)
img_signed.save("qr_firmado.png")
print("✅ QR firmado generado: qr_firmado.png")
print(qr_text)
