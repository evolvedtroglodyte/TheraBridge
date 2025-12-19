# Audio Transcription Pipeline - Test Setup Guide

This guide explains how to set up and run tests for the audio transcription pipeline.

## Prerequisites

### 1. Sample Audio Files

Tests require sample audio files to validate the transcription and diarization pipeline. Place audio files in the `tests/samples/` directory.

**Recommended sample files:**

```
tests/samples/
├── compressed-cbt-session.m4a                              # Compressed therapy session
├── LIVE Cognitive Behavioral Therapy Session (1).mp3      # CBT session
└── Person-Centred Therapy Session - Full Example.mp3      # Person-centered session
```

**Where to get sample files:**

1. **YouTube Therapy Sessions** (for development/testing):
   - Search for "therapy session example" or "counseling demonstration"
   - Use `yt-dlp` to download audio:
     ```bash
     yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=..."
     ```
   - Move downloaded file to `tests/samples/`

2. **Generate synthetic audio** (for unit tests):
   ```python
   from pydub.generators import Sine
   tone = Sine(440).to_audio_segment(duration=5000)
   tone.export("tests/samples/test_audio.mp3", format="mp3")
   ```

3. **Use your own recordings** (with proper consent):
   - Ensure you have proper consent and ethical approval
   - Anonymize any personal information
   - Follow HIPAA/privacy guidelines if applicable

**Note:** The repository `.gitignore` excludes `tests/samples/*.mp3` and `tests/samples/*.m4a` to avoid committing large audio files.

### 2. API Keys

Tests require API keys for transcription and diarization services.

**Required environment variables:**

Create a `.env` file in the `audio-transcription-pipeline/` directory:

```bash
# OpenAI API key for Whisper transcription
OPENAI_API_KEY=sk-...

# HuggingFace token for pyannote speaker diarization
# Get token from: https://huggingface.co/settings/tokens
HF_TOKEN=hf_...
```

**Getting API keys:**

1. **OpenAI API Key**:
   - Sign up at https://platform.openai.com
   - Navigate to API Keys section
   - Create new secret key
   - Add to `.env` as `OPENAI_API_KEY`

2. **HuggingFace Token**:
   - Sign up at https://huggingface.co
   - Go to Settings → Access Tokens
   - Create new token with "read" access
   - Accept pyannote model agreements:
     - https://huggingface.co/pyannote/speaker-diarization-3.1
     - https://huggingface.co/pyannote/segmentation-3.0
   - Add to `.env` as `HF_TOKEN`

### 3. Python Dependencies

Install test dependencies:

```bash
cd audio-transcription-pipeline
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

## Running Tests

### Run all tests

```bash
pytest tests/
```

### Run specific test files

```bash
pytest tests/test_full_pipeline.py
pytest tests/test_diarization.py
```

### Run tests with verbose output

```bash
pytest -v tests/
```

### Skip tests requiring sample files

Tests automatically skip if sample files are missing:

```bash
# These will skip gracefully if no samples available
pytest tests/test_full_pipeline.py
pytest tests/test_performance_logging.py
```

### Run only tests that don't require samples

```bash
pytest -m "not requires_sample_audio" tests/
```

### Run integration tests (requires everything)

```bash
pytest -m integration tests/
```

## Test Markers

Tests use markers to indicate requirements:

- `@pytest.mark.requires_sample_audio` - Requires sample audio files
- `@pytest.mark.requires_openai` - Requires OPENAI_API_KEY
- `@pytest.mark.requires_hf` - Requires HF_TOKEN
- `@pytest.mark.integration` - Requires all of the above

## Fixtures Available

The `conftest.py` provides these fixtures:

### Sample Audio Fixtures

```python
def test_with_cbt_sample(sample_cbt_session):
    """Test skips if CBT sample missing"""
    assert sample_cbt_session.exists()

def test_with_any_sample(any_sample_audio):
    """Test uses first available sample"""
    assert any_sample_audio.exists()
