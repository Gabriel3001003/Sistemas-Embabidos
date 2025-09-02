#include <SPI.h>
#include <Adafruit_Sensor.h>
#include "Adafruit_BME680.h"

// Define pines SOLO del lado izquierdo del ESP32-S3
#define CS_PIN   21
#define MOSI_PIN 19
#define MISO_PIN 20
#define SCK_PIN  18

// Crear instancia del BME680 en modo SPI por software
Adafruit_BME680 bme(CS_PIN, MOSI_PIN, MISO_PIN, SCK_PIN);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println(F("Iniciando BME680 en SPI con ESP32-S3"));

  if (!bme.begin()) {
    Serial.println("¡No se encontró un BME680 válido en SPI! Verifica el cableado.");
    while (1);
  }

  // Configurar oversampling y filtro
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320, 150); // 320 °C durante 150 ms
}

void loop() {
  if (!bme.performReading()) {
    Serial.println("Error al leer :(");
    return;
  }

  Serial.print("Temperatura = ");
  Serial.print(bme.temperature);
  Serial.println(" °C");

  Serial.print("Presión = ");
  Serial.print(bme.pressure / 100.0);
  Serial.println(" hPa");

  Serial.print("Humedad = ");
  Serial.print(bme.humidity);
  Serial.println(" %");

  Serial.print("Gas = ");
  Serial.print(bme.gas_resistance / 1000.0);
  Serial.println(" KOhms");

  Serial.println();
  delay(2000);
}
