import logging
import asyncio

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.metrics import LLMMetrics
from livekit.agents.voice import AgentTask, VoiceAgent
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import cartesia, deepgram, openai

# from livekit.plugins import noise_cancellation

logger = logging.getLogger("roomio-example")
logger.setLevel(logging.INFO)

load_dotenv()


class AlloyTask(AgentTask):
    """
    This is a basic example that demonstrates the use of LLM metrics.
    """
    def __init__(self) -> None:
        llm = openai.LLM(model="gpt-4o-mini")
        super().__init__(
            instructions="You are Echo.",
            stt=deepgram.STT(),
            llm=llm,
            tts=cartesia.TTS(),
        )
        
        # Wrap async handler in sync function
        def sync_wrapper(metrics: LLMMetrics):
            asyncio.create_task(self.on_metrics_collected(metrics))
            
        llm.on("metrics_collected", sync_wrapper)

    async def on_metrics_collected(self, metrics: LLMMetrics) -> None:
        logger.info("LLM Metrics Collected:")
        logger.info(f"\tType: {metrics.type}")
        logger.info(f"\tLabel: {metrics.label}")
        logger.info(f"\tRequest ID: {metrics.request_id}")
        logger.info(f"\tTimestamp: {metrics.timestamp}")
        logger.info(f"\tDuration: {metrics.duration:.4f}s")
        logger.info(f"\tTTFT: {metrics.ttft:.4f}s")
        logger.info(f"\tCancelled: {metrics.cancelled}")
        logger.info(f"\tCompletion Tokens: {metrics.completion_tokens}")
        logger.info(f"\tPrompt Tokens: {metrics.prompt_tokens}")
        logger.info(f"\tTotal Tokens: {metrics.total_tokens}")
        logger.info(f"\tTokens Per Second: {metrics.tokens_per_second:.2f}")


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    agent = VoiceAgent(
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