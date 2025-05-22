import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, elevenlabs, silero

logger = logging.getLogger("voice-switcher")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class VoiceSwitcherAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. 
                You can switch to a different voice if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(
                model="nova-2-general",
                language="en"
            ),
            llm=openai.LLM(model="gpt-4o"),
            tts=elevenlabs.TTS(
                language="en",
                model="eleven_turbo_v2_5",
            ),
            vad=silero.VAD.load()
        )
        self.current_voice = "Rachel"
        
        self.voice_names = {
            "Rachel": "Rachel",
            "Adam": "Adam",
            "Antoni": "Antoni",
            "Bella": "Bella",
            "Elli": "Elli"
        }
        
        self.voice_ids = {
            "Rachel": "21m00Tcm4TlvDq8ikWAM",
            "Adam": "pNInz6obpgDQGcFmaJgB",
            "Antoni": "ErXwobaYiN019PkySvjV",
            "Bella": "EXAVITQu4vr4xnSDxMaL",
            "Elli": "MF3mGyEYCl7XYWbV9V6O"
        }
        
        self.greetings = {
            "Rachel": "Hello! I'm now speaking with Rachel's voice. How can I help you today?",
            "Adam": "Hello! I'm now speaking with Adam's voice. How can I help you today?",
            "Antoni": "Hello! I'm now speaking with Antoni's voice. How can I help you today?",
            "Bella": "Hello! I'm now speaking with Bella's voice. How can I help you today?",
            "Elli": "Hello! I'm now speaking with Elli's voice. How can I help you today?"
        }

    async def on_enter(self):
        await self.session.say(f"Hi there! I'm speaking with Rachel's voice. I can switch between different voices including Adam, Antoni, Bella, and Elli. Just ask me to switch to any of these voices. How can I help you today?")

    async def _switch_voice(self, voice_name: str) -> None:
        """Helper method to switch the voice"""
        if voice_name == self.current_voice:
            await self.session.say(f"I'm already speaking with {voice_name}'s voice.")
            return
        
        if self.tts is not None:
            self.tts.update_options(voice_id=self.voice_ids[voice_name])
        
        self.current_voice = voice_name
        
        await self.session.say(self.greetings[voice_name])

    @function_tool
    async def switch_to_rachel(self):
        """Switch to Rachel's voice"""
        await self._switch_voice("Rachel")

    @function_tool
    async def switch_to_adam(self):
        """Switch to Adam's voice"""
        await self._switch_voice("Adam")
    
    @function_tool
    async def switch_to_antoni(self):
        """Switch to Antoni's voice"""
        await self._switch_voice("Antoni")
    
    @function_tool
    async def switch_to_bella(self):
        """Switch to Bella's voice"""
        await self._switch_voice("Bella")
    
    @function_tool
    async def switch_to_elli(self):
        """Switch to Elli's voice"""
        await self._switch_voice("Elli")


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()

    await session.start(
        agent=VoiceSwitcherAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
