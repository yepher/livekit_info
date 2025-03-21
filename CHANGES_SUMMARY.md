# LiveKit Agent Changes (v0.x to v1.0)

## Known Changes

### When to Migrate?
- If using deprecated or removed features (e.g., `VoicePipelineAgent`, `AssistantLLM`, `STTSegmentsForwarder`).
- To leverage improvements in plugin integrations and lifecycle events.
- During scheduled upgrades or new feature implementations.

### What's Changing?
Key structural and functional changes in Agent >=1.0 include:

- **Unified Agent Interface:**
    - `VoicePipelineAgent` and `MultimodalAgent` combined into `AgentSession`.
    - Removal of `AssistantLLM`; replaced by standard `AgentSession`.
- **Deprecated Components:**
    - `STTSegmentsForwarder` removed; functionality integrated elsewhere.
    - `livekit.agents.pipeline` renamed to `livekit.agents.voice`.
- **Agent Lifecycle Methods:**
    - Removal of `@agent.on`; event handling now through lifecycle hooks (`on_enter`, `on_exit`, `on_end_of_turn`).
- **Plugin Changes:**
    - Enhanced clarity and modularization for STT, TTS, and LLM plugins.

## File Changes

### Renamed Files

### Removed Files
- `livekit-agents/livekit/agents/llm/function_context.py`
- `livekit-agents/livekit/agents/multimodal/agent_playout.py`
- `livekit-agents/livekit/agents/multimodal/multimodal_agent.py`
- `livekit-agents/livekit/agents/pipeline/agent_output.py`
- `livekit-agents/livekit/agents/pipeline/agent_playout.py`
- `livekit-agents/livekit/agents/pipeline/human_input.py`
- `livekit-agents/livekit/agents/pipeline/log.py`
- `livekit-agents/livekit/agents/pipeline/pipeline_agent.py`
- `livekit-agents/livekit/agents/pipeline/plotter.py`
- `livekit-agents/livekit/agents/pipeline/speech_handle.py`
- `livekit-agents/livekit/agents/transcription/_utils.py`
- `livekit-agents/livekit/agents/transcription/stt_forwarder.py`
- `livekit-agents/livekit/agents/transcription/tts_forwarder.py`
- `livekit-agents/livekit/agents/utils/_message_change.py`
- `livekit-agents/setup.py`

### Added Files
- `livekit-agents/livekit/agents/debug/tracing.py`
- `livekit-agents/livekit/agents/ipc/mock_room.py`
- `livekit-agents/livekit/agents/llm/_strict.py`
- `livekit-agents/livekit/agents/llm/realtime.py`
- `livekit-agents/livekit/agents/llm/remote_chat_context.py`
- `livekit-agents/livekit/agents/llm/tool_context.py`
- `livekit-agents/livekit/agents/llm/utils.py`
- `livekit-agents/livekit/agents/utils/aio/utils.py`
- `livekit-agents/livekit/agents/utils/aio/wait_group.py`
- `livekit-agents/livekit/agents/voice/agent.py`
- `livekit-agents/livekit/agents/voice/agent_activity.py`
- `livekit-agents/livekit/agents/voice/agent_session.py`
- `livekit-agents/livekit/agents/voice/audio_recognition.py`
- `livekit-agents/livekit/agents/voice/avatar/_datastream_io.py`
- `livekit-agents/livekit/agents/voice/avatar/_queue_io.py`
- `livekit-agents/livekit/agents/voice/avatar/_runner.py`
- `livekit-agents/livekit/agents/voice/avatar/_types.py`
- `livekit-agents/livekit/agents/voice/chat_cli.py`
- `livekit-agents/livekit/agents/voice/events.py`
- `livekit-agents/livekit/agents/voice/generation.py`
- `livekit-agents/livekit/agents/voice/io.py`
- `livekit-agents/livekit/agents/voice/room_io/_input.py`
- `livekit-agents/livekit/agents/voice/room_io/_output.py`
- `livekit-agents/livekit/agents/voice/room_io/room_io.py`
- `livekit-agents/livekit/agents/voice/speech_handle.py`
- `livekit-agents/livekit/agents/voice/transcription/_utils.py`
- `livekit-agents/livekit/agents/voice/transcription/synchronizer.py`

