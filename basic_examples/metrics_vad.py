import logging

import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, vad
from livekit.agents.voice import AgentTask, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import cartesia, deepgram, openai, silero

logger = logging.getLogger("roomio-example")
logger.setLevel(logging.INFO)

load_dotenv()



class AlloyTask(AgentTask):
    def __init__(self) -> None:
        silero_vad = silero.VAD.load()
        super().__init__(
            instructions="You are Echo.",
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero_vad,
        )

   # Wrap async handler in sync function
        def sync_wrapper(event: vad.VADEvent):
            asyncio.create_task(self.on_vad_event(event))
            
        silero_vad.on("metrics_collected", sync_wrapper)


    def on_vad_event(self, event: vad.VADEvent):
        #VAD event: type='vad_metrics' label='livekit.plugins.silero.vad.VAD' timestamp=1741546116.7182899 idle_time=0.5794750419445336 inference_duration_total=0.007693251594901085 inference_count=32 speech_id=None error=None
        logger.info(f"VAD event")
        logger.info(f"\ttype: {event.type}")
        logger.info(f"\ttimestamp: {event.timestamp}")
        logger.info(f"\tidle_time: {event.idle_time}")
        logger.info(f"\tinference_duration_total: {event.inference_duration_total}")
        logger.info(f"\tinference_count: {event.inference_count}")
        logger.info(f"\tspeech_id: {event.speech_id}")
        logger.info(f"\terror: {event.error}")


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