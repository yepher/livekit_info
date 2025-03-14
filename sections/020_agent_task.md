# LiveKit Agent Documentation

## Overview
The `Agent` class is a core component of the LiveKit Voice Agent framework, designed to create conversational AI agents that can handle voice interactions. It provides a structured way to define agent behavior, process audio input, generate responses, and manage conversation flow.

You can chain multiple `Agent` together to form a flow of AI logic.

## Key Components
1. **Initialization Parameters**
   - `instructions`: System prompt defining agent personality/behavior
   - `chat_ctx`: Chat context management
   - `function_tools`: List of available AI functions
   - Speech Processing:
     - `stt`: Speech-to-Text engine
     - `tts`: Text-to-Speech engine
     - `vad`: Voice Activity Detection *(required for non streaming STT)*
   - `llm`: Language Model for response generation
   - `turn_detector`: End-of-turn detection

2. **Core Methods**
   - `on_enter()`: Called when task becomes active
   - `on_exit()`: Called when task is exited
   - `on_end_of_turn()`: Handles user speech completion
   - Processing nodes (`stt_node`, `llm_node`, `transcription_node`, `tts_node`)

## Usage Example

```python
from livekit.agents.voice import Agent
from livekit.plugins import deepgram, openai, cartesia

class CustomerSupportTask(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful customer support agent...",
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        # Initialize task-specific resources
        print("on_enter")
        
    async def on_exit(self):
        # Called when the task is exited
        print("on_exit")

    async def on_end_of_turn(self, chat_ctx, new_message):
        # Add custom processing before LLM response
        #
        # This is a good opportunity to update the chat 
        # context or edit the new message before it is sent 
        # to the LLM.
        print("on_end_of_turn: " + new_message)

    @llm.function_tool
    async def transfer_to_human(self, context):
        # Custom AI function for transfers
        return HumanAgent(), "Transferring to human agent"
```

## Workflow
1. **Initialization**
   - Configure speech processing components (STT, TTS, VAD)
   - Set up LLM with instructions and AI functions
   - Define conversation context and turn detection

2. **Lifecycle Hooks**
   - `on_enter`: Setup event listeners/initial state
   - `on_exit`: Cleanup resources
   - `on_end_of_turn`: Modify messages before LLM processing

3. **Processing Pipeline**
   ```mermaid
   graph TD
     A[Audio Input] --> B(STT Node)
     B --> C(LLM Node)
     C --> D(Transcription Node)
     D --> E(TTS Node)
     E --> F[Audio Output]
   ```

4. **AI Functions**
   - Annotate methods with `@llm.function_tool`
   - Enable natural language triggering of backend logic
   - Handle context-aware operations like transfers

## Key Features
- **Modular Architecture**: Swap STT/TTS/LLM providers
- **Conversation Management**: Built-in turn detection and context tracking
- **Custom Hooks**: Override methods for task-specific logic
- **Error Handling**: Built-in exception management
- **Async Support**: Full async/await compatibility

## Conclusion
The Agent framework provides a powerful abstraction for building voice-enabled AI agents. By implementing the provided hooks and leveraging the processing pipeline, developers can create sophisticated conversation flows while maintaining clean separation between components.
