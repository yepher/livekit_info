# LiveKit Agent Test Driver

This project provides a test driver for LiveKit agents, allowing you to simulate and test agent interactions in a LiveKit room. It supports both manual testing through console interaction and automated testing through JSON test scripts.

## Project Structure

The project is organized into several modules:

- `agent_driver.py`: Main entry point that handles command-line arguments and sets up the test environment
- `audio_utils.py`: Handles all audio-related functionality (WAV playback, text-to-speech, audio streaming)
- `test_script.py`: Manages test script execution and state tracking
- `room_handlers.py`: Contains all LiveKit room event handlers
- `room_manager.py`: Manages room connections and console interaction

## Prerequisites

- Python 3.7+
- LiveKit server URL and credentials
- FFmpeg (for audio conversion)
- Required Python packages: (see `requirements.txt`)
  ```
  livekit
  numpy
  sounddevice
  gtts
  ```

## Environment Setup

1. Set the following environment variables:
   ```bash
   export LIVEKIT_URL="your_livekit_server_url"
   export LIVEKIT_API_KEY="your liveket API key"
   export LIVEKIT_API_SECRET="your livekit API secret"
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Run the agent driver with a specific room:

```bash
python agent_driver.py --room my-room
```

### Running Tests

Run a specific test script:

```bash
python agent_driver.py --room my-room --test test_name
```

The test script should be located in the `tests` directory with a `.json` extension.

## Console Interaction

When running without a test script, you can interact with the agent through the console:

- Type any text and press Enter to convert it to speech and play it
- Use `/play_wav filename.wav` to play a WAV file
- Use `/exit` or `/quit` to exit the program

## Writing Test Scripts

Test scripts are JSON files that define a sequence of commands and expected events. Place your test scripts in the `tests` directory.

### Test Script Format

```json
[
  {
    "type": "wait_for_participant",
    "params": {
      "timeout": 30
    }
  },
  {
    "type": "wait_for_audio",
    "params": {
      "timeout": 30
    }
  },
  {
    "type": "tts",
    "params": {
      "text": "Hello, this is a test",
      "lang": "en"
    }
  },
  {
    "type": "wav",
    "params": {
      "filename": "test_audio.wav"
    }
  },
  {
    "type": "wait",
    "params": {
      "seconds": 2
    }
  }
]
```

### Available Commands

1. `wait_for_participant`
   - Waits for an agent participant to join the room
   - Optional `timeout` parameter (default: 30 seconds)

2. `wait_for_audio`
   - Waits for audio to be received from the agent
   - Optional `timeout` parameter (default: 30 seconds)

3. `wait_for_silence`
   - Waits for the agent to stop speaking
   - Optional `timeout` parameter (default: 30 seconds)

4. `tts`
   - Converts text to speech and plays it
   - Required `text` parameter
   - Optional `lang` parameter (default: "en")

5. `wav`
   - Plays a WAV file
   - Required `filename` parameter

6. `wait`
   - Waits for a specified number of seconds
   - Required `seconds` parameter

7. `event`
   - Simulates a LiveKit event
   - Required `event_type` parameter
   - Supported events:
     - `participant_connected`
     - `participant_disconnected`
     - `track_subscribed`

### Test State Tracking

The test script automatically tracks:
- Participant connection state
- Audio reception
- Speaking state
- Track states
- Connection quality
- Active speakers

### Test Results

The test will fail if:
- A participant doesn't join within the timeout period
- Audio is not received within the timeout period
- The agent doesn't stop speaking within the timeout period
- Poor connection quality is detected
- Any command execution fails

## Logging

All operations are logged to both the console and a `publish_wave.log` file. The log includes:
- Room connection events
- Participant events
- Audio playback events
- Test execution progress
- Errors and warnings

## Error Handling

The program handles various error conditions:
- Connection failures
- Audio playback errors
- Test script parsing errors
- Timeout conditions
- Resource cleanup

## Cleanup

When the program exits (either through normal completion or error), it will:
1. Cancel all audio playback tasks
2. Disconnect from the LiveKit room
3. Clean up temporary files
4. Log the final state 