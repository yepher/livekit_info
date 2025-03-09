import logging
import asyncio

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.metrics import TTSMetrics
from livekit.agents.voice import AgentTask, VoiceAgent
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import cartesia, deepgram, openai

logger = logging.getLogger("roomio-example")
logger.setLevel(logging.INFO)

load_dotenv()


class AlloyTask(AgentTask):
    """
    This is a basic example that demonstrates the use of TTS metrics.
    """
    def __init__(self) -> None:
        llm = openai.LLM(model="gpt-4o-mini")
        stt = deepgram.STT()
        tts = cartesia.TTS()
        super().__init__(
            instructions="You are Alloy, a helpful assistant.",
            stt=stt,
            llm=llm,
            tts=tts
        )
        
        # Wrap async handler in sync function
        def sync_wrapper(metrics: TTSMetrics):
            asyncio.create_task(self.on_metrics_collected(metrics))
            
        tts.on("metrics_collected", sync_wrapper)

    async def on_metrics_collected(self, metrics: TTSMetrics) -> None:
        logger.info("TTS Metrics Collected:")
        logger.info(f"\tType: {metrics.type}")
        logger.info(f"\tLabel: {metrics.label}")
        logger.info(f"\tRequest ID: {metrics.request_id}")
        logger.info(f"\tTimestamp: {metrics.timestamp}")
        logger.info(f"\tTTFB: {metrics.ttfb:.4f}s")
        logger.info(f"\tDuration: {metrics.duration:.4f}s")
        logger.info(f"\tAudio Duration: {metrics.audio_duration:.4f}s")
        logger.info(f"\tCancelled: {metrics.cancelled}")
        logger.info(f"\tCharacters Count: {metrics.characters_count}")
        logger.info(f"\tStreamed: {metrics.streamed}")
        logger.info(f"\tSpeech ID: {metrics.speech_id}")
        logger.info(f"\tError: {metrics.error}")


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