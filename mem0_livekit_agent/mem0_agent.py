import logging
import os
from typing import Optional

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
    metrics,
)
from livekit.agents.llm import function_tool
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from mem0 import AsyncMemoryClient


logger = logging.getLogger("basic-agent")

load_dotenv()

MEM0_API_KEY = os.getenv("MEM0_API_KEY")
if not MEM0_API_KEY:
    raise ValueError("MEM0_API_KEY is not set")

logger.info("Initializing Mem0 client...")
mem0 = AsyncMemoryClient(api_key=MEM0_API_KEY)


class MyAgent(Agent):
    def __init__(self, username: Optional[str] = None) -> None:
        super().__init__(
            instructions="""
            You are a helpful voice assistant.
            You are a travel guide named George and will help the user to plan a travel trip of their dreams. 
            You should help the user plan for various adventures like work retreats, family vacations or solo backpacking trips. 
            You should be careful to not suggest anything that would be dangerous, illegal or inappropriate.
            You can remember past interactions and use them to inform your answers.
            Use semantic memory retrieval to provide contextually relevant responses. 
            """,
        )
        self.user_id = username or "default_user"
        self.memories = []
        logger.info(f"Initialized agent for user: {self.user_id}")

    @function_tool
    async def wipe_memories(self, context: RunContext):
        """Delete all stored memories for the current user. Use this when the user wants to start fresh."""
        try:
            if not self.user_id:
                logger.error("No user_id available for wiping memories")
                return "I had trouble clearing my memories - no user identified"

            logger.info(f"Attempting to delete all memories for user: {self.user_id}")
            
            # Delete all memories for the user using the correct method
            await mem0.delete_all(user_id=self.user_id)
            
            self.memories = []
            logger.info(f"Successfully wiped memories for user: {self.user_id}")
            return "I've cleared all my memories. We can start fresh!"
        except Exception as e:
            logger.error(f"Error wiping memories for user {self.user_id}: {str(e)}")
            logger.error(f"Full error details: {e.__dict__ if hasattr(e, '__dict__') else str(e)}")
            return "I had trouble clearing my memories. Please try again."

    @function_tool
    async def store_important_info(self, context: RunContext, info: str, category: str):
        """Store important information about the user's travel plans in memory.
        This function is called automatically by the LLM when it identifies important details
        about the user's travel preferences, plans, or requirements.
        
        Args:
            info: The important information to store
            category: The category of information (e.g., 'travel_planning', 'preferences', 'requirements')
        """
        try:
            if not self.user_id:
                logger.error("No user_id available for storing information")
                return "I had trouble storing that information - no user identified"

            logger.info(f"Storing important information for user {self.user_id}: {info}")
            
            # Format the memory data according to Mem0's API requirements
            messages = [
                {
                    "role": "assistant",
                    "content": info
                }
            ]
            
            logger.debug(f"Attempting to store memory with data: {messages}")
            result = await mem0.add(
                messages,
                user_id=self.user_id,
                version="v2"  # Specify version as per documentation
            )
            logger.debug(f"Memory storage result: {result}")
            
            self.memories.append(info)
            return f"Stored important information about {category}"
        except Exception as e:
            logger.error(f"Error storing important information for user {self.user_id}: {str(e)}")
            logger.error(f"Full error details: {e.__dict__ if hasattr(e, '__dict__') else str(e)}")
            return "I had trouble storing that information"

    async def on_enter(self):
        # Load previous memories when agent starts
        try:
            if not self.user_id:
                logger.error("No user_id available for loading memories")
                self.session.generate_reply(instructions="Greet the user and say: I'm glad we're talking for the first time! I'm excited to help you plan your dream trip.")
                return

            logger.info(f"Attempting to load memories for user: {self.user_id}")
            
            # Get all memories for the user using the correct format
            memories = await mem0.get_all(
                filters={
                    "AND": [
                        {
                            "user_id": self.user_id
                        }
                    ]
                },
                version="v2"
            )
            
            if memories:
                logger.debug(f"Retrieved memories: {memories}")
                # Extract memory content from the correct field
                self.memories = [memory["memory"] for memory in memories if "memory" in memory]
                logger.info(f"Successfully loaded {len(self.memories)} previous memories for user {self.user_id}")
                
                if self.memories:
                    # Create a detailed summary of previous trip plans
                    summary = "I remember our previous conversation about your trip plans. "
                    
                    # Find the most recent trip-related memory
                    trip_memories = [m for m in self.memories if any(word in m.lower() for word in ["trip", "travel", "vacation", "cruise", "backpacking"])]
                    
                    if trip_memories:
                        # Get the most recent memory (assuming they're in chronological order)
                        latest_memory = trip_memories[0]
                        summary += f"You were planning to {latest_memory.lower()}. Would you like to continue planning this trip?"
                    else:
                        summary += "Let's continue planning your adventure!"
                    
                    self.session.generate_reply(instructions=f"Greet {self.user_id} and say: {summary}")
                else:
                    logger.info(f"No valid memories found for user {self.user_id}")
                    self.session.generate_reply(instructions="Greet the user and say: I'm glad we're talking for the first time! I'm excited to help you plan your dream trip.")
            else:
                logger.info(f"No previous memories found for user {self.user_id}")
                self.session.generate_reply(instructions="Greet the user and say: I'm glad we're talking for the first time! I'm excited to help you plan your dream trip.")
        except Exception as e:
            logger.error(f"Error loading memories for user {self.user_id}: {str(e)}")
            logger.error(f"Full error details: {e.__dict__ if hasattr(e, '__dict__') else str(e)}")
            self.memories = []  # Initialize empty memories list on error
            self.session.generate_reply(instructions="Greet the user and say: I'm glad we're talking for the first time! I'm excited to help you plan your dream trip.")


    async def on_exit(self):
        """Ensure all memories are stored when the session ends"""
        try:
            # Double check that all messages were stored
            if self.memories:
                logger.info(f"Final memory check - storing {len(self.memories)} memories")
                for memory in self.memories:
                    await mem0.add(
                        [{"role": "assistant", "content": memory}],
                        user_id=self.user_id
                    )
        except Exception as e:
            logger.error(f"Error in final memory storage: {str(e)}")

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # each log entry will include these fields
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "user_id": "your user_id",
    }
    await ctx.connect()

    # Wait for participant
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant: {participant.identity}")

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        # any combination of STT, LLM, TTS, or realtime API can be used
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=deepgram.STT(model="nova-3", language="multi"),
        tts=openai.TTS(voice="ash"),
        # use LiveKit's turn detection model
        turn_detection=MultilingualModel(),
    )

    # log metrics as they are emitted, and total usage after session is over
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    # shutdown callbacks are triggered when the session is over
    ctx.add_shutdown_callback(log_usage)

    # wait for a participant to join the room
    await ctx.wait_for_participant()

    await session.start(
        agent=MyAgent(username=participant.identity),  # Pass participant identity as username
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # uncomment to enable Krisp BVC noise cancellation
            # noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))