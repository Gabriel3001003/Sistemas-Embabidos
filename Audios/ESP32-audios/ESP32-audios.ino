#include <Arduino.h>
#include "TensorFlowLite_ESP32.h"  // Librería oficial
#include "model_data.h"            // Aquí irá tu modelo .tflite convertido a .h

// Buffers de trabajo
constexpr int tensorArenaSize = 20 * 1024;
uint8_t tensorArena[tensorArenaSize];

// Objetos principales de TFLite
tflite::MicroInterpreter* interpreter;
tflite::MicroErrorReporter errorReporter;
tflite::Model* model;

// Punteros a entrada/salida del modelo
TfLiteTensor* inputTensor;
TfLiteTensor* outputTensor;

void setup() {
  Serial.begin(115200);
  Serial.println("Inicializando TensorFlow Lite...");

  // Cargar el modelo
  model = tflite::GetModel(model_data);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("Error: versión de modelo incompatible.");
    while (1);
  }

  // Crear intérprete
  static tflite::AllOpsResolver resolver;
  static tflite::MicroInterpreter staticInterpreter(
    model, resolver, tensorArena, tensorArenaSize, &errorReporter);
  interpreter = &staticInterpreter;

  // Asignar tensores
  if (interpreter->AllocateTensors() != kTfLiteOk) {
    Serial.println("Error al asignar tensores.");
    while (1);
  }

  inputTensor = interpreter->input(0);
  outputTensor = interpreter->output(0);

  Serial.println("TensorFlow Lite inicializado correctamente.");
}

void loop() {
  // Ejemplo: simulamos una entrada de audio (dato aleatorio)
  for (int i = 0; i < inputTensor->bytes / sizeof(float); i++) {
    inputTensor->data.f[i] = random(0, 100) / 100.0f;
  }

  // Ejecutar inferencia
  if (interpreter->Invoke() != kTfLiteOk) {
    Serial.println("Error al ejecutar inferencia");
    return;
  }

  // Mostrar salida
  Serial.print("Salida del modelo: ");
  Serial.println(outputTensor->data.f[0]);

  delay(2000);
}


