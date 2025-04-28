# pylint: disable=W1203
import asyncio
import logging
import os
import sys
from signal import SIGINT, SIGTERM
from typing import Set

from dotenv import load_dotenv
from livekit import rtc, api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simplified format for console output
    handlers=[logging.StreamHandler()]  # Only use console handler
)
logger = logging.getLogger("text-chat")

# Load environment variables
load_dotenv()

# Store active tasks to prevent garbage collection
_active_tasks: Set[asyncio.Task] = set()

async def handle_text_stream_async(reader: rtc.TextStreamReader, participant_identity: str):
    try:
        async for text in reader:
            logger.info(f"{participant_identity}: {text}")
    except Exception as e:
        logger.error(f"Error in text stream: {e}")

def handle_text_stream(reader: rtc.TextStreamReader, participant_identity: str):
    """Create async task for handling text stream"""
    task = asyncio.create_task(handle_text_stream_async(reader, participant_identity))
    _active_tasks.add(task)
    task.add_done_callback(_active_tasks.remove)

def log_participant_details(participant: rtc.Participant, prefix: str = "system:"):
    """Log detailed information about a participant"""
    logger.info(f"{prefix} Participant connected: {participant.identity}")
    logger.info(f"{prefix}   Name: {participant.name}")
    logger.info(f"{prefix}   SID: {participant.sid}")

    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD:
        logger.info(f"{prefix}   Kind: {participant.kind} (Standard)")
    elif participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_INGRESS:
        logger.info(f"{prefix}   Kind: {participant.kind} (Ingress)")
    elif participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_EGRESS:
        logger.info(f"{prefix}   Kind: {participant.kind} (Egress)")
    elif participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        logger.info(f"{prefix}   Kind: {participant.kind} (SIP)")
    elif participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
        logger.info(f"{prefix}   Kind: {participant.kind} (Agent)")
    else:
        logger.info(f"{prefix}   Kind: {participant.kind} (Unknown)")

    logger.info(f"{prefix}   Metadata: {participant.metadata}")
    logger.info(f"{prefix}   Attributes: {participant.attributes}")
    logger.info(f"{prefix}   Track Publications:")
    for tid, publication in participant.track_publications.items():
        log_track_details(publication, prefix + "     ", tid)

def log_track_details(publication: rtc.TrackPublication, prefix: str = "system:", track_id: str = None):
    """Log detailed information about a track"""
    if track_id:
        logger.info(f"{prefix} Track ID: {track_id}")

    if publication.kind == rtc.TrackKind.KIND_AUDIO:
        logger.info(f"{prefix}   Kind: {publication.kind} (Audio)")
    elif publication.kind == rtc.TrackKind.KIND_VIDEO:
        logger.info(f"{prefix}   Kind: {publication.kind} (Video)")
    else:
        logger.info(f"{prefix}   Kind: {publication.kind} (Unknown)")

    logger.info(f"{prefix}   Name: {publication.name}")


    if publication.source == rtc.TrackSource.SOURCE_CAMERA:
        logger.info(f"{prefix}   Source: {publication.source} (Camera)")
    elif publication.source == rtc.TrackSource.SOURCE_MICROPHONE:
        logger.info(f"{prefix}   Source: {publication.source} (Microphone)")
    elif publication.source == rtc.TrackSource.SOURCE_SCREENSHARE:
        logger.info(f"{prefix}   Source: {publication.source} (Screen Share)")
    elif publication.source == rtc.TrackSource.SOURCE_SCREENSHARE_AUDIO:
        logger.info(f"{prefix}   Source: {publication.source} (Screen Share Audio)")
    
    logger.info(f"{prefix}   Muted: {publication.muted}")
    logger.info(f"{prefix}   Simulcasted: {publication.simulcasted}")
    logger.info(f"{prefix}   Width: {publication.width}")
    logger.info(f"{prefix}   Height: {publication.height}")
    logger.info(f"{prefix}   MimeType: {publication.mime_type}")
    logger.info(f"{prefix}   Sid: {publication.sid}")

