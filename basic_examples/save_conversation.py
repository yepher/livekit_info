""" save_conversation.py
 This script is used to asynchronously save the conversation to:
      ./transcripts/YYYYMMDD_HHMMSS_room_name.txt
 
 It is not practical as a production script, since it saves the conversation to a local file/
 but it can be instructive to see how how to see events that happens in the session
"""

import logging
import asyncio
import datetime
from pathlib import Path
import aiofiles

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    ConversationItemAddedEvent,
    JobContext,
    JobProcess,
    RoomInputOptions,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
)
from livekit.agents.llm import function_tool
from livekit.agents.voice import MetricsCollectedEvent, FunctionToolsExecutedEvent
from livekit.plugins import deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# uncomment to enable Krisp background voice/noise cancellation
# currently supported on Linux and MacOS
# from livekit.plugins import noise_cancellation

logger = logging.getLogger("basic-agent")

load_dotenv()

# Create transcriptions directory if it doesn't exist
Path("transcripts").mkdir(exist_ok=True)

async def entrypoint(ctx: JobContext):
    # Create a queue for transcriptions
    log_queue = asyncio.Queue()
    start_time = datetime.datetime.now()

    async def write_transcription():
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"transcripts/{timestamp}_{ctx.room.name}.txt"
        async with aiofiles.open(filename, "w") as f:
            while True:
                msg = await log_queue.get()
                if msg is None:
                    break
                await f.write(msg)
                await f.flush()  # Ensure the message is written to disk immediately

    # each log entry will include these fields
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "user_id": "your user_id",
    }
    await ctx.connect()

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        # any combination of STT, LLM, TTS, or realtime API can be used
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=deepgram.STT(model="nova-3", language="multi"),
        tts=openai.TTS(voice="ash"),
        # use LiveKit's turn detection model
        turn_detection=MultilingualModel(),
    )

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        # This logs every metric event which can be excessive
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        msg = f"{timestamp} - Metrics collected: {ev}\n"
        log_queue.put_nowait(msg)
        print(msg.strip())


    @session.on("conversation_item_added")
    def on_conversation_item_added(event: ConversationItemAddedEvent):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # to iterate over all types of content:
        for content in event.item.content:
            if isinstance(content, str):
                msg = f"{timestamp} - Chat Context: {event.item.role}: {content} (interrupted={event.item.interrupted})\n"
                log_queue.put_nowait(msg)
                print(msg.strip())
            else:
                msg = f"{timestamp} - Unknown content type: {type(content)}\n"
                log_queue.put_nowait(msg)
                print(msg.strip())

    @session.on("function_tools_executed")
    def on_function_tools_executed(event: FunctionToolsExecutedEvent):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"{timestamp} - Function tools executed: {event}\n"
        log_queue.put_nowait(msg)
        print(msg.strip())

    # Start the transcription writer task
    write_task = asyncio.create_task(write_transcription())

    async def finish_queue():
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        msg = f"\nSession Duration: {days} days, {hours} hours, {minutes} minutes, {seconds} seconds\n"
        log_queue.put_nowait(msg)
        log_queue.put_nowait(None)
        await write_task

    ctx.add_shutdown_callback(finish_queue)

    # wait for a participant to join the room
    await ctx.wait_for_participant()

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # uncomment to enable Krisp BVC noise cancellation
            # noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Kelly. You would interact with users via voice."
            "with that in mind keep your responses concise and to the point."
            "You are curious and friendly, and have a sense of humor.",
        )

    async def on_enter(self):
        # when the agent is added to the session, it'll generate a reply
        # according to its instructions
        self.session.generate_reply()

    # all functions annotated with @function_tool will be passed to the LLM when this
    # agent is active
    @function_tool
    async def lookup_weather(
        self,
        context: RunContext,
        location: str,
        latitude: str,
        longitude: str,
    ):
        """Called when the user asks for weather related information.
        Ensure the user's location (city or region) is provided.
        When given a location, please estimate the latitude and longitude of the location and
        do not ask the user for them.

        Args:
            location: The location they are asking for
            latitude: The latitude of the location
            longitude: The longitude of the location
        """

        logger.info(f"Looking up weather for {location}")

        return {
            "weather": "sunny",
            "temperature": 70,
            "location": location,
        }


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))