```

### Environment Fixtures

```python
def test_transcription(openai_api_key):
    """Test skips if OPENAI_API_KEY not set"""
    client = OpenAI(api_key=openai_api_key)

def test_diarization(hf_token):
    """Test skips if HF_TOKEN not set"""
    pipeline = Pipeline.from_pretrained(..., token=hf_token)
```

### Directory Fixtures

```python
def test_output(outputs_dir, processed_dir):
    """Temporary directories for test artifacts"""
    output_file = outputs_dir / "result.json"
    processed_audio = processed_dir / "audio.wav"
```

## Troubleshooting

### Tests skip with "No sample audio files found"

**Solution:** Add sample audio files to `tests/samples/` directory. See "Where to get sample files" above.

### Tests skip with "OPENAI_API_KEY not set"

**Solution:** Create `.env` file in `audio-transcription-pipeline/` directory with your OpenAI API key.

### Tests skip with "HF_TOKEN not set"

**Solution:** Add HuggingFace token to `.env` file. Ensure you've accepted pyannote model agreements.

### Test fails with "Audio file not found"

**Cause:** Test uses hardcoded path instead of fixture.

**Solution:** Update test to use fixtures:

```python
# ❌ Bad: Hardcoded path
def test_pipeline():
    audio_file = Path("tests/samples/onemintestvid.mp3")
    if not audio_file.exists():
        print("ERROR: Audio file not found")
        return

# ✅ Good: Use fixture
def test_pipeline(any_sample_audio):
    # Test automatically skips if no samples
    result = process_audio(any_sample_audio)
```

### pyannote fails with "Agreement not accepted"

**Solution:**
1. Visit https://huggingface.co/pyannote/speaker-diarization-3.1
2. Click "Agree and access repository"
3. Do the same for https://huggingface.co/pyannote/segmentation-3.0
4. Wait a few minutes for permissions to propagate

## Best Practices

### Writing new tests

1. **Use fixtures for sample files:**
   ```python
   @pytest.mark.requires_sample_audio
   def test_my_feature(any_sample_audio, outputs_dir):
       result = my_function(any_sample_audio)
       output_file = outputs_dir / "result.json"
       output_file.write_text(json.dumps(result))
   ```

2. **Add appropriate markers:**
   ```python
   @pytest.mark.requires_openai
   @pytest.mark.requires_hf
   def test_full_pipeline(any_sample_audio, openai_api_key, hf_token):
       # Test runs only if all requirements met
       pass
   ```

3. **Use temporary directories:**
   ```python
   def test_output_files(outputs_dir):
       # Don't write to tests/outputs/ directly
       output = outputs_dir / "test.json"
       # tmp_path cleans up automatically
   ```

4. **Document skip conditions:**
   ```python
   def test_specific_file():
       """
       Tests audio preprocessing.

       REQUIRES: tests/samples/specific-file.mp3
       SKIPS: If sample file not available
       """
       path = Path("tests/samples/specific-file.mp3")
       if not path.exists():
           pytest.skip("specific-file.mp3 not available")
   ```

## Sample File Size Guidelines

- **Unit tests:** Use small files (<1MB) or synthetic audio
- **Integration tests:** Use real therapy sessions (20-50MB typical)
- **Performance tests:** Use variety of file sizes

**Compress large files:**

```bash
ffmpeg -i input.mp3 -b:a 64k -ar 16000 compressed.m4a
```

## CI/CD Considerations

For CI/CD pipelines:

1. **Store sample files separately:** Use artifact storage (S3, GCS) instead of git
2. **Use mock data:** For unit tests, mock transcription/diarization responses
3. **Conditional integration tests:** Run full pipeline tests only on main branch
4. **API key management:** Use encrypted secrets, not `.env` files

## Support

If you encounter issues:

1. Check this README for troubleshooting steps
2. Verify all prerequisites are installed
3. Ensure API keys have proper permissions
4. Check test output for specific error messages