### Modified Files
- `.github/update_versions.py`
- `livekit-agents/livekit/agents/_exceptions.py`
- `livekit-agents/livekit/agents/cli/cli.py`
- `livekit-agents/livekit/agents/cli/log.py`
- `livekit-agents/livekit/agents/cli/proto.py`
- `livekit-agents/livekit/agents/cli/watcher.py`
- `livekit-agents/livekit/agents/http_server.py`
- `livekit-agents/livekit/agents/inference_runner.py`
- `livekit-agents/livekit/agents/ipc/channel.py`
- `livekit-agents/livekit/agents/ipc/inference_proc_lazy_main.py`
- `livekit-agents/livekit/agents/ipc/job_executor.py`
- `livekit-agents/livekit/agents/ipc/job_proc_executor.py`
- `livekit-agents/livekit/agents/ipc/job_proc_lazy_main.py`
- `livekit-agents/livekit/agents/ipc/job_thread_executor.py`
- `livekit-agents/livekit/agents/ipc/log_queue.py`
- `livekit-agents/livekit/agents/ipc/proc_client.py`
- `livekit-agents/livekit/agents/ipc/proc_pool.py`
- `livekit-agents/livekit/agents/ipc/proto.py`
- `livekit-agents/livekit/agents/ipc/supervised_proc.py`
- `livekit-agents/livekit/agents/job.py`
- `livekit-agents/livekit/agents/llm/chat_context.py`
- `livekit-agents/livekit/agents/llm/fallback_adapter.py`
- `livekit-agents/livekit/agents/llm/llm.py`
- `livekit-agents/livekit/agents/metrics/base.py`
- `livekit-agents/livekit/agents/metrics/utils.py`
- `livekit-agents/livekit/agents/plugin.py`
- `livekit-agents/livekit/agents/stt/fallback_adapter.py`
- `livekit-agents/livekit/agents/stt/stream_adapter.py`
- `livekit-agents/livekit/agents/stt/stt.py`
- `livekit-agents/livekit/agents/tokenize/_basic_sent.py`
- `livekit-agents/livekit/agents/tokenize/_basic_word.py`
- `livekit-agents/livekit/agents/tokenize/basic.py`
- `livekit-agents/livekit/agents/tokenize/token_stream.py`
- `livekit-agents/livekit/agents/tokenize/tokenizer.py`
- `livekit-agents/livekit/agents/tokenize/utils.py`
- `livekit-agents/livekit/agents/tts/fallback_adapter.py`
- `livekit-agents/livekit/agents/tts/stream_adapter.py`
- `livekit-agents/livekit/agents/tts/tts.py`
- `livekit-agents/livekit/agents/types.py`
- `livekit-agents/livekit/agents/utils/aio/channel.py`
- `livekit-agents/livekit/agents/utils/aio/interval.py`
- `livekit-agents/livekit/agents/utils/aio/itertools.py`
- `livekit-agents/livekit/agents/utils/aio/task_set.py`
- `livekit-agents/livekit/agents/utils/audio.py`
- `livekit-agents/livekit/agents/utils/codecs/decoder.py`
- `livekit-agents/livekit/agents/utils/connection_pool.py`
- `livekit-agents/livekit/agents/utils/hw/cpu.py`
- `livekit-agents/livekit/agents/utils/log.py`
- `livekit-agents/livekit/agents/vad.py`
- `livekit-agents/livekit/agents/version.py`
- `livekit-agents/livekit/agents/worker.py`

## Class Changes

### Renamed Classes
- PipelineEOUMetrics -> EOUMetrics

### Removed Classes
- `APIConnectOptions`
- `ATTRIBUTE_AGENT_STATE`
- `AgentCallContext`
- `AgentMetrics`
- `AgentOutput`
- `AgentPlayout`
- `AgentTranscriptionOptions`
- `AssistantPlotter`
- `AudioBuffer`
- `AudioStreamDecoder`
- `AutoSubscribe`
- `AvailabilityChangedEvent`
- `BaseContext`
- `CGroupV2CPUMonitor`
- `CalledFunction`
- `Chan`
- `ChatAudio`
- `ChatImage`
- `ChatMessage`
- `Choice`
- `ConnectionPool`
- `DuplexClosed`
- `EncodeOptions`
- `ExpFilter`
- `FunctionArgInfo`
- `FunctionCallInfo`
- `FunctionContext`
- `FunctionInfo`
- `HumanInput`
- `Hyphenator`
- `Image`
- `InferenceExecutor`
- `InferenceProcExecutor`
- `Interval`
- `LLM`
- `LLMCapabilities`
- `MessageChange`
- `MovingAverage`
- `MultimodalAgent`
- `MultimodalLLMMetrics`
- `NotGiven`
- `PUNCTUATIONS`
- `PipelineLLMMetrics`
- `PipelineSTTMetrics`
- `PipelineTTSMetrics`
- `PipelineVADMetrics`
- `PlayoutHandle`
- `PlotEventMessage`
- `PlotMessage`
- `Plugin`
- `ProcStartArgs`
- `PublishTranscriptionError`
- `ResizeOptions`
- `STTSegmentsForwarder`
- `Sleep`
- `SleepFinished`
- `SpeechData`
- `SpeechHandle`
- `StreamAdapter`
- `SupervisedProc`
- `SynthesisHandle`
- `TTSSegmentsForwarder`
- `TYPE_CHECKING`
- `TaskSet`
- `ToolChoice`
- `TypeInfo`
- `UsageCollector`
- `UsageSummary`
- `VoicePipelineAgent`
- `Worker`

### Added Classes
- `AgentMetrics`
- `AgentState`
- `AudioContent`
- `BaseModel`
- `DEFAULT_API_CONNECT_OPTIONS`
- `EOUMetrics`
- `FunctionCall`
- `FunctionCallOutput`
- `FunctionTool`
- `FunctionToolCall`
- `IPC_MESSAGES`
- `ImageContent`
- `JobExecutorType`
- `NOT_GIVEN`
- `Room`
- `SimulateJobArgs`
- `TTS`
- `ToolContext`
- `TracingRequest`
- `TracingResponse`
- `WorkerInfo`

## Migration Examples

