import logging

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import cartesia, deepgram, openai

logger = logging.getLogger("roomio-example")
logger.setLevel(logging.INFO)

load_dotenv()


class AlloyAgent(Agent):
    """
    This is a basic example that demonstrates the use of Agent hooks.
    """
    def __init__(self) -> None:
        super().__init__(
            instructions="You are Echo.",
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
        )

    async def on_enter(self) -> None:
        """Called when the task is entered"""
        logger.info("on_enter")

    async def on_exit(self) -> None:
        """Called when the task is exited"""
        logger.info("on_exit")

    async def on_end_of_turn(self, chat_ctx: llm.ChatContext, new_message: llm.ChatMessage) -> None:
        """Called when the user has finished speaking, and the LLM is about to respond

        This is a good opportunity to update the chat context or edit the new message before it is
        sent to the LLM.
        """
        logger.info(f"on_end_of_turn: cat_ctx={chat_ctx}; new_message={new_message}")



async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()

    await session.start(
        agent=AlloyAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint)
    )