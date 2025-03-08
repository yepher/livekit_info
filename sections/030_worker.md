## Worker Class

[source](https://github.com/livekit/agents/blob/dev-1.0/livekit-agents/livekit/agents/worker.py)

Handles deployment and management of VoiceAgent instances across multiple LiveKit rooms.

### Initialization

```python
def __init__(
    self,
    *,
    agent_factory: Callable[[rtc.Room], VoiceAgent | Awaitable[VoiceAgent]],
    livekit_url: str,
    api_key: str,
    api_secret: str,
    room_manager: Optional[RoomManager] = None,
    worker_id: str = "voice-agent-worker",
    max_connections: int = 100,
    reconnect_timeout: float = 3.0,
    **kwargs,
) -> None
```

**Key Parameters:**
- `agent_factory`: Creates [VoiceAgent](#voiceagent-class) instances per room
- `livekit_url`: LiveKit server URL (e.g.: wss://your-domain.livekit.cloud)
- `api_key/secret`: LiveKit API credentials
- `max_connections`: Maximum concurrent room connections
- `reconnect_timeout`: Delay before reconnecting failed connections

### Key Methods

#### `start()`
```python
async def start(self) -> None
```
Connects to LiveKit server and starts processing room connections.

#### `aclose()`
```python
async def aclose(self) -> None
```
Gracefully shuts down all active connections and agents.

### Events

- `agent_created`: Emitted when a new agent is created
  ```python
  class AgentCreatedEvent:
      room: rtc.Room
      agent: VoiceAgent
  ```

### Usage Example

```python
async def agent_factory(room: rtc.Room) -> VoiceAgent:
    agent = VoiceAgent(
        instructions="You're a conference assistant",
        stt=DeepgramSTT(),
        llm=OpenAILlm(),
        tts=ElevenLabsTTS()
    )
    # Customize agent per room
    agent.userdata = {"room_name": room.name}
    return agent

worker = Worker(
    agent_factory=agent_factory,
    livekit_url="wss://your.livekit.server",
    api_key="your-key",
    api_secret="your-secret"
)

async def main():
    await worker.start()
    # Run until interrupted
    while True:
        await asyncio.sleep(1)
```

### Worker Management Tips

1. Use agent_factory to customize agents per room/participant
2. Handle rate limits in agent factory for large deployments
3. Use room metadata to configure agent behavior
4. Implement health checks for long-running workers
5. Handle SIGTERM/SIGINT for graceful shutdowns

