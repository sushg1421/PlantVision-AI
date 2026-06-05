# accuracy_test.py
import tensorflow as tf
import numpy as np
import json
from PIL import Image

model = tf.keras.models.load_model(r"C:\Users\susha\plant-app\back-end\models\disease_model.h5")

with open(r"C:\Users\susha\plant-app\back-end\models\disease_classes.json") as f:
    CLASS_NAMES = json.load(f)

# Test with a few images from your dataset directly
test_dir = r"C:\Users\susha\plant-app\back-end\ml\dataset\plantvillage"
import os

correct = 0
total = 0

for class_name in CLASS_NAMES[:5]:  # test first 5 classes
    class_dir = os.path.join(test_dir, class_name)
    images = os.listdir(class_dir)[:3]  # 3 images per class
    for img_name in images:
        img_path = os.path.join(class_dir, img_name)
        img = Image.open(img_path).convert("RGB").resize((224, 224))
        arr = np.expand_dims(np.array(img) / 255.0, 0)
        preds = model.predict(arr, verbose=0)[0]
        predicted = CLASS_NAMES[np.argmax(preds)]
        confidence = round(float(np.max(preds)) * 100, 1)
        status = "✓" if predicted == class_name else "✗"
        print(f"{status} Expected: {class_name} | Got: {predicted} ({confidence}%)")
        if predicted == class_name:
            correct += 1
        total += 1

print(f"\nAccuracy on sample: {correct}/{total} = {round(correct/total*100, 1)}%")