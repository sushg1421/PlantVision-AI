"""
PlantVision AI — Disease Model Training Script
===============================================
Run this ONCE locally or on Google Colab to train the disease detection model.
Output: models/disease_model.h5  (copy this to your back-end/models/ folder)

Requirements:
    pip install tensorflow kaggle pillow numpy scikit-learn

Kaggle setup (one-time):
    1. Go to https://www.kaggle.com/account → Create New Token → downloads kaggle.json
    2. Place kaggle.json in:
         Windows: C:/Users/<you>/.kaggle/kaggle.json
         Linux/Mac: ~/.kaggle/kaggle.json
    3. OR set environment variables:
         KAGGLE_USERNAME=your_username
         KAGGLE_KEY=your_api_key
"""

import os
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import json

# ─── Config ────────────────────────────────────────────────────────────────────
IMG_SIZE      = (224, 224)
BATCH_SIZE    = 32
EPOCHS_FROZEN = 10   # train with base frozen
EPOCHS_FINE   = 5    # fine-tune last 20 layers
DATASET_DIR   = "dataset/plantvillage"   # where Kaggle extracts to
OUTPUT_DIR    = "../models"              # relative to ml/ folder → back-end/models/
OUTPUT_MODEL  = os.path.join(OUTPUT_DIR, "disease_model.h5")
CLASSES_FILE  = os.path.join(OUTPUT_DIR, "disease_classes.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("dataset", exist_ok=True)

# ─── Step 1: Download PlantVillage from Kaggle ────────────────────────────────
def download_dataset():
    if os.path.exists(DATASET_DIR):
        print("✓ Dataset already downloaded, skipping.")
        return

    print("Downloading PlantVillage dataset from Kaggle...")
    try:
        import kaggle
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            "abdallahalidev/plantvillage-dataset",
            path="dataset",
            unzip=True
        )
        # Kaggle extracts to dataset/plantvillage/segmented or color
        # We'll use the 'color' subfolder
        raw_path = "dataset/plantvillage dataset/color"
        if os.path.exists(raw_path):
            os.rename(raw_path, DATASET_DIR)
        print("✓ Dataset downloaded successfully.")
    except Exception as e:
        print(f"\n✗ Kaggle download failed: {e}")
        print("\nManual alternative:")
        print("  1. Download from: https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset")
        print("  2. Extract the 'color' folder to: ml/dataset/plantvillage/")
        print("  3. Re-run this script.")
        sys.exit(1)

# ─── Step 2: Build data generators ───────────────────────────────────────────
def build_generators():
    print("\nLoading dataset...")

    # Augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.15,
        brightness_range=[0.8, 1.2]
    )

    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2
    )

    train_gen = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        seed=42
    )

    val_gen = val_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        seed=42
    )

    num_classes = len(train_gen.class_indices)
    print(f"✓ Found {num_classes} classes, {train_gen.samples} training images, {val_gen.samples} validation images.")

    # Save class names for use in disease_router.py
    class_names = {v: k for k, v in train_gen.class_indices.items()}
    class_list = [class_names[i] for i in range(num_classes)]
    with open(CLASSES_FILE, "w") as f:
        json.dump(class_list, f, indent=2)
    print(f"✓ Class names saved to {CLASSES_FILE}")

    return train_gen, val_gen, num_classes

# ─── Step 3: Build model ──────────────────────────────────────────────────────
def build_model(num_classes):
    print("\nBuilding MobileNetV2 model...")

    base_model = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False  # freeze for initial training

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.4),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation="softmax")
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    print(f"✓ Model built. Total params: {model.count_params():,}")
    return model, base_model

# ─── Step 4: Train ───────────────────────────────────────────────────────────
def train(model, base_model, train_gen, val_gen):

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=3, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6
        ),
        tf.keras.callbacks.ModelCheckpoint(
            OUTPUT_MODEL, monitor="val_accuracy", save_best_only=True
        )
    ]

    # Phase 1: train with frozen base
    print(f"\n── Phase 1: Training top layers ({EPOCHS_FROZEN} epochs) ──")
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FROZEN,
        callbacks=callbacks
    )

    # Phase 2: fine-tune last 20 layers of base
    print(f"\n── Phase 2: Fine-tuning last 20 layers ({EPOCHS_FINE} epochs) ──")
    base_model.trainable = True
    for layer in base_model.layers[:-20]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),  # lower LR for fine-tune
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FINE,
        callbacks=callbacks
    )

    return model

# ─── Step 5: Evaluate & save ─────────────────────────────────────────────────
def evaluate_and_save(model, val_gen):
    print("\nEvaluating final model...")
    loss, acc = model.evaluate(val_gen)
    print(f"✓ Validation accuracy: {acc * 100:.2f}%")
    print(f"✓ Model saved to: {OUTPUT_MODEL}")
    print("\n── Next steps ──────────────────────────────────────────────────")
    print(f"  1. Copy '{OUTPUT_MODEL}' to 'back-end/models/disease_model.h5'")
    print(f"  2. Copy '{CLASSES_FILE}' to 'back-end/models/disease_classes.json'")
    print(f"  3. Restart your FastAPI server")
    print(f"  4. Call POST /disease/detect with a leaf image to test")

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  PlantVision AI — Disease Model Trainer")
    print("=" * 60)

    # Check GPU
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        print(f"✓ GPU detected: {gpus[0].name}")
        tf.config.experimental.set_memory_growth(gpus[0], True)
    else:
        print("⚠ No GPU detected. Training on CPU will be slow.")
        print("  Recommended: run this on Google Colab (free GPU).")

    download_dataset()
    train_gen, val_gen, num_classes = build_generators()
    model, base_model = build_model(num_classes)
    model = train(model, base_model, train_gen, val_gen)
    evaluate_and_save(model, val_gen)