# LiveKit Agent with Mem0 Integration

This project implements a voice-enabled toy travel planning assistant using [LiveKit](https://livekit.io/) and [Mem0](https://app.mem0.ai/) for memory management. The agent, named George, helps users plan various types of trips while maintaining context from previous conversations.

## Prerequisites

- Python 3.10 or higher
- Mem0 API key
- OpenAI API key (for GPT-4 and TTS)
- Deepgram API key (for speech-to-text)
- Environment variables set up (see Configuration section)

## Installation

1. Clone this repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # download models
   pip mem0_agent.py download-files
   ```

## Configuration

Create a `.env` file in the project root with the following variables, or export them in your environment:

```env
MEM0_API_KEY=your_mem0_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
LIVEKIT_URL=your_livekit_server_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

## Running the Agent

1. Ensure all environment variables are set
2. Run the agent:
   ```bash
   python mem0_agent.py dev
   ```

The agent will:
- Connect to your LiveKit server
- Wait for a participant to join
- Initialize the voice assistant with:
  - GPT-4 for conversation
  - Deepgram for speech-to-text
  - OpenAI TTS for text-to-speech
  - Mem0 for memory management
  - Silero for voice activity detection

## Features

- Voice-enabled travel planning assistant
- Persistent memory using Mem0
- Real-time speech processing
- Multi-language support
- Context-aware responses
- Memory management capabilities:
  - Store important travel information
  - Recall previous conversations
  - Clear memories when needed

## Memory Management

The agent can:
- Store important travel preferences and plans
- Recall previous conversations
- Clear all memories when requested
- Automatically enrich conversations with relevant past information

## Troubleshooting

If you encounter issues:
1. Verify all API keys are correctly set in the `.env` file
2. Check your LiveKit server connection
3. Ensure all required Python packages are installed
4. Check the logs for detailed error messages

