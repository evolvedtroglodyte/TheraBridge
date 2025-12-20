#!/bin/bash
#
# Fully Automated Vast.ai GPU Pipeline
# Upload → Process → Download → Display → Done
#
# Usage: ./run_on_vast.sh <instance_id> <audio_file>
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INSTANCE_ID="$1"
AUDIO_FILE="$2"

if [ -z "$INSTANCE_ID" ] || [ -z "$AUDIO_FILE" ]; then
    echo -e "${RED}Usage: $0 <instance_id> <audio_file>${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 29040483 \"tests/samples/Carl Rogers...mp3\""
    echo ""
    echo "Get instance ID from: vastai show instances"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo -e "${RED}Error: Audio file not found: $AUDIO_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Automated Vast.ai GPU Pipeline${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Get SSH connection details
echo -e "${YELLOW}Step 1/6: Getting SSH connection info...${NC}"
SSH_INFO=$(vastai show instances | grep "^$INSTANCE_ID")
if [ -z "$SSH_INFO" ]; then
    echo -e "${RED}Error: Instance $INSTANCE_ID not found${NC}"
    echo "Run: vastai show instances"
    exit 1
fi

SSH_HOST=$(echo "$SSH_INFO" | awk '{print $10}')
SSH_PORT=$(echo "$SSH_INFO" | awk '{print $11}')

echo -e "${GREEN}✓ Instance: $INSTANCE_ID${NC}"
echo -e "${GREEN}✓ SSH: root@$SSH_HOST:$SSH_PORT${NC}\n"

# Create processing script to run on remote instance
cat > /tmp/process_audio_vast.sh << 'REMOTE_SCRIPT'
#!/bin/bash
set -e

echo "==> Installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git ffmpeg > /dev/null 2>&1

echo "==> Setting up Python environment..."
pip install -q --upgrade pip
pip install -q torch torchaudio faster-whisper pyannote.audio pydub

echo "==> Cloning repository..."
if [ -d "TheraBridge" ]; then
    rm -rf TheraBridge
fi
git clone -q https://github.com/evolvedtroglodyte/TheraBridge.git
cd TheraBridge/audio-transcription-pipeline

# Set HuggingFace token from environment (user must set before running)
# export HF_TOKEN=your_token_here  # Set this in your environment or .env file

echo "==> Processing audio with GPU pipeline..."
python3 << 'PYTHON_SCRIPT'
import os
import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

print("\n" + "="*60)
print("GPU AUDIO PROCESSING")
print("="*60 + "\n")

# Import and run pipeline
from pipeline_gpu import GPUTranscriptionPipeline

start_time = time.time()

with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    results = pipeline.process(
        audio_path="/root/audio_input.mp3",
        num_speakers=2,
        language="en",
        enable_diarization=True
    )

total_time = time.time() - start_time

# Add timing
results['total_processing_time'] = total_time

