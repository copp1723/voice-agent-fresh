#!/usr/bin/env python3
"""Quick test for Chatterbox module loading"""

try:
    print("Testing Chatterbox import...")
    from chatterbox.tts import ChatterboxTTS
    print("✓ Chatterbox module imported successfully!")
    
    print("\nChecking available methods:")
    print(f"  - from_pretrained: {hasattr(ChatterboxTTS, 'from_pretrained')}")
    print(f"  - generate: {hasattr(ChatterboxTTS, 'generate')}")
    
    print("\nAttempting to load model...")
    model = ChatterboxTTS.from_pretrained(device="cpu")
    print("✓ Model loaded successfully!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nTrying alternative import...")
    try:
        import chatterbox
        print(f"  chatterbox module found at: {chatterbox.__file__}")
    except:
        print("  chatterbox module not found")
        
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    
print("\nChecking torch availability...")
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")