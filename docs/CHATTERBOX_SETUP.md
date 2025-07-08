# Chatterbox TTS Installation Guide

## Prerequisites
- Python 3.11+
- CUDA-capable GPU (recommended) or CPU

## Installation Steps

1. **Install PyTorch** (if not already installed):
   ```bash
   # For CUDA 11.8
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # For CPU only
   pip install torch torchvision torchaudio
   ```

2. **Install Chatterbox dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chatterbox** (when available):
   ```bash
   # From GitHub (current method)
   git clone https://github.com/resemble-ai/chatterbox.git
   cd chatterbox
   pip install -e .
   cd ..
   
   # Or via pip (when released)
   # pip install chatterbox-tts
   ```

4. **Configure environment**:
   - Copy `.env.template` to `.env`
   - Set `USE_CHATTERBOX=true` to enable Chatterbox
   - Optionally add voice sample paths for voice cloning

5. **Test the integration**:
   ```bash
   python test_chatterbox_integration.py
   ```

## Voice Samples (Optional)

To use voice cloning:
1. Record 10-30 seconds of clear speech for each agent
2. Save as WAV files in the `voice_samples/` directory
3. Update paths in `.env` file

## Troubleshooting

- If Chatterbox fails to load, the system will fall back to OpenAI TTS
- Check logs for detailed error messages
- Ensure CUDA is properly installed for GPU acceleration
- For production, consider using CPU-optimized settings
