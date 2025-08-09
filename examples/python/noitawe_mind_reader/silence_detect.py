import asyncio
import logging
import random
import uuid
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import openai, silero, deepgram

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Create debug directory if it doesn't exist
debug_dir = Path("debug")
debug_dir.mkdir(exist_ok=True)

logger = logging.getLogger("twenty-questions-game")
logger.setLevel(logging.INFO)

# Set up transcript logging in debug directory
transcript_logger = logging.getLogger("transcript")
transcript_logger.setLevel(logging.INFO)
transcript_handler = logging.FileHandler(debug_dir / f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
transcript_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
transcript_logger.addHandler(transcript_handler)

def print_to_console(text: str, prefix: str = ""):
    """Print text to console with optional prefix"""
    if prefix:
        print(f"{prefix} {text}")
    else:
        print(text)
    sys.stdout.flush()  # Ensure immediate output

class TwentyQuestionsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are no-it-awe, the mind reading AI. I am hosting a 20 Questions game. The user will think of a famous person, place, or thing.
                You will ask up to 20 yes/no questions to try to guess what they're thinking of.
                
                CRITICAL RULES - READ CAREFULLY:
                - Ask ONLY ONE question at a time using the ask_question function
                - NEVER call ask_question more than once in a single response
                - Wait for the user's response before asking the next question
                - Do NOT ask multiple questions in a single response
                - Do NOT speak questions out loud - only use the ask_question function
                - Do NOT generate any text responses when using function tools
                - After each question, wait for the response before continuing
                - When using ask_question, make_guess, or make_final_guess functions, do NOT add any additional text
                - If you think you know the answer, use make_guess function
                - If you run out of questions, use make_final_guess function
                
                TIMEOUT HANDLING:
                - If the user doesn't answer a question in time, it doesn't count as one of the 20 questions
                - When a timeout occurs, ask a DIFFERENT question, not the same one
                - Use the timeout as an opportunity to ask a more specific or different type of question
                
                GAME START:
                - After the greeting, immediately ask your first question using ask_question
                - Start with a simple question like "Is it a living thing?" or "Is it a person?"
                
                QUESTION FORMAT:
                - Use ask_question with ONLY the question text (e.g., "Is it a human", "Is it an animal")
                - Do NOT include timeout information in the question
                - Do NOT include question marks in the question text
                - Keep questions simple and yes/no format
                
                DEBUGGING TOOL:
                - If the user says "dump session history", use the dump_session_history function
                - This will save the current session history to a timestamped file for debugging
                
                IMPORTANT: You can only call ONE function per response. Choose carefully.
                
                Be engaging and make the game fun, but remember: ONE QUESTION AT A TIME and NO TEXT WHEN USING FUNCTIONS!
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )
        self._question_number = 0
        self._max_questions = 20
        self._game_active = False
        self._waiting_for_response = False
        self._current_question = None
        self._response_received = asyncio.Event()
        self._question_lock = asyncio.Lock()
        self._last_user_response = None
        self._question_queue = asyncio.Queue()
        self._processing_question = False
        self._question_just_queued = False

    @function_tool
    async def ask_question(
        self,
        context: RunContext,
        question: str
    ) -> str:
        """
        Ask the user a yes/no question and wait for their response.
        
        Args:
            question: The yes/no question to ask the user (should be just the question, no timeout info)
        """
        # Clean the question text - remove any timeout information
        clean_question = question.split("You have")[0].strip()
        if clean_question.endswith("?"):
            clean_question = clean_question[:-1].strip()
        
        # Add question to queue
        await self._question_queue.put(clean_question)
        transcript_logger.info(f"QUEUED: {clean_question}")
        
        # Only process the queue if not currently processing and not waiting for response
        if not self._processing_question and not self._waiting_for_response:
            asyncio.create_task(self._process_question_queue())
        
        self._question_just_queued = True
        return f"Question queued: {clean_question}"

    async def on_enter(self):
        """Start the 20 Questions game"""
        self._game_active = True
        self._question_number = 0
        self._waiting_for_response = False
        self._current_question = None
        self._response_received = asyncio.Event()
        self._last_user_response = None
        self._processing_question = False
        self._question_just_queued = False
        
        transcript_logger.info("=== GAME STARTED ===")
        
        # Set up event handlers for TTS and STT logging
        self._setup_logging_handlers()
        
        greeting_text = (
            "Hello, I am no-it-awe, the mind reading AI! I am hosting a 20 Questions game. "
            "Think of a famous person, place, or thing. "
            "I will ask you up to 20 yes/no questions to try to guess what you're thinking of. "
            "You have between 5 and 15 seconds to answer each question. "
            "Ready? Let's begin!"
        )
        
        await self.session.say(greeting_text)
        print_to_console(f'"{greeting_text}"', "AI:")
        
        # Let the LLM handle all questions through function calls
        # Don't automatically queue the first question to prevent conflicts
        
        # Add a small delay and then trigger the LLM to ask the first question
        await asyncio.sleep(1.0)
        transcript_logger.info("READY: Triggering LLM to ask first question")
        # The LLM should now generate a response and call ask_question
        
        # Fallback: If no question is asked within 3 seconds, automatically queue the first question
        await asyncio.sleep(3.0)
        if self._question_number == 0 and self._question_queue.empty():
            transcript_logger.info("FALLBACK: LLM didn't ask first question, automatically queuing")
            await self._question_queue.put("Is it a living thing?")
            asyncio.create_task(self._process_question_queue())

    def _setup_logging_handlers(self):
        """Set up event handlers to log all TTS and STT activity"""
        
        # Log when agent starts speaking
        @self.session.on("agent_started_speaking")
        def on_agent_started_speaking(event):
            transcript_logger.info(f"TTS STARTED: Agent began speaking")
        
        # Log when agent stops speaking
        @self.session.on("agent_stopped_speaking")
        def on_agent_stopped_speaking(event):
            transcript_logger.info(f"TTS STOPPED: Agent finished speaking")
        
        # Log speech creation
        @self.session.on("speech_created")
        def on_speech_created(event):
            speech_id = getattr(event, 'speech_handle', None)
            if speech_id:
                speech_id = getattr(speech_id, 'id', 'unknown')
            else:
                speech_id = 'unknown'
            transcript_logger.info(f"TTS CREATED: Speech created with ID {speech_id}")
        
        # Log user input transcription
        @self.session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            transcript = getattr(event, 'transcript', 'unknown')
            is_final = getattr(event, 'is_final', False)
            transcript_logger.info(f"STT RECEIVED: '{transcript}' (final: {is_final})")
            
            # Print user text to console when final
            if is_final and transcript and transcript != 'unknown':
                print_to_console(f'"{transcript}"', "USER:")
        
        # Log when user starts speaking
        @self.session.on("user_started_speaking")
        def on_user_started_speaking(event):
            transcript_logger.info(f"STT STARTED: User began speaking")
        
        # Log when user stops speaking
        @self.session.on("user_stopped_speaking")
        def on_user_stopped_speaking(event):
            transcript_logger.info(f"STT STOPPED: User finished speaking")

    async def _log_tts_output(self, text: str):
        """Log TTS output with timestamp and print to console"""
        transcript_logger.info(f"TTS OUTPUT: '{text}'")
        print_to_console(f'"{text}"', "AI:")

    async def _log_stt_input(self, text: str):
        """Log STT input with timestamp"""
        transcript_logger.info(f"STT INPUT: '{text}'")

    async def _process_question_queue(self):
        """Process questions from the queue one at a time"""
        if self._processing_question:
            logger.info("Skipping queue processing - already processing a question")
            return  # Don't process more questions if one is already being processed
            
        while not self._question_queue.empty() and self._game_active:
            question = await self._question_queue.get()
            transcript_logger.info(f"PROCESSING: {question}")
            
            async with self._question_lock:
                if self._question_number >= self._max_questions:
                    logger.info("Maximum questions reached")
                    return
                
                if self._waiting_for_response:
                    logger.info(f"Rejected question '{question}' - still waiting for response to '{self._current_question}'")
                    transcript_logger.info(f"REJECTED: {question} (waiting for: {self._current_question})")
                    # Put the question back in the queue
                    await self._question_queue.put(question)
                    return
                
                self._processing_question = True
                self._question_number += 1
                self._waiting_for_response = True
                self._current_question = question
                self._response_received.clear()
                
                logger.info(f"Question {self._question_number}: {question}")
                transcript_logger.info(f"AGENT: Question {self._question_number}: {question}")
                
                # Generate random timeout between 5-15 seconds
                timeout_seconds = random.uniform(5.0, 15.0)
                
                # Ask the question with timeout announcement
                question_text = f"Question {self._question_number}: {question}? You have {timeout_seconds:.1f} seconds to answer."
                await self._log_tts_output(question_text)
                await self.session.say(question_text)
                
                # Wait for response with timeout
                try:
                    await asyncio.wait_for(self._response_received.wait(), timeout=timeout_seconds)
                    logger.info(f"User responded to question: '{question}'")
                    transcript_logger.info(f"RESPONSE: User answered question {self._question_number}")
                    
                    # Don't restate the user's response - let the LLM handle it
                    # This prevents duplication with LLM-generated responses
                    
                except asyncio.TimeoutError:
                    logger.info(f"Timeout reached for question: '{question}' after {timeout_seconds:.1f}s")
                    transcript_logger.info(f"TIMEOUT: Question {self._question_number} timed out after {timeout_seconds:.1f}s")
                    timeout_text = f"You did not answer in time. Let me ask a different question."
                    await self._log_tts_output(timeout_text)
                    await self.session.say(timeout_text)
                    
                    # Don't count timeout as a question - decrement the question number
                    self._question_number -= 1
                    transcript_logger.info(f"TIMEOUT: Decremented question number back to {self._question_number}")
                    
                    # Don't put the question back in the queue - let the LLM ask a different question
                    # The LLM will generate a response and call ask_question with a new question

                finally:
                    self._waiting_for_response = False
                    self._current_question = None
                    self._processing_question = False
                    self._question_just_queued = False
                    
                    # Continue processing the queue if there are more questions
                    if not self._question_queue.empty():
                        asyncio.create_task(self._process_question_queue())
                    else:
                        # If no more questions in queue, allow LLM to generate response
                        # This will let the LLM acknowledge the answer and ask the next question
                        logger.info("Question processing complete - allowing LLM response")
                        transcript_logger.info("READY: Allowing LLM to generate next question")

    @function_tool
    async def make_guess(
        self,
        context: RunContext,
        guess: str
    ) -> str:
        """
        Make a guess about what the user is thinking of.
        
        Args:
            guess: Your guess about what the user is thinking of
        """
        guess_text = f"I think you're thinking of: {guess}. Am I correct?"
        await self._log_tts_output(guess_text)
        await self.session.say(guess_text)
        transcript_logger.info(f"AGENT: Making guess: {guess}")
        
        # Wait for confirmation
        timeout_seconds = random.uniform(5.0, 15.0)
        self._waiting_for_response = True
        self._response_received.clear()
        
        try:
            await asyncio.wait_for(self._response_received.wait(), timeout=timeout_seconds)
            transcript_logger.info(f"RESPONSE: User responded to guess")
            return f"Guess made: {guess}"
        except asyncio.TimeoutError:
            transcript_logger.info(f"TIMEOUT: Guess confirmation timed out")
            timeout_text = "I didn't hear a response. Let me continue asking questions."
            await self._log_tts_output(timeout_text)
            await self.session.say(timeout_text)
            return "Timeout on guess confirmation - continuing with questions"
        finally:
            self._waiting_for_response = False

    @function_tool
    async def make_final_guess(
        self,
        context: RunContext,
        final_guess: str
    ) -> str:
        """
        Make a final guess when out of questions.
        
        Args:
            final_guess: Your final guess about what the user is thinking of
        """
        final_guess_text = f"I'm out of questions! My final guess is: {final_guess}. Am I correct?"
        await self._log_tts_output(final_guess_text)
        await self.session.say(final_guess_text)
        transcript_logger.info(f"AGENT: Final guess: {final_guess}")
        
        timeout_seconds = random.uniform(5.0, 15.0)
        self._waiting_for_response = True
        self._response_received.clear()
        
        try:
            await asyncio.wait_for(self._response_received.wait(), timeout=timeout_seconds)
            transcript_logger.info(f"RESPONSE: User responded to final guess")
            return f"Final guess made: {final_guess}"
        except asyncio.TimeoutError:
            transcript_logger.info(f"TIMEOUT: Final guess confirmation timed out")
            timeout_text = "I didn't hear a response. The game is over!"
            await self._log_tts_output(timeout_text)
            await self.session.say(timeout_text)
            return "Game ended with timeout on final guess"
        finally:
            self._waiting_for_response = False

    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Called when user completes speaking - signal response received"""
        self._last_user_response = new_message.text_content
        logger.info(f"User spoke: {new_message.text_content}")
        await self._log_stt_input(new_message.text_content)
        transcript_logger.info(f"USER: {new_message.text_content}")
        
        # Signal that we received a response if we're waiting for one
        if self._waiting_for_response:
            logger.info(f"Setting response event for current question: '{self._current_question}'")
            self._response_received.set()
            
            # Don't automatically process the queue here - let the LLM handle it
            # The LLM will call ask_question when ready for the next question
        
        # Fallback: If no questions are queued and we're not waiting for a response,
        # and this isn't the first interaction, queue a follow-up question
        elif (not self._question_queue.empty() or self._question_number == 0) and not self._waiting_for_response:
            # Only do this if we have some conversation history (not the very first interaction)
            if self._question_number > 0:
                logger.info("Fallback: No questions queued, triggering LLM to ask next question")
                transcript_logger.info("FALLBACK: Triggering LLM to ask next question")
                # This will trigger the LLM to generate a response and potentially call ask_question

    async def on_conversation_turn_completed(self, turn_ctx, new_message):
        """Called when agent completes speaking - process queued questions"""
        if not self._game_active:
            return
            
        # Don't automatically process the queue - let the LLM handle it through function calls
        # This prevents conflicts between automatic processing and LLM-driven processing

    async def on_llm_response_started(self, turn_ctx):
        """Called when LLM starts generating a response - prevent if waiting for response"""
        if self._waiting_for_response:
            logger.info("Preventing LLM response - waiting for user response")
            transcript_logger.info("BLOCKED: LLM response prevented - waiting for user")
            # Cancel the response generation
            return False
        
        # Prevent LLM responses when we have queued questions to process
        if not self._question_queue.empty() and not self._processing_question:
            logger.info("Preventing LLM response - have queued questions to process")
            transcript_logger.info("BLOCKED: LLM response prevented - processing queued questions")
            return False
        
        # Prevent LLM responses when currently processing a question
        if self._processing_question:
            logger.info("Preventing LLM response - currently processing a question")
            transcript_logger.info("BLOCKED: LLM response prevented - processing question")
            return False
        
        # Prevent LLM responses when a question was just queued (to avoid duplicate speech)
        if hasattr(self, '_question_just_queued') and self._question_just_queued:
            logger.info("Preventing LLM response - question just queued, avoiding duplicate speech")
            transcript_logger.info("BLOCKED: LLM response prevented - question just queued")
            self._question_just_queued = False
            return False
            
        return True

    async def on_llm_response_completed(self, turn_ctx, response):
        """Called when LLM completes generating a response - log for debugging"""
        if hasattr(response, 'content') and response.content:
            transcript_logger.info(f"LLM RESPONSE: {response.content}")
        return True

    @function_tool
    async def dump_session_history(
        self,
        context: RunContext
    ) -> str:
        """
        Dump the current session history to a file for debugging purposes.
        """
        try:
            # Get current timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = debug_dir / f"session_history_{timestamp}.txt"
            
            # Write session information to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Session History Dump - {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                
                # Log session object information
                f.write(f"Session object type: {type(self.session)}\n")
                f.write(f"Session attributes: {[attr for attr in dir(self.session) if not attr.startswith('_')]}\n\n")
                
                # Try to get conversation history from different sources
                f.write("Attempting to access conversation history:\n")
                f.write("-" * 30 + "\n")
                
                # Try different approaches to get history
                history_sources = [
                    ('session.history', lambda: getattr(self.session, 'history', None)),
                    ('session._history', lambda: getattr(self.session, '_history', None)),
                    ('session.conversation_history', lambda: getattr(self.session, 'conversation_history', None)),
                    ('session.messages', lambda: getattr(self.session, 'messages', None)),
                    ('session.chat_history', lambda: getattr(self.session, 'chat_history', None)),
                ]
                
                for source_name, getter_func in history_sources:
                    try:
                        history = getter_func()
                        if history is not None:
                            f.write(f"✓ Found {source_name}: {type(history)}\n")
                            if hasattr(history, '__len__'):
                                try:
                                    f.write(f"  Length: {len(history)}\n")
                                    # Try to iterate if it's iterable
                                    if hasattr(history, '__iter__'):
                                        for i, entry in enumerate(history[:5]):  # Only show first 5 entries
                                            f.write(f"  Entry {i}: {type(entry)} - {str(entry)[:100]}...\n")
                                        if len(history) > 5:
                                            f.write(f"  ... and {len(history) - 5} more entries\n")
                                except Exception as e:
                                    f.write(f"  Error getting length: {e}\n")
                            else:
                                f.write(f"  Content: {str(history)[:200]}...\n")
                        else:
                            f.write(f"✗ {source_name}: Not found\n")
                    except Exception as e:
                        f.write(f"✗ {source_name}: Error - {e}\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("End of session dump\n")
            
            transcript_logger.info(f"Session history dumped to {filename}")
            return f"Session history successfully dumped to {filename}"
            
        except Exception as e:
            error_msg = f"Failed to dump session history: {str(e)}"
            transcript_logger.error(error_msg)
            return error_msg

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()
    agent = TwentyQuestionsAgent()

    await session.start(
        agent=agent,
        room=ctx.room
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint)) 