#include <SPI.h>
#include <mcp2515.h>

struct can_frame canMsg;
MCP2515 mcp2515(5);  // CS en GPIO 5 (ajusta si usas otro pin)

void setup() {
  Serial.begin(115200);
  SPI.begin(18, 19, 21, 5); // SCK=18, MISO=19, MOSI=21, CS=5
  mcp2515.reset();

  // Configuración 500 kbps, cristal 8 MHz
  mcp2515.setBitrate(CAN_125KBPS, MCP_8MHZ);
  mcp2515.setNormalMode();

  Serial.println("📡 Receptor listo (esperando PING)");
}

void loop() {
  if (mcp2515.readMessage(&canMsg) == MCP2515::ERROR_OK) {
  char mensaje[9];
  for (int i = 0; i < canMsg.can_dlc; i++) {
    mensaje[i] = (char)canMsg.data[i];
  }
  mensaje[canMsg.can_dlc] = '\0';

  Serial.print("📥 Recibido: ");
  Serial.println(mensaje);

  // Si recibimos "PING", contestamos con "PONG"
  if (strcmp(mensaje, "PING") == 0) {
    struct can_frame reply;
    reply.can_id  = 0x101;
    reply.can_dlc = 4;
    reply.data[0] = 'P';
    reply.data[1] = 'O';
    reply.data[2] = 'N';
    reply.data[3] = 'G';

    mcp2515.sendMessage(&reply);
    Serial.println("🔄 Respuesta enviada: PONG");
  }
}

}
