import logging

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.llm import ai_function
from livekit.agents.voice import AgentTask, CallContext, VoiceAgent
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import cartesia, deepgram, openai

# from livekit.plugins import noise_cancellation

logger = logging.getLogger("roomio-example")
logger.setLevel(logging.INFO)

load_dotenv()


class EchoTask(AgentTask):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are Echo.",
            # llm=openai.realtime.RealtimeModel(voice="echo"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
        )


    @ai_function
    async def talk_to_alloy(self, context: CallContext):
        return AlloyTask(), "Transferring you to Alloy."


class AlloyTask(AgentTask):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are Echo.",
            # llm=openai.realtime.RealtimeModel(voice="echo"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
        )

    async def on_enter(self) -> None:
        """Called when the task is entered"""
        logger.info("xxxxxxxxu on_enter")

    async def on_exit(self) -> None:
        """Called when the task is exited"""
        logger.info("xxxxxxxxu on_exit")

    async def on_end_of_turn(self, chat_ctx: llm.ChatContext, new_message: llm.ChatMessage) -> None:
        """Called when the user has finished speaking, and the LLM is about to respond

        This is a good opportunity to update the chat context or edit the new message before it is
        sent to the LLM.
        """
        logger.info(f"xxxxxxxxu on_end_of_turn: cat_ctx={chat_ctx}; new_message={new_message}")
        
    @ai_function
    async def talk_to_echo(self, context: CallContext):
        logger.info(f"xxxxxxxxu talk_to_echo {context}")
        return EchoTask(), "Transferring you to Echo."


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    agent = VoiceAgent(
        task=AlloyTask(),
    )

    await agent.start(
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint)
    )