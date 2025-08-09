import logging  
import asyncio  
from typing import Dict, Optional  
from dotenv import find_dotenv, load_dotenv  
from livekit import rtc  
from livekit.agents import (  
    JobContext,  
    WorkerOptions,  
    cli,  
)  
from livekit.agents.voice import Agent, AgentSession  
from livekit.agents.voice.room_io import RoomInputOptions, RoomOutputOptions, RoomIO  
from livekit.plugins import openai, deepgram, silero  
  
load_dotenv(find_dotenv())  
logger = logging.getLogger("multi-participant-agent")  
  
class MultiParticipantAgent(Agent):  
    def __init__(self) -> None:  
        super().__init__(  
            instructions="""  
                You are a voice assistant that can hear and respond to multiple participants   
                in a meeting. You should acknowledge different speakers and facilitate   
                conversation between all participants. When someone starts speaking,   
                focus your attention on them and respond appropriately.  
            """,  
            stt=deepgram.STT(),  
            llm=openai.LLM(model="gpt-4o-mini"),  
            tts=openai.TTS(),  
            vad=silero.VAD.load()  
        )  
  
    async def on_enter(self):  
        """Generate initial greeting when agent starts"""  
        await self.session.generate_reply(  
            instructions="Greet the participants and let them know you can hear everyone in the meeting and will focus on whoever is speaking."  
        )  
  
class ActiveSpeakerManager:  
    def __init__(self, room_io: RoomIO, session: AgentSession):  
        self.room_io = room_io  
        self.session = session  
        self.current_speaker: Optional[str] = None  
        self.speaker_timeout_task: Optional[asyncio.Task] = None  
        self.speaker_timeout_duration = 3.0  # seconds of silence before switching back to all participants  
        
    def on_active_speakers_changed(self, speakers: list[rtc.Participant]):  
        """Handle active speaker changes"""  
        if not speakers:  
            # No active speakers, switch back to listening to all participants  
            if self.current_speaker is not None:  
                logger.info(f"No active speakers, switching back to listening to all participants")  
                self.room_io.unset_participant()  
                self.current_speaker = None  
                if self.speaker_timeout_task:  
                    self.speaker_timeout_task.cancel()  
                    self.speaker_timeout_task = None  
            return  
            
        # Get the primary speaker (first in the list)  
        primary_speaker = speakers[0]  
        speaker_identity = primary_speaker.identity  
        
        # Don't switch if it's the same speaker  
        if self.current_speaker == speaker_identity:  
            return  
            
        # Cancel any existing timeout task  
        if self.speaker_timeout_task:  
            self.speaker_timeout_task.cancel()  
            
        # Switch to the new speaker  
        logger.info(f"Active speaker changed to: {speaker_identity}")  
        self.room_io.set_participant(speaker_identity)  
        self.current_speaker = speaker_identity  
        
        # Set up timeout to switch back to all participants if speaker stops  
        self.speaker_timeout_task = asyncio.create_task(self._speaker_timeout())  

    async def _speaker_timeout(self):  
        """Timeout task to switch back to listening to all participants"""  
        try:  
            await asyncio.sleep(self.speaker_timeout_duration)  
            if self.current_speaker is not None:  
                logger.info(f"Speaker timeout, switching back to listening to all participants")  
                self.room_io.unset_participant()  
                self.current_speaker = None  
        except asyncio.CancelledError:  
            # Task was cancelled, which means speaker is still active  
            pass  

async def entrypoint(ctx: JobContext):  
    await ctx.connect()  
      
    # Create agent session  
    session = AgentSession(  
        stt=deepgram.STT(),  
        llm=openai.LLM(model="gpt-4o-mini"),  
        tts=openai.TTS(),  
        vad=silero.VAD.load()  
    )  
      
    # Create RoomIO for participant switching  
    room_io = RoomIO(session, room=ctx.room)  
    await room_io.start()  
      
    # Create active speaker manager  
    speaker_manager = ActiveSpeakerManager(room_io, session)  
      
    # Set up active speaker detection  
    @ctx.room.on("active_speakers_changed")  
    def on_active_speakers_changed(speakers: list[rtc.Participant]):  
        speaker_manager.on_active_speakers_changed(speakers)  
      
    # Start session with room - this will create a default RoomIO  
    await session.start(  
        agent=MultiParticipantAgent(),  
        room=ctx.room,  
        room_input_options=RoomInputOptions(  
            participant_kinds=[  
                rtc.ParticipantKind.PARTICIPANT_KIND_SIP,  
                rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD,  
            ],  
            # Don't specify participant_identity to allow multiple participants  
        ),  
        room_output_options=RoomOutputOptions()  
    )  
      
    logger.info("Multi-participant agent started with active speaker detection")  
  
if __name__ == "__main__":  
    cli.run_app(  
        WorkerOptions(  
            entrypoint_fnc=entrypoint,  
        ),  
    )