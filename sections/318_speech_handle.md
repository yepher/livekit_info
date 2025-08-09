### SpeechHandle architecture and usage

This document describes `agents/src/voice/speech_handle.ts`, a small control object representing a queued TTS playback segment. It exposes interruption, authorization, and playout completion signals and carries an associated chat message.

#### Purpose

- Represent one unit of speech output, carrying metadata such as priority and parent linkage.
- Allow callers to interrupt (if permitted), await authorization, and await playout completion.
- Provide a future-like interface (`then`, `waitForPlayout`) to chain logic after playback.

#### API

- Static priorities:
  - `SPEECH_PRIORITY_LOW = 0`, `SPEECH_PRIORITY_NORMAL = 5`, `SPEECH_PRIORITY_HIGH = 10`.

- Creation:
  - `SpeechHandle.create({ allowInterruptions?, stepIndex?, parent? })` → new handle with unique id.

- Properties and getters:
  - `id: string`, `allowInterruptions: boolean`, `stepIndex: number`, `parent?: SpeechHandle`.
  - `interrupted: boolean` – set once `interrupt()` is called.
  - `done: boolean` – set once playout completes.
  - `chatMessage?: ChatMessage` – associated message when known.

- Control methods:
  - `interrupt()` – resolves the internal interrupt future; throws if interruptions are not allowed or if already done.
  - `then(cb)` – run `cb(handle)` after playout done.
  - `waitForPlayout()` – await playout completion.
  - `waitIfNotInterrupted(promises: Promise[])` – races the provided promises against the interrupt future; returns once either bucket resolves.

- Internal (used by queue/execution engine):
  - `_setChatMessage(msg)`, `_authorizePlayout()`, `_waitForAuthorization()`, `_markPlayoutDone()`.

#### Typical usage

```ts
const handle = SpeechHandle.create({ allowInterruptions: true });

// Queue speech and await completion later
handle.then(() => console.log('speech done'));

// Interrupt if a VAD event indicates the user spoke
handle.interrupt();
```

#### Interaction with AgentActivity and IO

- When TTS starts/queues, a `SpeechHandle` is created and returned to the caller (e.g., `AgentSession.say()` or `generateReply()`).
- The IO layer (`AudioOutput`) reports playback finished events, which eventually call `_markPlayoutDone()`.
- VAD events can call `handle.interrupt()` to stop playback early (if `allowInterruptions`).

#### Known shortcomings and probable bugs

- Interrupt after done
  - `interrupt()` returns early if `done` is true; callers may assume an error is thrown. This is a design choice but document clearly.

- Authorization is never rejected
  - `_waitForAuthorization()` awaits a future that is resolved via `_authorizePlayout()` but never rejected; queues must enforce cancellation semantics separately.

- No timeout helpers
  - No built-in timeout for authorization or playout; upstream must handle timeouts.

- Parent linkage is not used here
  - `parent` is stored but not leveraged in this module; ensure upstream semantics (e.g., batching or hierarchical cancellation) are implemented if needed.