async def main(room: rtc.Room):
    logger.info("Starting text chat client...")
    logger.info("Type 'exit' or 'quit' to exit the application")
    logger.info("Press Ctrl+C to force quit")
    logger.info("----------------------------------------")
    
    # Get room name from command line or use default
    room_name = sys.argv[1] if len(sys.argv) > 1 else "text-chat-room"
    
    # Create token
    token = (
        api.AccessToken()
        .with_identity("text-user")
        .with_name("Text User")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    # Set up event handlers before connecting
    @room.on("participant_connected")
    def participant_connected(participant: rtc.Participant):
        log_participant_details(participant)

    @room.on("participant_disconnected")
    def participant_disconnected(participant: rtc.Participant):
        logger.info(f"system: Participant disconnected: {participant.identity}")

    @room.on("local_track_published")
    def local_track_published(publication: rtc.LocalTrackPublication, track: rtc.Track):
        log_track_details(publication, "system:     ", track.sid)

    @room.on("local_track_unpublished")
    def local_track_unpublished(publication: rtc.LocalTrackPublication):
        logger.info(f"system: Local track unpublished: {publication.sid}")

    @room.on("local_track_subscribed")
    def local_track_subscribed(track: rtc.Track):
        logger.info(f"system: Local track subscribed: {track.kind}")

    @room.on("track_published")
    def track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"system: Track Published by {participant.identity}:")
        for tid, publication in participant.track_publications.items():
            log_track_details(publication, "system:     ", tid)

    @room.on("track_unpublished")
    def track_unpublished(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"system: Track unpublished by {participant.identity}: {publication.sid}")

    @room.on("track_subscribed")
    def track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"system: Track subscribed from {participant.identity}: {track.kind}")

    @room.on("track_unsubscribed")
    def track_unsubscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"system: Track unsubscribed from {participant.identity}: {track.kind}")

    @room.on("track_subscription_failed")
    def track_subscription_failed(participant: rtc.RemoteParticipant, track_sid: str, error: str):
        logger.info(f"system: Track subscription failed for {participant.identity}: {error}")

    @room.on("track_muted")
    def track_muted(participant: rtc.Participant, publication: rtc.TrackPublication):
        logger.info(f"system: Track muted by {participant.identity}: {publication.sid}")

    @room.on("track_unmuted")
    def track_unmuted(participant: rtc.Participant, publication: rtc.TrackPublication):
        logger.info(f"system: Track unmuted by {participant.identity}: {publication.sid}")

    @room.on("active_speakers_changed")
    def active_speakers_changed(speakers: list[rtc.Participant]):
        speaker_ids = [s.identity for s in speakers]
        logger.info(f"system: Active speakers changed: {', '.join(speaker_ids)}")

    @room.on("room_metadata_changed")
    def room_metadata_changed(old_metadata: str, new_metadata: str):
        logger.info(f"system: Room metadata changed from '{old_metadata}' to '{new_metadata}'")

    @room.on("participant_metadata_changed")
    def participant_metadata_changed(participant: rtc.Participant, old_metadata: str, new_metadata: str):
        logger.info(f"system: Participant {participant.identity} metadata changed from '{old_metadata}' to '{new_metadata}'")

    @room.on("participant_name_changed")
    def participant_name_changed(participant: rtc.Participant, old_name: str, new_name: str):
        logger.info(f"system: Participant {participant.identity} name changed from '{old_name}' to '{new_name}'")

    @room.on("participant_attributes_changed")
    def participant_attributes_changed(changed_attributes: dict, participant: rtc.Participant):
        logger.info(f"system: Participant {participant.identity} attributes changed: {changed_attributes}")

    @room.on("connection_quality_changed")
    def connection_quality_changed(participant: rtc.Participant, quality: rtc.ConnectionQuality):
        logger.info(f"system: Connection quality changed for {participant.identity}: {quality}")

    @room.on("transcription_received")
    def transcription_received(segments: list[rtc.TranscriptionSegment], participant: rtc.Participant, publication: rtc.TrackPublication):
        for segment in segments:
            logger.info(f"system: Transcription from {participant.identity}: {segment.text}")

    @room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        try:
            # Parse the JSON data
            import json
            data_dict = json.loads(data.data)
            message = data_dict.get("message", "")
            sender = data_dict.get("from", {}).get("identity", "Unknown")
            logger.info(f"{sender}: {message}")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    @room.on("sip_dtmf_received")
    def sip_dtmf_received(sip_dtmf: rtc.SipDTMF):
        logger.info(f"system: SIP DTMF received: {sip_dtmf.digit}")

    @room.on("e2ee_state_changed")
    def e2ee_state_changed(participant: rtc.Participant, state: rtc.EncryptionState):
        logger.info(f"system: E2EE state changed for {participant.identity}: {state}")

    @room.on("connection_state_changed")
    def connection_state_changed(connection_state: rtc.ConnectionState):
        logger.info(f"system: Connection state changed: {connection_state}")

    @room.on("connected")
    def connected():
        logger.info("system: Connected to room")

    @room.on("disconnected")
    def disconnected(reason: rtc.DisconnectReason):
        logger.info(f"system: Disconnected from room: {reason}")

    @room.on("reconnecting")
    def reconnecting():
        logger.info("system: Reconnecting to room...")

    @room.on("reconnected")
    def reconnected():
        logger.info("system: Reconnected to room")

    # Register text stream handler with background task
    def register_text_handler(reader: rtc.TextStreamReader, participant_identity: str):
        task = asyncio.create_task(handle_text_stream_async(reader, participant_identity))
        _active_tasks.add(task)
        task.add_done_callback(lambda t: _active_tasks.remove(t))

    room.register_text_stream_handler("lk.chat", register_text_handler)
    room.register_text_stream_handler("lk.transcription", register_text_handler)

    # Connect to room
    logger.info(f"Connecting to room: {room_name}")
    await room.connect(os.getenv("LIVEKIT_URL"), token)
    logger.info("Connected successfully")

    # Print existing participants
    for identity, participant in room.remote_participants.items():
        logger.info(f"Existing participant: {identity}")
        log_participant_details(participant, "")

    # Create a queue for user input
    input_queue = asyncio.Queue()

    # Function to get user input in a separate thread
    def input_loop(event_loop):
        while True:
            try:
                user_input = input().strip()  # Remove the "You: " prompt from here
                if user_input.lower() in ["exit", "quit"]:
                    asyncio.run_coroutine_threadsafe(input_queue.put("exit"), event_loop)
                    break
                asyncio.run_coroutine_threadsafe(input_queue.put(user_input), event_loop)
            except (EOFError, KeyboardInterrupt):
                asyncio.run_coroutine_threadsafe(input_queue.put("exit"), event_loop)
                break

    # Start input loop in a separate thread
    import threading
    input_thread = threading.Thread(target=input_loop, args=(asyncio.get_event_loop(),), daemon=True)
    input_thread.start()

    # Main chat loop
    try:
        while True:
            # Wait for either user input or a timeout
            try:
                user_input = await asyncio.wait_for(input_queue.get(), timeout=0.1)
                if user_input == "exit":
                    logger.info("Exiting...")
                    # Get the event loop and stop it
                    loop = asyncio.get_event_loop()
                    loop.stop()
                    break
                if user_input:
                    logger.info(f"You: {user_input}")  # Add the "You:" prefix here when we actually have input
                    await room.local_participant.send_text(user_input, topic="lk.chat")
            except asyncio.TimeoutError:
                # No user input, continue processing events
                continue
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Cleanup
        await room.disconnect()
        logger.info("Disconnected from room")

if __name__ == "__main__":
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    room = rtc.Room(loop=loop)

    async def cleanup():
        await room.disconnect()
        loop.stop()

    # Start main coroutine
    main_task = asyncio.ensure_future(main(room))

    # Setup signal handlers
    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, lambda: asyncio.ensure_future(cleanup()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up any remaining tasks
        pending = asyncio.all_tasks(loop)
        for pending_task in pending:
            pending_task.cancel()
        # Run the loop until all tasks are done
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()