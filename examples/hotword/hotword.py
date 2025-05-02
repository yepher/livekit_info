import logging
from pathlib import Path
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero
import re

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):  
    def __init__(self) -> None:  
        super().__init__(  
            instructions="""  
                You are a helpful agent.  
            """,  
            stt=deepgram.STT(),  
            llm=openai.LLM(),  
            tts=openai.TTS(),  
            vad=silero.VAD.load()  
        )  
        self.hot_word_detected = False  
        self.hot_word = "hey home"  
      
    async def on_enter(self):  
        # Inform the user that the agent is waiting for the hot word  
        logger.info("Waiting for hot word: 'Hey Home'")  
        # We don't want to generate a reply immediately anymore  
        # self.session.generate_reply()  
      
    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:  
        parent_stream = super().stt_node(text, model_settings)  
          
        if parent_stream is None:  
            return None  
              
        async def process_stream():  
            async for event in parent_stream:  
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:  
                    transcript = event.alternatives[0].text.lower()  
                    logger.info(f"Received transcript: '{transcript}'")
                    
                    # Clean the transcript by removing punctuation and extra spaces
                    cleaned_transcript = re.sub(r'[^\w\s]', '', transcript)  # Remove punctuation
                    cleaned_transcript = ' '.join(cleaned_transcript.split())  # Normalize spaces
                    logger.info(f"Cleaned transcript: '{cleaned_transcript}'")
                      
                    if not self.hot_word_detected:  
                        # Check for hot word in cleaned transcript
                        if self.hot_word in cleaned_transcript:  
                            logger.info(f"Hot word detected: '{self.hot_word}'")  
                            self.hot_word_detected = True  
                              
                            # Extract content after the hot word  
                            content_after_hot_word = cleaned_transcript.split(self.hot_word, 1)[-1].strip()  
                            if content_after_hot_word:  
                                # Replace the transcript with only the content after the hot word  
                                event.alternatives[0].text = content_after_hot_word  
                                yield event  
                        # If hot word not detected, don't yield the event (discard input)  
                    else:  
                        # Hot word already detected, process this utterance  
                        yield event  
                          
                        # After end of utterance, reset to look for hot word again  
                        if str(event.type) == "SpeechEventType.END_OF_SPEECH":  
                            logger.info("End of utterance detected, waiting for hot word again")  
                            self.hot_word_detected = False  
                elif self.hot_word_detected:  
                    # Pass through other event types (like START_OF_SPEECH) when hot word is active  
                    yield event  
                  
        return process_stream()  
  
    async def on_user_turn_completed(self, chat_ctx, new_message=None):  
        # Only generate a reply if the hot word was detected  
        if self.hot_word_detected:  
            # Let the default behavior happen  
            return await super().on_user_turn_completed(chat_ctx, new_message)  
        # Otherwise, don't generate a reply  
        from livekit.agents.voice.agent_activity import StopResponse  
        raise StopResponse()

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()

    await session.start(
        agent=SimpleAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
