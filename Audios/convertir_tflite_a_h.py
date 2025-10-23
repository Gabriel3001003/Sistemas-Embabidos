# convertir_tflite_a_h.py
tflite_model = 'yes_no_model.tflite'
h_file = 'yes_no_model_data.h'

with open(tflite_model, 'rb') as f:
    data = f.read()

with open(h_file, 'w') as f:
    f.write('unsigned char yes_no_model_tflite[] = {\n')
    for i, b in enumerate(data):
        f.write(f'{b}, ')
        if (i + 1) % 12 == 0:
            f.write('\n')
    f.write('\n};\n')
    f.write(f'unsigned int yes_no_model_tflite_len = {len(data)};\n')
