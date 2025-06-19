import asyncio
import logging
import os
import random
from pathlib import Path
from dotenv import load_dotenv
from typing import Annotated, Optional, Tuple
from pydantic import Field
from PIL import Image
import numpy as np

# Suppress PIL debug messages
logging.getLogger('PIL').setLevel(logging.WARNING)

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero, deepgram
from livekit.agents.llm import function_tool

from browser_manager import BrowserState
from agent_camera import AgentCamera

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self, room: rtc.Room, voice: str) -> None:
        self.browser_state = BrowserState()
        self.room = room
        self.participant_names = {}
        self._update_participant_names()
        
        # Create greeting
        greeting = "Hello!"
        if self.participant_names:
            names = list(self.participant_names.values())
            greeting = f"Hello {', '.join(names)}!"

        super().__init__(
            instructions=f"""
                {greeting} I am a helpful agent that can control a web browser. When you speak, I listen and respond.
                I can perform various browser actions when requested. Here are the available commands:

                Browser Control:
                - "open browser" or "show browser": Opens a browser window
                - "close browser" or "hide browser": Closes the browser window
                - "go to [website]": Navigates to a specific website
                - "go back": Navigates back in browser history
                - "go forward": Navigates forward in browser history
                - "reload": Reloads the current page

                Tab Management:
                - "list tabs": Shows all open browser tabs with their titles and URLs
                - "switch to tab [number]": Switches to a specific tab by number
                - "new tab [url]": Creates a new tab, optionally navigating to a URL
                - "close tab [number]": Closes a specific tab by number

                Quick Actions:
                - "open LiveKit Help": Opens browser to LiveKit documentation for easy testing

                Scrolling:
                - "scroll down [pixels]": Scrolls down by specified pixels (default 100)
                - "scroll up [pixels]": Scrolls up by specified pixels (default 100)
                - "start auto-scroll [direction] [speed]": Starts auto-scrolling (direction: up/down, speed: 0.2-3.0)
                - "stop auto-scroll": Stops auto-scrolling

                Interaction:
                - "click at [x] [y]": Clicks at specific coordinates
                - "click [text]": Clicks an element with matching text
                - "fill [selector] [value]": Fills an input field
                - "select [selector] [value]": Selects an option from a dropdown
                - "list inputs": Lists all input fields on the page
                - "press enter": Presses the Enter key

                Content Reading:
                - "read page": Gets the page content as markdown
                - "get title": Gets the page title
                - "scroll to [text]": Scrolls to a section containing the text

                When you ask me to perform any of these actions:
                1. I will use the appropriate tool function
                2. Wait for the tool response
                3. Acknowledge the action and its result in my response
                4. If the action failed, I will explain what went wrong and suggest alternatives

                Always check if the browser is open before attempting any actions.
                If the browser is not open, I will ask you to open it first.

                If an action fails due to a browser crash:
                1. I will inform you that the browser needs to be reopened
                2. Suggest reopening the browser
                3. Wait for your confirmation before proceeding

                IMPORTANT: I will always respond to tool calls with a simple string message.
                I will not include any special formatting or markdown in tool responses.
                I will keep tool responses concise and clear.

                When responding to users, I will use their name if I know it.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(voice=voice),
            vad=silero.VAD.load()
        )


    async def _send_message(self, message: str):
        await self.room.local_participant.send_text(text=message, topic="lk.chat")

    def _update_participant_names(self):
        """Update the cached participant names."""
        for identity, participant in self.room.remote_participants.items():
            logger.info(f"Participant name: {participant.name}")
            logger.info(f"Participant kind: {participant.kind}")
            
            self.participant_names[identity] = participant.name

    def get_participant_name(self, identity: str) -> str:
        """Get the name of a participant by their identity."""
        return self.participant_names.get(identity, "you")

    async def on_enter(self):
        self._update_participant_names()
        await self._send_message("Hello! I'm a browsing agent. Would you like me to open my browser?")
        self.session.generate_reply()

    async def on_participant_joined(self, participant: rtc.RemoteParticipant):
        """Handle new participants joining."""
        self._update_participant_names()
        name = self.get_participant_name(participant.identity)
        await self.session.generate_reply(f"Welcome {name}!")

    async def on_participant_left(self, participant: rtc.RemoteParticipant):
        """Handle participants leaving."""
        self._update_participant_names()
        name = self.get_participant_name(participant.identity)
        await self.session.generate_reply(f"Goodbye {name}!")

    @function_tool()
    async def open_browser(self) -> str:
        """Opens a browser window and starts screen sharing."""
        if not self.browser_state.is_open:
            try:
                success = await self.browser_state.open_browser(self.room)
                if success:
                    return "Browser opened successfully."
                return "Failed to open browser."
            except Exception as e:
                logger.error(f"Error opening browser: {e}")
                return "Failed to open browser."
        return "Browser is already open."

    @function_tool()
    async def close_browser(self) -> str:
        """Closes the browser window and stops screen sharing."""
        if self.browser_state.is_open:
            try:
                success = await self.browser_state.close_browser(self.room)
                if success:
                    return "Browser closed successfully."
                return "Failed to close browser."
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
                return "Failed to close browser."
        return "Browser is already closed."

    @function_tool()
    async def navigate_to(self, url: Annotated[str, Field(description="The URL to navigate to")]) -> str:
        """Navigates to a specific website in the browser."""
        return await self.browser_state.perform_action("navigate_to", url=url)

    @function_tool()
    async def go_back(self) -> str:
        """Goes back in browser history."""
        return await self.browser_state.perform_action("go_back")

    @function_tool()
    async def go_forward(self) -> str:
        """Goes forward in browser history."""
        return await self.browser_state.perform_action("go_forward")

    @function_tool()
    async def reload_page(self) -> str:
        """Reloads the current page."""
        return await self.browser_state.perform_action("reload")

    @function_tool()
    async def scroll_down(self, pixels: int) -> str:
        """Scrolls down by the specified number of pixels."""
        return await self.browser_state.perform_action("scroll_down", pixels=pixels)

    @function_tool()
    async def scroll_up(self, pixels: int) -> str:
        """Scrolls up by the specified number of pixels."""
        return await self.browser_state.perform_action("scroll_up", pixels=pixels)

    @function_tool()
    async def start_auto_scroll(self, direction: str, speed: float) -> str:
        """Starts auto-scrolling in the specified direction at the given speed."""
        result = await self.browser_state.perform_action("start_auto_scroll", direction=direction, speed=speed)
        if result == "done":
            return f"Started auto-scrolling {direction} at {speed}x speed."
        elif result.startswith("I've reached"):
            return result
        return "Failed to start auto-scrolling."

    @function_tool()
    async def stop_auto_scroll(self) -> str:
        """Stops auto-scrolling."""
        return await self.browser_state.perform_action("stop_auto_scroll")

    @function_tool()
    async def click_at(self, x: Annotated[int, Field(description="X coordinate")], 
                      y: Annotated[int, Field(description="Y coordinate")]) -> str:
        """Clicks at the specified coordinates."""
        result = await self.browser_state.perform_action("click_at", x=x, y=y)
        await self._check_new_tab_notifications()
        return result

    @function_tool()
    async def click_by_text(self, text: Annotated[str, Field(description="Text content of the element to click")]) -> str:
        """Clicks an element with the specified text content."""
        result = await self.browser_state.perform_action("click_by_text", text=text)
        await self._check_new_tab_notifications()
        return result

    @function_tool()
    async def fill_input(self, selector: Annotated[str, Field(description="CSS selector for the input field")], 
                        value: Annotated[str, Field(description="Value to fill in the input field")]) -> str:
        """Fills an input field with the specified value."""
        return await self.browser_state.perform_action("fill_input", selector=selector, value=value)

    @function_tool()
    async def select_option(self, selector: Annotated[str, Field(description="CSS selector for the select element")], 
                           value: Annotated[str, Field(description="Value to select")]) -> str:
        """Selects an option from a dropdown."""
        return await self.browser_state.perform_action("select_option", selector=selector, value=value)

    @function_tool()
    async def list_input_fields(self) -> str:
        """Lists all input fields on the current page."""
        return await self.browser_state.perform_action("list_input_fields")

    @function_tool()
    async def read_page_content(self) -> str:
        """Gets the page content as formatted markdown."""
        return await self.browser_state.perform_action("read_page_content")

    @function_tool()
    async def get_page_title(self) -> str:
        """Gets the current page title."""
        return await self.browser_state.perform_action("get_page_title")

    @function_tool()
    async def scroll_to_section(self, text: Annotated[str, Field(description="Text content to scroll to")]) -> str:
        """Scrolls to a section containing the specified text."""
        return await self.browser_state.perform_action("scroll_to_section", text=text)

    @function_tool()
    async def press_enter(self) -> str:
        """Presses the Enter key."""
        result = await self.browser_state.perform_action("press_enter")
        await self._check_new_tab_notifications()
        return result

    @function_tool()
    async def list_tabs(self) -> str:
        """List all open browser tabs with their titles and URLs."""
        return await self.browser_state.list_tabs()

    @function_tool()
    async def switch_tab(self, tab_number: Annotated[int, Field(description="Tab number to switch to (1-based index)")]) -> str:
        """Switch to a specific tab by number (1-based index)."""
        return await self.browser_state.switch_tab(tab_number)

    @function_tool()
    async def new_tab(self, url: Annotated[Optional[str], Field(description="Optional URL to navigate to in the new tab")] = None) -> str:
        """Create a new browser tab, optionally navigating to a URL."""
        return await self.browser_state.new_tab(url)

    @function_tool()
    async def close_tab(self, tab_number: Annotated[int, Field(description="Tab number to close (1-based index)")]) -> str:
        """Close a specific tab by number (1-based index)."""
        return await self.browser_state.close_tab(tab_number)

    @function_tool()
    async def open_livekit_help(self) -> str:
        """Opens the browser to the LiveKit Help documentation for easy testing."""
        if not self.browser_state.is_open:
            success = await self.browser_state.open_browser(self.room)
            if not success:
                return "Failed to open browser."
        
        return await self.browser_state.perform_action("navigate_to", url="https://deepwiki.com/livekit/livekit_composite")

    async def _check_new_tab_notifications(self):
        """Checks for and handles new tab notifications."""
        if self.browser_state.is_open:
            notification = await self.browser_state.check_new_tab_notification()
            if notification:
                await self._send_message(notification)
                return True
        return False

    @function_tool()
    async def send_message(self, message: Annotated[str, Field(description="The message to send to the user")]) -> str:
        """Sends a message to the user in the chat."""
        await self._send_message(message)
        return "Message sent successfully."

    @function_tool()
    async def respond_as_text(self, message: Annotated[str, Field(description="The message to send as a text response")]) -> str:
        """Responds to the user with a text message instead of voice."""
        await self._send_message(message)
        return "Responded with text message."

    @function_tool()
    async def help(self) -> str:
        """Provides help information about available actions."""
        help_message = """Here are the types of actions you can ask me to perform:

Browser Control:
- "open browser" or "show browser": Opens a browser window
- "close browser" or "hide browser": Closes the browser window
- "go to [website]": Navigates to a specific website
- "go back": Navigates back in browser history
- "go forward": Navigates forward in browser history
- "reload": Reloads the current page

Tab Management:
- "list tabs": Shows all open browser tabs with their titles and URLs
- "switch to tab [number]": Switches to a specific tab by number
- "new tab [url]": Creates a new tab, optionally navigating to a URL
- "close tab [number]": Closes a specific tab by number

Quick Actions:
- "open LiveKit Help": Opens browser to LiveKit documentation for easy testing

Scrolling:
- "scroll down [pixels]": Scrolls down by specified pixels (e.g., "scroll down 200")
- "scroll up [pixels]": Scrolls up by specified pixels (e.g., "scroll up 200")
- "start auto-scroll [direction] [speed]": Starts auto-scrolling (e.g., "start auto-scroll down 1.5")
- "stop auto-scroll": Stops auto-scrolling

Interaction:
- "click at [x] [y]": Clicks at specific coordinates
- "click [text]": Clicks an element with matching text
- "fill [selector] [value]": Fills an input field
- "select [selector] [value]": Selects an option from a dropdown
- "list inputs": Lists all input fields on the page
- "press enter": Presses the Enter key

Content Reading:
- "read page": Gets the page content as markdown
- "get title": Gets the page title
- "scroll to [text]": Scrolls to a section containing the text

Communication:
- "send that as text" or "respond as text": Sends my response as a text message
- "send message [text]": Sends a specific text message to you

Remember to open the browser first before trying any other actions!"""
        await self._send_message(help_message)
        return "Sent help information as text message."

class JobState:
    def __init__(self, room: rtc.Room):
        self.room = room
        
        # Randomly select agent configuration
        self.agent_config = self._select_agent_config()
        
        # Initialize agent with selected voice
        self.agent = SimpleAgent(room, self.agent_config[1])
        self.session = AgentSession()
        
        # Initialize agent camera
        image_path = Path(__file__).parent / "res" / self.agent_config[0]
        self.agent_camera = AgentCamera(str(image_path))
        
        self._cleanup_handlers = []

    def _select_agent_config(self) -> Tuple[str, str]:
        """Randomly select between female/sage and male/ash configurations."""
        configs = [
            ("agent_female.png", "sage"),
            ("agent_male.png", "ash")
        ]
        return random.choice(configs)

    async def start(self):
        # Start agent session
        await self.session.start(
            agent=self.agent,
            room=self.room
        )

        # Start agent camera
        await self.agent_camera.start(self.room)
        
        # Register cleanup handler
        self._cleanup_handlers.append(self._cleanup_multiprocessing)

    async def stop(self):
        # Stop agent camera
        await self.agent_camera.stop(self.room)

        # Close browser if open
        if self.agent.browser_state.is_open:
            await self.agent.browser_state.close_browser(self.room)
            
        # Run cleanup handlers
        for handler in self._cleanup_handlers:
            try:
                await handler()
            except Exception as e:
                logger.error(f"Error in cleanup handler: {e}")

    async def _cleanup_multiprocessing(self):
        """Clean up any lingering multiprocessing resources."""
        import multiprocessing
        for process in multiprocessing.active_children():
            try:
                process.terminate()
                process.join(timeout=1)
            except Exception as e:
                logger.error(f"Error cleaning up process {process.pid}: {e}")

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    
    # Create job state
    job_state = JobState(ctx.room)
    
    try:
        # Start the job
        await job_state.start()
        
        # Keep the job running
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        # Clean up when job is cancelled
        await job_state.stop()
    except Exception as e:
        logger.error(f"Error in job: {e}")
        await job_state.stop()
        raise

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
