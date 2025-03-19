import json
import logging
import time
import asyncio
from typing import List, Dict, Union
from livekit import rtc
from audio_utils import play_string, play_wav

class TestScript:
    def __init__(self, filename: str, room: rtc.Room):
        self.filename = filename
        self.room = room
        self.commands: List[Dict] = []
        self.current_index = 0
        self.load_script()
        self.participant_joined = False
        self.expected_participant = None
        self.audio_received = False
        self.audio_timeout = None
        self.test_failed = False
        self.failure_reason = None
        self.is_speaking = False
        self.last_speaking_change = time.time()
        self.connection_state = "disconnected"
        self.active_speakers = []
        self.data_received = {}
        self.track_states = {}
        self.connection_qualities = {}  # Track connection quality by participant

    def load_script(self):
        """Load and parse the test script file."""
        try:
            with open(self.filename, 'r') as f:
                self.commands = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing script file: {e}")
            raise
        except FileNotFoundError:
            logging.error(f"Script file not found: {self.filename}")
            raise

    def set_participant_joined(self, participant_identity: str):
        """Mark that a participant has joined."""
        if participant_identity and participant_identity.startswith("agent-"):
            self.participant_joined = True
            self.expected_participant = participant_identity  # Store the actual agent identity
            logging.info(f"Agent participant {participant_identity} has joined")
            self.set_connection_state("connected", participant_identity)

    def set_audio_received(self):
        """Mark that audio has been received from the expected participant."""
        if not self.audio_received:
            self.audio_received = True
            logging.info("Audio received from participant")
            self.set_track_state("published", "test_track_sid", "audio", self.expected_participant)

    def set_speaking_state(self, is_speaking: bool):
        """Update the speaking state of the participant."""
        if self.is_speaking != is_speaking:
            self.is_speaking = is_speaking
            self.last_speaking_change = time.time()
            logging.info(f"Participant speaking state changed: {is_speaking}")

    def set_test_failed(self, reason: str):
        """Mark the test as failed with a reason."""
        self.test_failed = True
        self.failure_reason = reason
        logging.error(f"Test failed: {reason}")

    def set_connection_state(self, state: str, participant_identity: str = None):
        """Update the connection state."""
        self.connection_state = state
        logging.info(f"Connection state changed to: {state}")
        if participant_identity:
            logging.info(f"Connection state for {participant_identity}: {state}")
            # If participant disconnected, clear their quality
            if state == "disconnected":
                self.connection_qualities.pop(participant_identity, None)

    def set_active_speakers(self, speakers: list[str]):
        """Update the list of active speakers."""
        self.active_speakers = speakers
        logging.info(f"Active speakers changed: {speakers}")

    def set_data_received(self, participant_identity: str, data: bytes):
        """Update the received data for a participant."""
        self.data_received[participant_identity] = data
        logging.info(f"Data received from {participant_identity}: {data[:10]}...")

    def set_track_state(self, state: str, sid: str, kind: str, participant_identity: str = None, error: str = None):
        """Update the track state."""
        self.track_states[sid] = {
            "state": state,
            "kind": kind,
            "participant": participant_identity,
            "error": error
        }
        logging.info(f"Track state changed: {state} for {sid} ({kind})")
        if participant_identity:
            logging.info(f"Track state for {participant_identity}: {state} for {sid} ({kind})")
        if error:
            logging.error(f"Track error: {error}")

    def set_connection_quality(self, participant_identity: str, quality: rtc.ConnectionQuality):
        """Update the connection quality for a participant."""
        self.connection_qualities[participant_identity] = quality
        logging.info(f"Connection quality for {participant_identity}: {quality}")
        # If quality is poor (0), we might want to fail the test
        if quality == 0:  # POOR quality
            self.set_test_failed(f"Poor connection quality detected for {participant_identity}")

    def get_connection_quality(self, participant_identity: str) -> rtc.ConnectionQuality:
        """Get the connection quality for a participant."""
        return self.connection_qualities.get(participant_identity, 0)  # Default to POOR if unknown

    async def execute_command(self, source: rtc.AudioSource) -> bool:
        """Execute the next command in the script."""
        if self.current_index >= len(self.commands):
            return False

        command = self.commands[self.current_index]
        cmd_type = command.get('type')
        params = command.get('params', {})

        try:
            if cmd_type == 'wait_for_participant':
                timeout = params.get('timeout', 30)  # Default 30 seconds timeout
                self.participant_joined = False
                
                # Wait for the participant to join with timeout
                start_time = time.time()
                while not self.participant_joined:
                    if time.time() - start_time > timeout:
                        self.set_test_failed("Timeout waiting for agent participant to join")
                        return False
                    await asyncio.sleep(0.1)
                
                logging.info(f"Agent participant joined, continuing script")
                self.current_index += 1
                return True

            elif cmd_type == 'wait_for_audio':
                timeout = params.get('timeout', 30)  # Default 30 seconds timeout
                self.audio_received = False
                
                # Wait for audio with timeout
                start_time = time.time()
                while not self.audio_received:
                    if time.time() - start_time > timeout:
                        self.set_test_failed("Timeout waiting for audio from participant")
                        return False
                    # If we detect the agent speaking, consider that audio received
                    if self.is_speaking and self.expected_participant in self.active_speakers:
                        self.set_audio_received()
                        break
                    await asyncio.sleep(0.1)
                
                logging.info("Audio received from participant")
                self.current_index += 1
                return True

            elif cmd_type == 'wait_for_silence':
                timeout = params.get('timeout', 30)  # Default 30 seconds timeout
                silence_threshold = 1.0  # Seconds of silence required
                
                # Wait for silence with timeout
                start_time = time.time()
                while True:
                    if time.time() - start_time > timeout:
                        self.set_test_failed("Timeout waiting for participant to stop speaking")
                        return False
                    
                    # Check if we've had enough silence
                    if not self.is_speaking and (time.time() - self.last_speaking_change) >= silence_threshold:
                        logging.info("Participant has stopped speaking")
                        self.current_index += 1
                        return True
                    
                    await asyncio.sleep(0.1)
                
            elif cmd_type == 'tts':
                text = params.get('text', '')
                lang = params.get('lang', 'en')
                await play_string(source, text, lang)
            elif cmd_type == 'wav':
                filename = params.get('filename')
                if filename:
                    await play_wav(source, filename)
            elif cmd_type == 'wait':
                seconds = params.get('seconds', 1)
                await asyncio.sleep(seconds)
            elif cmd_type == 'event':
                event_type = params.get('event_type')
                if event_type == 'participant_connected':
                    participant_info = {
                        'sid': 'test_sid',
                        'identity': 'test_identity',
                        'name': 'Test Participant',
                        'metadata': '',
                        'is_speaking': False,
                        'audio_level': 0,
                        'connection_quality': rtc.ConnectionQuality.EXCELLENT
                    }
                    self.room.emit('participant_connected', participant_info)
                elif event_type == 'participant_disconnected':
                    participant_info = {
                        'sid': 'test_sid',
                        'identity': 'test_identity',
                        'name': 'Test Participant'
                    }
                    self.room.emit('participant_disconnected', participant_info)
                elif event_type == 'track_subscribed':
                    participant_info = {
                        'sid': 'test_sid',
                        'identity': 'test_identity',
                        'name': 'Test Participant'
                    }
                    track_info = {
                        'sid': 'test_track_sid',
                        'name': 'test_track',
                        'kind': rtc.TrackKind.KIND_AUDIO,
                        'muted': False,
                        'stream_state': rtc.StreamState.ACTIVE
                    }
                    self.room.emit('track_subscribed', track_info, participant_info)
            else:
                logging.warning(f"Unknown command type: {cmd_type}")

            self.current_index += 1
            return True
        except Exception as e:
            self.set_test_failed(f"Error executing command {self.current_index}: {e}")
            return False

    def is_finished(self) -> bool:
        """Check if all commands have been executed."""
        return self.current_index >= len(self.commands) or self.test_failed

    def get_test_result(self) -> tuple[bool, str]:
        """Get the test result and reason if failed."""
        return not self.test_failed, self.failure_reason if self.test_failed else "Test completed successfully" 