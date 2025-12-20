#!/bin/bash
set -e

echo "==> Checking environment..."
if [ ! -d "TheraBridge" ]; then
    echo "==> Cloning repository..."
    git clone -q https://github.com/evolvedtroglodyte/TheraBridge.git
fi

cd TheraBridge/audio-transcription-pipeline

echo "==> Installing dependencies..."
pip install -q torch torchaudio faster-whisper pyannote.audio pydub

export HF_TOKEN=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

echo "==> Processing audio with GPU pipeline..."
python3 << 'EOF'
import os
import json
import sys
from pathlib import Path

sys.path.insert(0, 'src')

from pipeline_gpu import GPUTranscriptionPipeline

with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    results = pipeline.process(
        audio_path="/root/audio_input.mp3",
        num_speakers=2,
        language="en",
        enable_diarization=True
    )

with open('/root/results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("Processing complete!")
EOF
