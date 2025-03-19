import os
import wave
import tempfile
import subprocess
import numpy as np
from gtts import gTTS
from livekit import rtc

SAMPLE_RATE = 48000
NUM_CHANNELS = 1

def read_wav_file(file_path: str) -> tuple[np.ndarray, int]:
    """Read a WAV file and return its data as a numpy array and sample rate."""
    with wave.open(file_path, 'rb') as wav_file:
        # Get WAV file parameters
        n_channels = wav_file.getnchannels()
        sampwidth = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        
        # Read the WAV data
        wav_data = wav_file.readframes(n_frames)
        wav_array = np.frombuffer(wav_data, dtype=np.int16)
        
        # Reshape if stereo
        if n_channels == 2:
            wav_array = wav_array.reshape(-1, 2)
            # Convert to mono by averaging channels
            wav_array = wav_array.mean(axis=1).astype(np.int16)
        
        # Resample if necessary (simple linear interpolation)
        if framerate != SAMPLE_RATE:
            x = np.arange(len(wav_array))
            x_new = np.linspace(0, len(wav_array) - 1, int(len(wav_array) * SAMPLE_RATE / framerate))
            wav_array = np.interp(x_new, x, wav_array).astype(np.int16)
        
        return wav_array, SAMPLE_RATE

async def play_wav(source: rtc.AudioSource, wav_filename: str) -> None:
    """Play a WAV file from the local file system."""
    import logging
    logging.info("Playing WAV: %s", wav_filename)
    wav_data, _ = read_wav_file(wav_filename)
    samples_per_channel = 480  # 10ms at 48kHz
    audio_frame = rtc.AudioFrame.create(SAMPLE_RATE, NUM_CHANNELS, samples_per_channel)
    audio_data = np.frombuffer(audio_frame.data, dtype=np.int16)
    
    position = 0
    while position < len(wav_data):
        # Get next chunk of audio data
        chunk = wav_data[position:position + samples_per_channel]
        
        # If we're at the end, pad with silence if needed
        if len(chunk) < samples_per_channel:
            # Pad the remaining space with silence
            padded_chunk = np.zeros(samples_per_channel, dtype=np.int16)
            padded_chunk[:len(chunk)] = chunk
            np.copyto(audio_data, padded_chunk)
        else:
            np.copyto(audio_data, chunk)
            
        await source.capture_frame(audio_frame)
        position += samples_per_channel
    
    # Send a few frames of silence to ensure clean ending
    for _ in range(3):
        np.copyto(audio_data, np.zeros(samples_per_channel, dtype=np.int16))
        await source.capture_frame(audio_frame)

async def play_string(source: rtc.AudioSource, text: str, lang: str = 'en') -> None:
    """Play a string of text as speech."""
    # Create temporary files for both MP3 and WAV
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3, \
         tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
        temp_mp3_filename = temp_mp3.name
        temp_wav_filename = temp_wav.name
    
    try:
        # Generate speech using gTTS
        import logging
        logging.info("TTS: %s", text)
        tts = gTTS(text=text, lang=lang)
        tts.save(temp_mp3_filename)
        
        # Convert MP3 to WAV using ffmpeg with suppressed output
        subprocess.run([
            'ffmpeg', '-y',  # Overwrite output file without asking
            '-loglevel', 'error',  # Only show errors
            '-i', temp_mp3_filename,
            '-acodec', 'pcm_s16le',
            '-ar', str(SAMPLE_RATE),
            '-ac', str(NUM_CHANNELS),
            temp_wav_filename
        ], check=True)
        
        # Play the converted WAV file
        await play_wav(source, temp_wav_filename)
    finally:
        # Clean up the temporary files
        os.unlink(temp_mp3_filename)
        os.unlink(temp_wav_filename)

