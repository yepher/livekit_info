# New Classes in LiveKit Agents v1.0

This document describes the new classes introduced in LiveKit Agents v1.0.

## Core Classes

### AgentMetrics
A class for tracking and collecting metrics about agent performance and behavior.

### AgentState
An enum or class representing the current state of an agent (e.g., idle, running, error).

### BaseModel
A Pydantic base model class used for data validation and serialization.

### DEFAULT_API_CONNECT_OPTIONS
Default configuration options for API connections.

### NOT_GIVEN
A sentinel value used to indicate that a parameter was not provided.

### Room
A class representing a LiveKit room, providing methods for room management and participant interaction.

### TTS
A class for text-to-speech functionality.

### WorkerInfo
A class containing information about a worker, including its HTTP port and other metadata.

## Content Types

### AudioContent
```python
class AudioContent(BaseModel):
    type: Literal["audio_content"] = Field(default="audio_content")
    frame: list[rtc.AudioFrame]
    transcript: str | None = None
```
Represents audio content in the chat context, including the audio frames and optional transcript.

### ImageContent
```python
class ImageContent(BaseModel):
    type: Literal["image_content"] = Field(default="image_content")
    url: str
    detail: Literal["auto", "low", "high"] = "auto"
```
Represents image content in the chat context, including the image URL and detail level.

## Function and Tool Related

### FunctionCall
```python
class FunctionCall(BaseModel):
    id: str = Field(default_factory=lambda: utils.shortuuid("item_"))
    type: Literal["function_call"] = "function_call"
    call_id: str
    arguments: str
    name: str
```
Represents a function call in the chat context.

### FunctionCallOutput
```python
class FunctionCallOutput(BaseModel):
    id: str = Field(default_factory=lambda: utils.shortuuid("item_"))
    type: Literal["function_call_output"] = "function_call_output"
    call_id: str
    output: str | dict
```
Represents the output of a function call.

### FunctionTool
A class representing a function that can be called by the LLM.

### FunctionToolCall
A class representing an actual call to a function tool.

### ToolContext
```python
class ToolContext:
    """Stateless container for a set of AI functions"""
    
    def __init__(self, tools: list[FunctionTool]) -> None:
        self.update_tools(tools)
    
    @classmethod
    def empty(cls) -> ToolContext:
        return cls([])
    
    @property
    def function_tools(self) -> dict[str, FunctionTool]:
        return self._tools_map.copy()
    
    def update_tools(self, tools: list[FunctionTool]) -> None:
        self._tools = tools
        for method in find_function_tools(self):
            tools.append(method)
        self._tools_map = {}
        for tool in tools:
            info = get_function_info(tool)
            if info.name in self._tools_map:
                raise ValueError(f"duplicate function name: {info.name}")
            self._tools_map[info.name] = tool
    
    def copy(self) -> ToolContext:
        return ToolContext(self._tools.copy())
```
A container for managing AI function tools.

## Metrics and Monitoring

### EOUMetrics
A class for tracking end-of-turn metrics.

### IPC_MESSAGES
Constants or enums for IPC (Inter-Process Communication) message types.

### JobExecutorType
An enum or class defining types of job executors.

### SimulateJobArgs
```python
@dataclass
class SimulateJobArgs:
    room: str = ""
    participant_identity: str = ""
```
Arguments for simulating a job.

### TracingRequest
A class for making tracing requests to gather debugging information.

### TracingResponse
A class containing tracing response data for debugging and monitoring. 