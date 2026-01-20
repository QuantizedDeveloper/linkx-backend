#!/bin/bash
set -e

BASE="https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js/weights"

FILES=(
  ssd_mobilenetv1_model-weights_manifest.json
  ssd_mobilenetv1_model-shard1
  ssd_mobilenetv1_model-shard2

  face_landmark_68_model-weights_manifest.json
  face_landmark_68_model-shard1

  face_recognition_model-weights_manifest.json
  face_recognition_model-shard1
  face_recognition_model-shard2
)

echo "Downloading face-api.js models…"

for file in "${FILES[@]}"; do
  echo "→ $file"
  curl -fLO "$BASE/$file"
done

echo "✅ All models downloaded successfully"
