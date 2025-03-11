## Performance Monitoring & Metrics

The framework provides detailed performance metrics collected through utility modules. All metrics are measured in milliseconds unless otherwise specified.

```mermaid
graph TD
    A[User Input] --> B[STT Processing]
    B --> C[LLM Processing]
    C --> D[Function Execution]
    D --> E[TTS Synthesis]
    E --> F[Audio Output]
    style B fill:#f9d,stroke:#333
    style C fill:#9df,stroke:#333
    style D fill:#fd9,stroke:#333
    style E fill:#dfd,stroke:#333
```

### Core Metrics

| Metric | Calculation | Description | Impact Factors |
|--------|-------------|-------------|----------------|
| **STT Latency** | `transcript_end - audio_start` | Full speech-to-text conversion time | Audio length, model complexity |
| **TTFB (Time to First Byte)** | `first_audio_frame_time - text_start` | TTS response initiation delay | text length, model complexity  |
| **TTFT (Time to First Token)** | `first_token_time - llm_start` | LLM response initiation delay | Model size, context length |


### Metric Visualization

```mermaid
gantt
    title End-to-End Processing Timeline
    dateFormat  X
    axisFormat %s
    section Components
    STT Processing : 0, 1500
    LLM Processing : 1500, 3000
    TTS Synthesis : 3000, 4500
```

### Initial Prompt Metrics Example

This example breaks down what metrics are calculated during the initial prompt when someone joins the room that says:  

`Initial Prompt: Hello from the weather station. Tell me your location to check the weather.`

The text is chunked into two parts and sent to TTS.

```mermaid
sequenceDiagram
    participant U as User
    participant agent as Agent
    participant VAD
    participant EOU
    participant STT as STT<br>Deepgram
    participant LLM as LLM<br>OpenAI
    participant FNC as Function
    participant TTS as TTS<br>OpenAI
    
    Note over agent,TTS: Initial Prompt: Hello from the weather station. Tell me your location to check the weather.<br>Note: can get split into multip chuncks that will have same sequence_id
    
    agent->>agent: chunck text

    Note over agent,TTS: ChunkA: Hello from the weather station.
    agent->>+TTS: Hello from the weather station.
    TTS->>agent: audio frame[0]
    Note left of U: TTFB = time until agent receive frist audio frame
    agent->>U: audio frame[0]
    agent->>agent: audio_duration += audio frame[0].duration
    TTS->>-agent: audio frame[1-N]
    agent->>agent: audio_duration += audio frame[1-N].duration
    agent->>U: audio frame[1-N]
    Note left of U: audio_duration = sum of all audio frame durations


    Note over agent,TTS: ChunkB: Tell me your location to check the weather.
    agent->>+TTS: Tell me your location to check the weather.
    TTS->>agent: audio frame[0]
    Note left of U: TTFB = time until agent receive frist audio frame
    TTS->>agent: audio frame[0]
    agent->>agent: audio_duration += audio frame[0].duration
    TTS->>-agent: audio frame[1-N]
    agent->>agent: audio_duration += audio frame[1-N].duration
    agent->>U: audio frame[1-N]
    Note left of U: audio_duration = sum of all audio frame durations
```

## Metrics Round Trip (no function call)

This example breaks down what metrics are calculated during a user request and the response they hear.

**User:** `Can you hear me?`
**Reponse:** `Yes, I can hear you! Please tell me the location you'd like the weather for.`


```mermaid
sequenceDiagram
    participant U as User
    participant agent as Agent
    participant STT as STT<br>Deepgram
    participant LLM as LLM<br>OpenAI
    participant FNC as Function
    participant TTS as TTS<br>OpenAI
    participant OpenAI
    

    U->>agent: Audio: Can you hear me?
    STT->>+STT: Start STT duration timer
    agent->>STT: audio frame[0]
    Note over STT,LLM: event START_OF_SPEECH
    Note over STT,LLM: event RECOGNITION_USAGE
    Note over STT,LLM: event INTERIM_TRANSCRIPT
    STT->>OpenAI: audio frame[0]

    agent->>STT: audio frame[1-n]
    STT->>OpenAI: audio frame[1-n]
    Note over STT,LLM: event FINAL_TRANSCRIPT
    OpenAI->>STT: Text: Can you hear me?
    STT->>LLM: Text: Can you hear me?
    Note over STT,LLM: END_OF_SPEECH


    LLM->>+LLM: Start LLM duration timer
    LLM->>OpenAI: Inference on text: "Can you hear me?"
    OpenAI->>LLM: tokens
    Note over LLM,OpenAI: TTFT = Time of transmit text until first tokens are returned

    LLM->>TTS: LLM Response
    OpenAI->>LLM: completion_tokens=20, prompt_tokens=184, total_tokens=204, cache_creation_input_tokens=0, cache_read_input_tokens=0
    Note over LLM,OpenAi: LLM Duration = Time since LLM timer start
    Note over LLM,OpenAi: tokens_per_second = completion_tokens / LLM duration
    TTS->>TTS: Start TTS timer

    
    Note over agent,TTS: Text: Yes, I can hear you! Please tell me the location you'd like the weather for.
    
    agent->>agent: chunck text

    Note over agent,TTS: ChunkA: Yes, I can hear you! Please tell me the location you'd like the weather for.
    agent->>+TTS: Yes, I can hear you! Please tell me the location you'd like the weather for.
    TTS->>agent: audio frame[0]
    Note left of U: TTFB = time until agent receive frist audio frame
    agent->>U: audio frame[0]
    agent->>agent: audio_duration += audio frame[0].duration
    TTS->>-agent: audio frame[1-N]
    agent->>agent: audio_duration += audio frame[1-N].duration
    agent->>U: audio frame[1-N]
    Note left of U: audio_duration = sum of all audio frame durations
    STT->>-agent: stt duration = time since STT process started (cumulative)
```



### Best Practices

1. Monitor P90/P95 values instead of averages
2. Set component-specific alert thresholds
3. Correlate metrics with business KPIs
4. Retain historical data for trend analysis
5. Implement metric sampling in high-volume systems
6. Use dimensional tagging for advanced filtering
7. Combine with distributed tracing for debugging

This section should be added after the [Error Handling Strategies](#error-handling-strategies) section in the API guide.

