import os
import logging
import asyncio
from livekit import rtc, api
from test_script import TestScript
from room_handlers import setup_room_handlers
from audio_utils import play_string, play_wav
from shared_state import audio_playback_tasks, publish_source, room

SAMPLE_RATE = 48000
NUM_CHANNELS = 1

async def handle_console_input(source: rtc.AudioSource) -> None:
    """Handle console input for controlling the agent."""
    while True:
        try:
            text = await asyncio.get_event_loop().run_in_executor(None, input)
            if text.lower() in ['/exit', '/quit']:
                logging.info("Exit command received, shutting down...")
                # Force exit immediately
                os._exit(0)
            elif text.startswith('/play_wav '):
                # Extract filename from command
                filename = text[9:].strip()
                await play_wav(source, filename)
            elif text.strip():  # If text is not empty
                await play_string(source, text)
        except asyncio.CancelledError:
            logging.info("Console input task cancelled")
            break
        except Exception as e:
            logging.error("Error processing console input: %s", e)
            if text.lower() in ['/exit', '/quit', 'exit', 'quit']:
                os._exit(1)

async def run_room(room_instance: rtc.Room, room_name: str, script: TestScript = None) -> None:
    """Run the room and handle participant connections and disconnections."""
    global publish_source, room
    room = room_instance
    
    @room.on("participant_disconnected")
    def on_participant_disconnect(participant: rtc.Participant, *_):
        logging.info("participant disconnected: %s", participant.identity)
        if script:
            script.set_connection_state("disconnected", participant.identity)

    token = (
        api.AccessToken()
        .with_identity("python-publisher")
        .with_name("Python Publisher")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
            )
        )
        .to_jwt()
    )
    url = os.getenv("LIVEKIT_URL")

    logging.info("connecting to %s", url)
    try:
        await room.connect(
            url,
            token,
            options=rtc.RoomOptions(
                auto_subscribe=True,
            ),
        )
        logging.info("connected to room %s", room.name)
    except rtc.ConnectError as e:
        logging.error("failed to connect to the room: %s", e)
        return

    # Create audio source for publishing
    publish_source = rtc.AudioSource(SAMPLE_RATE, NUM_CHANNELS)

    # publish a track for sending audio
    publish_track = rtc.LocalAudioTrack.create_audio_track("publish", publish_source)
    publish_options = rtc.TrackPublishOptions()
    publish_options.source = rtc.TrackSource.SOURCE_MICROPHONE
    publication = await room.local_participant.publish_track(publish_track, publish_options)
    logging.info("published track %s", publication.sid)

    # Start console input handling in the background
    console_task = asyncio.ensure_future(handle_console_input(publish_source))

    if script:
        try:
            # Run script commands
            while not script.is_finished():
                await script.execute_command(publish_source)
                await asyncio.sleep(0.1)  # Small delay between commands
            
            # Get and log test result
            success, message = script.get_test_result()
            if success:
                logging.info("Test completed successfully")
            else:
                logging.error(f"Test failed: {message}")
                os._exit(0)
        except asyncio.CancelledError:
            logging.info("Script execution cancelled")
            os._exit(0)
        finally:
            # Cancel the console input task and exit
            console_task.cancel()
            os._exit(0)
    else:
        # Wait for the console input task to complete
        await console_task

async def cleanup():
    """Clean up resources and tasks."""
    logging.info("Starting cleanup...")
    try:
        # Cancel all audio playback tasks first
        for task in audio_playback_tasks:
            if not task.done():
                task.cancel()
        logging.info("Cancelled all audio playback tasks")
        
        # Disconnect from the room
        if room:
            await room.disconnect()
            logging.info("Disconnected from room")
        
        # Force exit immediately
        os._exit(0)
    except Exception as e:
        logging.error("Error during cleanup: %s", e)
        os._exit(1) 