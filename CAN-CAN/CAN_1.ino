#include <SPI.h>
#include <mcp2515.h>

struct can_frame canMsg;
MCP2515 mcp2515(5);  // CS en GPIO 5 (ajusta si usas otro pin)

void setup() {
  Serial.begin(115200);
  SPI.begin(18, 19, 21, 5); // SCK=18, MISO=19, MOSI=21, CS=5
  mcp2515.reset();

  // Configuración 500 kbps, cristal 8 MHz
  mcp2515.setBitrate(CAN_500KBPS, MCP_8MHZ);
  mcp2515.setNormalMode();

  Serial.println("🚀 Transmisor listo (manda PING)");
}

void loop() {
  // Construir mensaje
  canMsg.can_id  = 0x100;
  canMsg.can_dlc = 4;
  canMsg.data[0] = 'P';
  canMsg.data[1] = 'I';
  canMsg.data[2] = 'N';
  canMsg.data[3] = 'G';

  mcp2515.sendMessage(&canMsg);
  Serial.println("👉 Enviado: PING");

  delay(1000);

  // Revisar si hay respuesta
  if (mcp2515.readMessage(&canMsg) == MCP2515::ERROR_OK) {
    Serial.print("📩 Recibido: ");
    for (int i = 0; i < canMsg.can_dlc; i++) {
      Serial.write(canMsg.data[i]);
    }
    Serial.println();
  }
}
