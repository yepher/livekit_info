import logging
import datetime
import json

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
)
from livekit.agents.llm import function_tool
from livekit.plugins import deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# uncomment to enable Krisp background voice/noise cancellation
# currently supported on Linux and MacOS
# from livekit.plugins import noise_cancellation

logger = logging.getLogger("basic-agent")

load_dotenv()


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


async def entrypoint(ctx: JobContext):

    async def write_transcript():
        current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # This example writes to the temporary directory, but you can save to any location
        filename = f"/tmp/transcript_{ctx.room.name}_{current_date}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session.history.to_dict(), f, indent=2)
            
        print(f"Transcript for {ctx.room.name} saved to {filename}")

    ctx.add_shutdown_callback(write_transcript)


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


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