async def play_audio_stream(audio_stream: rtc.AudioStream, _) -> None:
    """Play an audio stream from a LiveKit participant."""
    import logging
    import asyncio
    import sounddevice as sd
    from queue import Queue
    
    try:
        logging.info("Starting audio stream playback")
        
        # Create a queue for audio frames
        audio_queue = Queue()
        stream_active = True
        
        async def audio_stream_reader():
            """Task to read audio frames from the stream and put them in the queue."""
            nonlocal stream_active
            try:
                while stream_active:
                    try:
                        frame_event = await audio_stream.__anext__()
                        frame = frame_event.frame
                        if frame and frame.data is not None:
                            frame_data = np.frombuffer(frame.data, dtype=np.int16)
                            if len(frame_data.shape) == 1:
                                frame_data = frame_data.reshape(-1, 1)
                            frame_data = frame_data.astype(np.float32) / 32768.0
                            audio_queue.put(frame_data)
                            #logging.info("Queued audio frame - shape: %s, queue size: %d", 
                            #           frame_data.shape, audio_queue.qsize())
                    except StopAsyncIteration:
                        logging.info("Audio stream ended")
                        stream_active = False
                        break
                    except Exception as e:
                        logging.error("Error reading audio frame: %s", e)
                        stream_active = False
                        break
            except asyncio.CancelledError:
                logging.info("Audio stream reader task cancelled")
                stream_active = False
            except Exception as e:
                logging.error("Error in audio stream reader: %s", e)
                stream_active = False
        
        def audio_callback(outdata, frames, time, status):
            if status:
                logging.warning('Audio callback status: %s', status)
            
            try:
                # Get the next frame from the queue
                if not audio_queue.empty():
                    frame_data = audio_queue.get()
                    if len(frame_data) >= frames:
                        outdata[:] = frame_data[:frames]
                    else:
                        # Pad with silence if frame is too short
                        outdata[:] = np.zeros((frames, 1), dtype=np.float32)
                else:
                    # Output silence if no frame available
                    outdata[:] = np.zeros((frames, 1), dtype=np.float32)
            except Exception as e:
                logging.error("Error in audio callback: %s", e)
                outdata[:] = np.zeros((frames, 1), dtype=np.float32)
        
        # Start the audio stream reader task
        reader_task = asyncio.create_task(audio_stream_reader())
        
        try:
            devices = sd.query_devices()
            default_output = sd.default.device[1]
            logging.info("Using audio output device: %s", devices[default_output]['name'])
            logging.info("Available audio devices:")
            for i, device in enumerate(devices):
                logging.info("%d: %s", i, device['name'])
            
            # Try to use the default output device
            try:
                with sd.OutputStream(
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    callback=audio_callback,
                    device=default_output,
                    blocksize=480,  # Match the frame size we're receiving
                    dtype=np.float32,  # Use float32 for internal processing
                    finished_callback=lambda: logging.info("Audio output stream finished")
                ):
                    logging.info("Audio output stream started successfully")
                    # Keep the stream running until explicitly cancelled or stream ends
                    while stream_active:
                        try:
                            await asyncio.sleep(0.1)  # Shorter sleep interval for more responsive playback
                            # Check if we have frames in the queue
                            if audio_queue.empty() and not stream_active:
                                logging.info("No more frames and stream is inactive, stopping playback")
                                break
                        except asyncio.CancelledError:
                            logging.info("Audio playback task cancelled")
                            break
                        except Exception as e:
                            logging.error("Error in audio playback loop: %s", e)
                            break
            except Exception as e:
                logging.error("Failed to use default output device: %s", e)
                # Try to use any available output device
                for i, device in enumerate(devices):
                    if device['max_output_channels'] > 0:  # This is an output device
                        try:
                            with sd.OutputStream(
                                samplerate=SAMPLE_RATE,
                                channels=1,
                                callback=audio_callback,
                                device=i,
                                blocksize=480,
                                dtype=np.float32,
                                finished_callback=lambda: logging.info("Audio output stream finished")
                            ):
                                logging.info("Audio output stream started successfully on device %d: %s", 
                                           i, device['name'])
                                while stream_active:
                                    try:
                                        await asyncio.sleep(0.1)
                                        # Check if we have frames in the queue
                                        if audio_queue.empty() and not stream_active:
                                            logging.info("No more frames and stream is inactive, stopping playback")
                                            break
                                    except asyncio.CancelledError:
                                        logging.info("Audio playback task cancelled")
                                        break
                                    except Exception as e:
                                        logging.error("Error in audio playback loop: %s", e)
                                        break
                                break  # If we get here, we successfully started the stream
                        except Exception as e:
                            logging.error("Failed to use device %d (%s): %s", 
                                        i, device['name'], e)
                            continue
                else:
                    raise RuntimeError("No working audio output devices found")
                    
        except Exception as e:
            logging.error("Error setting up audio output: %s", e)
            raise
        finally:
            # Cancel the reader task
            reader_task.cancel()
            try:
                await reader_task
            except asyncio.CancelledError:
                pass
            
    except asyncio.CancelledError:
        logging.info("Audio stream task cancelled")
    except Exception as e:
        logging.error("Error playing audio stream: %s", e) 