# Save results
with open('/root/results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

# Print summary
perf = results.get('performance', {})
transcript = results.get('aligned_transcript', []) or results.get('transcript', [])

print("\n" + "="*60)
print("PROCESSING COMPLETE")
print("="*60)
print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
print(f"Segments: {len(transcript)}")

# Count speakers
speakers = {}
for seg in transcript:
    speaker = seg.get('speaker', 'Unknown')
    speakers[speaker] = speakers.get(speaker, 0) + 1

for speaker, count in sorted(speakers.items()):
    print(f"{speaker}: {count} segments")

print("="*60 + "\n")
PYTHON_SCRIPT

echo "==> Results saved to /root/results.json"
REMOTE_SCRIPT

chmod +x /tmp/process_audio_vast.sh

# Upload audio file
echo -e "${YELLOW}Step 2/6: Uploading audio file ($(du -h "$AUDIO_FILE" | cut -f1))...${NC}"
scp -q -P "$SSH_PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    "$AUDIO_FILE" "root@$SSH_HOST:/root/audio_input.mp3"
echo -e "${GREEN}✓ Audio uploaded${NC}\n"

# Upload processing script
echo -e "${YELLOW}Step 3/6: Uploading processing script...${NC}"
scp -q -P "$SSH_PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    /tmp/process_audio_vast.sh "root@$SSH_HOST:/root/process.sh"
echo -e "${GREEN}✓ Script uploaded${NC}\n"

# Run processing on remote instance
echo -e "${YELLOW}Step 4/6: Running GPU processing (this will take 5-10 minutes)...${NC}\n"
ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    "root@$SSH_HOST" "bash /root/process.sh"

# Download results
echo -e "\n${YELLOW}Step 5/6: Downloading results...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="outputs/vast_results/results_${TIMESTAMP}.json"
mkdir -p outputs/vast_results

scp -q -P "$SSH_PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    "root@$SSH_HOST:/root/results.json" "$RESULTS_FILE"
echo -e "${GREEN}✓ Results downloaded to: $RESULTS_FILE${NC}\n"

# Display results
echo -e "${YELLOW}Step 6/6: Displaying results...${NC}\n"

python3 << DISPLAY_SCRIPT
import json
from pathlib import Path

with open("$RESULTS_FILE") as f:
    data = json.load(f)

# Performance metrics
perf = data.get('performance', {})
total_time = data.get('total_processing_time', 0)

print("="*60)
print("PERFORMANCE METRICS")
print("="*60)

# Get audio duration
audio_duration = 0
transcript = data.get('aligned_transcript', []) or data.get('transcript', [])
if transcript:
    audio_duration = max([seg.get('end', 0) for seg in transcript] or [0])

if audio_duration > 0:
    speedup = audio_duration / max(total_time, 1)
    print(f"Audio Duration:      {audio_duration:.1f}s ({audio_duration/60:.1f} min)")
    print(f"Processing Time:     {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"Speedup:             {speedup:.2f}x real-time")
else:
    print(f"Processing Time:     {total_time:.1f}s ({total_time/60:.1f} min)")

print()

# Stage breakdown
stages = perf.get('stages', {})
if stages:
    print("STAGE BREAKDOWN")
    print("-" * 60)
    for stage, time_val in stages.items():
        print(f"{stage:25s} {time_val:8.2f}s")
    print()

# GPU metrics
gpu = perf.get('gpu_metrics', {})
if gpu:
    print("GPU METRICS")
    print("-" * 60)
    print(f"Provider:            {gpu.get('provider', 'unknown')}")
    print(f"Device:              {gpu.get('device', 'unknown')}")
    print(f"Peak VRAM:           {gpu.get('peak_vram_gb', 0):.1f} GB")
    print(f"Avg Utilization:     {gpu.get('avg_utilization_pct', 0):.1f}%")
    print()

# Transcript statistics
print("TRANSCRIPT STATISTICS")
print("-" * 60)
print(f"Total segments:      {len(transcript)}")

speakers = {}
for seg in transcript:
    speaker = seg.get('speaker', 'Unknown')
    speakers[speaker] = speakers.get(speaker, 0) + 1

for speaker, count in sorted(speakers.items()):
    print(f"{speaker:20s} {count} segments")
print()

# Show first 30 segments of transcript
print("="*60)
print("DIARIZED TRANSCRIPT (First 30 segments)")
print("="*60 + "\n")

current_speaker = None
for i, seg in enumerate(transcript[:30]):
    speaker = seg.get('speaker', 'Unknown')
    text = seg.get('text', '').strip()
    start = seg.get('start', 0)

    if speaker != current_speaker:
        print(f"\n[{speaker}] ({start:.1f}s)")
        current_speaker = speaker

    print(f"  {text}")

if len(transcript) > 30:
    print(f"\n... ({len(transcript) - 30} more segments)")

print("\n" + "="*60)
print(f"Full results saved to: $RESULTS_FILE")
print("="*60 + "\n")
DISPLAY_SCRIPT

# Cost estimate
COST_PER_HOUR=$(vastai show instances | grep "^$INSTANCE_ID" | awk '{print $12}')
PROCESSING_HOURS=$(python3 -c "import json; data=json.load(open('$RESULTS_FILE')); print(data.get('total_processing_time', 0) / 3600)")
ESTIMATED_COST=$(python3 -c "print(f'{float('$COST_PER_HOUR') * float('$PROCESSING_HOURS'):.4f}')")

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}COST ESTIMATE${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Processing Time:  $(python3 -c "import json; data=json.load(open('$RESULTS_FILE')); print(f\"{data.get('total_processing_time', 0)/60:.1f} min\")")"
echo -e "Instance Cost:    \$${COST_PER_HOUR}/hr"
echo -e "Estimated Cost:   \$${ESTIMATED_COST}"
echo ""

echo -e "${GREEN}✓ Pipeline complete!${NC}\n"
echo -e "${YELLOW}IMPORTANT: Destroy instance when done:${NC}"
echo -e "  vastai destroy instance $INSTANCE_ID"
echo ""
