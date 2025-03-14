import logging

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import cartesia, deepgram, openai, silero

logger = logging.getLogger("roomio-example")
logger.setLevel(logging.INFO)

load_dotenv()


class AlloyTask(Agent):
    """
    This is a basic example that demonstrates the use of Agent hooks.
    """
    def __init__(self) -> None:
        super().__init__(
            instructions="You are Echo.",
            stt=openai.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(),
            vad=silero.VAD.load(),
        )


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    agent = AgentSession(
        task=AlloyTask(),
    )

    await agent.start(
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint)
    )
