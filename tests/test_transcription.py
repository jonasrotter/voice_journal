"""Test script for audio transcription with Azure OpenAI Whisper.

This script:
1. Logs in with test user
2. Creates a test audio file (WAV with speech-like pattern)
3. Uploads audio and creates journal entry
4. Waits for background processing to complete
5. Verifies the entry is transcribed and updated in DB
"""
import requests
import time
import struct
import math

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": "transcripttest@voicejournal.com",
    "password": "testpassword123"
}


def create_test_audio_with_tone(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Create a WAV audio file with varying tones (more speech-like).
    
    Using 16kHz sample rate which is optimal for Whisper transcription.
    """
    num_samples = int(duration_seconds * sample_rate)
    
    # Create varying frequency tones (simulates speech patterns)
    audio_samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Mix multiple frequencies for richer audio
        frequency = 200 + 100 * math.sin(2 * math.pi * 0.5 * t)  # Varying base frequency
        sample = int(16000 * math.sin(2 * math.pi * frequency * t))
        audio_samples.append(max(-32768, min(32767, sample)))
    
    # Build WAV file
    wav_data = bytearray()
    
    # RIFF header
    wav_data.extend(b'RIFF')
    data_size = len(audio_samples) * 2
    file_size = 36 + data_size
    wav_data.extend(struct.pack('<I', file_size))
    wav_data.extend(b'WAVE')
    
    # fmt chunk
    wav_data.extend(b'fmt ')
    wav_data.extend(struct.pack('<I', 16))  # chunk size
    wav_data.extend(struct.pack('<H', 1))   # PCM
    wav_data.extend(struct.pack('<H', 1))   # mono
    wav_data.extend(struct.pack('<I', sample_rate))  # sample rate
    wav_data.extend(struct.pack('<I', sample_rate * 2))  # byte rate
    wav_data.extend(struct.pack('<H', 2))   # block align
    wav_data.extend(struct.pack('<H', 16))  # bits per sample
    
    # data chunk
    wav_data.extend(b'data')
    wav_data.extend(struct.pack('<I', data_size))
    for sample in audio_samples:
        wav_data.extend(struct.pack('<h', sample))
    
    return bytes(wav_data)


def login() -> str:
    """Login and return JWT token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    return response.json()["access_token"]


def upload_audio(token: str, audio_data: bytes) -> dict:
    """Upload audio and create entry."""
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        "audio": ("test_audio.wav", audio_data, "audio/wav")
    }
    
    response = requests.post(
        f"{BASE_URL}/entries",
        headers=headers,
        files=files
    )
    
    if response.status_code != 201:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")
    
    return response.json()


def get_entry(token: str, entry_id: str) -> dict:
    """Get entry details."""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/entries/{entry_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Get entry failed: {response.status_code} - {response.text}")
    
    return response.json()


def wait_for_processing(token: str, entry_id: str, timeout: int = 60) -> dict:
    """Wait for entry to be processed."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        entry = get_entry(token, entry_id)
        status = entry.get("status")
        
        print(f"  Status: {status}")
        
        if status == "processed":
            return entry
        elif status == "failed":
            raise Exception(f"Processing failed for entry {entry_id}")
        
        time.sleep(2)
    
    raise Exception(f"Timeout waiting for processing after {timeout}s")


def main():
    print("=" * 60)
    print("Voice Journal - Transcription Test")
    print("=" * 60)
    
    # Step 1: Login
    print("\n=== Step 1: Login ===")
    try:
        token = login()
        print(f"Login successful!")
    except Exception as e:
        print(f"Login failed: {e}")
        return
    
    # Step 2: Create test audio
    print("\n=== Step 2: Create Test Audio ===")
    audio_data = create_test_audio_with_tone(duration_seconds=3.0, sample_rate=16000)
    print(f"Created test audio: {len(audio_data)} bytes, 3s duration, 16kHz sample rate")
    
    # Step 3: Upload audio and create entry
    print("\n=== Step 3: Upload Audio & Create Entry ===")
    try:
        entry = upload_audio(token, audio_data)
        entry_id = entry["id"]
        print(f"Entry created:")
        print(f"  ID: {entry_id}")
        print(f"  Status: {entry['status']}")
        print(f"  Audio URL: {entry['audio_url']}")
    except Exception as e:
        print(f"Upload failed: {e}")
        return
    
    # Step 4: Wait for AI processing
    print("\n=== Step 4: Wait for AI Processing ===")
    print("Waiting for Azure OpenAI to transcribe and process...")
    try:
        processed_entry = wait_for_processing(token, entry_id, timeout=60)
        print("\nProcessing complete!")
    except Exception as e:
        print(f"Processing failed: {e}")
        # Try to get current state
        try:
            entry = get_entry(token, entry_id)
            print(f"Current entry state:")
            print(f"  Status: {entry.get('status')}")
            print(f"  Transcript: {entry.get('transcript', 'N/A')[:100] if entry.get('transcript') else 'None'}")
        except:
            pass
        return
    
    # Step 5: Display results
    print("\n=== Step 5: Transcription Results ===")
    print(f"Entry ID: {processed_entry['id']}")
    print(f"Status: {processed_entry['status']}")
    print(f"Transcript: {processed_entry.get('transcript', 'N/A')}")
    print(f"Summary: {processed_entry.get('summary', 'N/A')}")
    print(f"Emotion: {processed_entry.get('emotion', 'N/A')}")
    print(f"Audio URL: {processed_entry['audio_url']}")
    
    # Verify success
    print("\n" + "=" * 60)
    if processed_entry.get('transcript'):
        print("✅ SUCCESS: Audio transcribed and entry updated in database!")
    else:
        print("⚠️ WARNING: Entry processed but transcript is empty")
    print("=" * 60)


if __name__ == "__main__":
    main()
