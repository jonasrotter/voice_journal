"""Test script to create audio and journal entry."""
import requests
import struct
import wave
import io
import math

def main():
    # 1. Login to get token
    print('=== Step 1: Login ===')
    login_data = {'email': 'testuser@voicejournal.com', 'password': 'SecurePass123!'}
    response = requests.post('http://localhost:8000/api/v1/auth/login', json=login_data)
    if response.status_code != 200:
        print(f'Login failed: {response.text}')
        return
    token = response.json()['access_token']
    print(f'Login successful, got token')

    # 2. Create a test WAV audio file
    print('')
    print('=== Step 2: Create Test Audio ===')
    sample_rate = 44100
    duration = 2
    frequency = 440

    samples = []
    for i in range(int(sample_rate * duration)):
        sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(struct.pack('<h', sample))

    audio_data = b''.join(samples)

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)

    wav_buffer.seek(0)
    print(f'Created test audio: {len(wav_buffer.getvalue())} bytes, {duration}s duration')

    # 3. Upload audio to create entry
    print('')
    print('=== Step 3: Upload Audio & Create Entry ===')
    headers = {'Authorization': f'Bearer {token}'}
    files = {'audio': ('test_recording.wav', wav_buffer.getvalue(), 'audio/wav')}
    response = requests.post('http://localhost:8000/api/v1/entries', headers=headers, files=files)

    if response.status_code != 201:
        print(f'Upload failed: {response.status_code} - {response.text}')
        return

    entry = response.json()
    print(f'Entry created!')
    print(f'  ID: {entry["id"]}')
    print(f'  Status: {entry["status"]}')
    print(f'  Audio URL: {entry["audio_url"]}')
    print(f'  Created: {entry["created_at"]}')

    if 'blob.core.windows.net' in entry['audio_url']:
        print('')
        print('SUCCESS: Audio stored in Azure Blob Storage!')
    else:
        print('')
        print('WARNING: Audio stored locally, not in Azure Blob Storage')

if __name__ == '__main__':
    main()
