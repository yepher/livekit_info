# LiveKit Browsing Agent

A voice-controlled web browsing agent that can navigate, interact with, and read web pages.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
python main.py download-files
```

2. Set up your environment variables in `.env`:
```bash
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=your_openai_api_key
```

## Available Commands

The agent can perform the following actions through voice commands:

### Browser Control
- "open browser" or "show browser": Opens a browser window
- "close browser" or "hide browser": Closes the browser window
- "go to [website]": Navigates to a specific website
- "go back": Navigates back in browser history
- "go forward": Navigates forward in browser history
- "reload": Reloads the current page

### Scrolling
- "scroll down [pixels]": Scrolls down by specified pixels (e.g., "scroll down 200")
- "scroll up [pixels]": Scrolls up by specified pixels (e.g., "scroll up 200")
- "start auto-scroll [direction] [speed]": Starts auto-scrolling (e.g., "start auto-scroll down 1.5")
- "stop auto-scroll": Stops auto-scrolling

### Interaction
- "click at [x] [y]": Clicks at specific coordinates
- "click [text]": Clicks an element with matching text
- "fill [selector] [value]": Fills an input field
- "select [selector] [value]": Selects an option from a dropdown
- "list inputs": Lists all input fields on the page
- "press enter": Presses the Enter key

### Content Reading
- "read page": Gets the page content as markdown
- "get title": Gets the page title
- "scroll to [text]": Scrolls to a section containing the text

### Communication
- "send that as text" or "respond as text": Sends the agent's response as a text message in the chat
- "send message [text]": Sends a specific text message to the user

## Example Usage

1. Start the agent:
```bash
python main.py start
```

2. Join the LiveKit room and start giving voice commands:
- "Open browser"
- "Go to docs.livekit.io"
- "Scroll down 200"
- "Click Documentation"
- "Read page"
- "Send that as text"

## Notes

- The browser window is headless by default
- The agent will automatically share its screen in the LiveKit room
- All commands require the browser to be open first
- The agent will provide feedback on the success or failure of each action
- Auto-scroll will automatically stop when reaching the top or bottom of the page
- The agent can respond via voice or text messages in the chat

## Troubleshooting

If you encounter issues:
1. Make sure all dependencies are installed correctly
2. Verify your environment variables are set properly
3. Check that you have a stable internet connection
4. Ensure your OpenAI API key has sufficient credits


## TODO/Known Issues

* Large long pages (larger than context length) cause unrecoverable errors
    * TOFIX: Change read page to let agent view a range of the page content, prune context as needed. Maybe provide local cache that lets agent build RAG knowledge during session
* Needs a lot of improvements for navigations