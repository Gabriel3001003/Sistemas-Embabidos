import tensorflow as tf

# Cargar modelo entrenado
model = tf.keras.models.load_model("yes_no_model.h5")

# Convertir a TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Guardar archivo .tflite
with open("yes_no_model.tflite", "wb") as f:
    f.write(tflite_model)

print("✅ Modelo convertido a yes_no_model.tflite")
