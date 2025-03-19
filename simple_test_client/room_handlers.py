import logging
import asyncio
from typing import Union
from livekit import rtc
from test_script import TestScript
from audio_utils import play_audio_stream
from shared_state import audio_playback_tasks  # Import from shared_state instead

def setup_room_handlers(room: rtc.Room, script: TestScript = None) -> None:
    """Set up all room event handlers."""
    
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        """Handle participant connection events."""
        logging.info("participant connected: %s %s", participant.sid, participant.identity)
        if script:
            script.set_participant_joined(participant.identity)
            script.set_connection_state("connected", participant.identity)

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        """Handle participant disconnection events."""
        logging.info("participant disconnected: %s %s", participant.sid, participant.identity)
        if script:
            script.set_connection_state("disconnected", participant.identity)

    @room.on("local_track_published")
    def on_local_track_published(
        publication: rtc.LocalTrackPublication,
        track: Union[rtc.LocalAudioTrack, rtc.LocalVideoTrack],
    ):
        """Handle local track publication events."""
        logging.info("local track published: %s", publication.sid)
        if script:
            script.set_track_state("published", publication.sid, track.kind)

    @room.on("active_speakers_changed")
    def on_active_speakers_changed(speakers: list[rtc.Participant]):
        """Handle active speakers changes."""
        logging.info("active speakers changed: %s", speakers)
        if script:
            # Check if any agent participant is speaking
            is_speaking = any(p.identity and p.identity.startswith("agent-") for p in speakers)
            script.set_speaking_state(is_speaking)
            script.set_active_speakers([p.identity for p in speakers])

    @room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        """Handle data packet reception."""
        logging.info("received data from %s: %s", data.participant.identity, data.data)
        if script:
            script.set_data_received(data.participant.identity, data.data)

    @room.on("track_muted")
    def on_track_muted(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        """Handle track muting events."""
        logging.info("track muted: %s", publication.sid)
        if script:
            script.set_track_state("muted", publication.sid, publication.kind, participant.identity)

    @room.on("track_unmuted")
    def on_track_unmuted(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        """Handle track unmuting events."""
        logging.info("track unmuted: %s", publication.sid)
        if script:
            script.set_track_state("unmuted", publication.sid, publication.kind, participant.identity)

    @room.on("local_track_unpublished")
    def on_local_track_unpublished(publication: rtc.LocalTrackPublication):
        """Handle local track unpublishing events."""
        logging.info("local track unpublished: %s", publication.sid)
        if script:
            script.set_track_state("unpublished", publication.sid, publication.kind)

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle track subscription events."""
        logging.info("track subscribed: %s (kind: %s) from participant: %s", 
                    publication.sid, track.kind, participant.identity)
        
        # Update script state if available
        if script:
            script.set_track_state("subscribed", publication.sid, track.kind, participant.identity)
        
        # Set up audio playback for all audio tracks
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logging.info("Setting up audio playback for participant: %s", participant.identity)
            if script:
                script.set_audio_received()
            
            try:
                _audio_stream = rtc.AudioStream(track)
                task = asyncio.ensure_future(play_audio_stream(_audio_stream, None))
                audio_playback_tasks.append(task)
                logging.info("Started audio playback task for participant: %s (task count: %d)", 
                           participant.identity, len(audio_playback_tasks))
            except Exception as e:
                logging.error("Failed to set up audio playback for participant %s: %s", 
                            participant.identity, e)

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle track unsubscription events."""
        logging.info("track unsubscribed: %s", publication.sid)
        if script:
            script.set_track_state("unsubscribed", publication.sid, track.kind, participant.identity)

    @room.on("connection_quality_changed")
    def on_connection_quality_changed(participant: rtc.Participant, quality: rtc.ConnectionQuality):
        """Handle connection quality changes."""
        logging.info("connection quality changed for %s", participant.identity)
        if script:
            script.set_connection_quality(participant.identity, quality)

    @room.on("track_subscription_failed")
    def on_track_subscription_failed(
        participant: rtc.RemoteParticipant, track_sid: str, error: str
    ):
        """Handle track subscription failures."""
        logging.info("track subscription failed: %s %s", participant.identity, error)
        if script:
            script.set_track_state("subscription_failed", track_sid, None, participant.identity, error)

    @room.on("connection_state_changed")
    def on_connection_state_changed(state: rtc.ConnectionState):
        """Handle connection state changes."""
        logging.info("connection state changed: %s", state)
        if script:
            script.set_connection_state(state)

    @room.on("connected")
    def on_connected() -> None:
        """Handle successful connection events."""
        logging.info("connected")
        if script:
            script.set_connection_state("connected")

    @room.on("disconnected")
    def on_disconnected() -> None:
        """Handle disconnection events."""
        logging.info("disconnected")
        if script:
            script.set_connection_state("disconnected")

    @room.on("reconnecting")
    def on_reconnecting() -> None:
        """Handle reconnection attempts."""
        logging.info("reconnecting")
        if script:
            script.set_connection_state("reconnecting")

    @room.on("reconnected")
    def on_reconnected() -> None:
        """Handle successful reconnection events."""
        logging.info("reconnected")
        if script:
            script.set_connection_state("reconnected") 