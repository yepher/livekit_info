## LiveKit Agents 1.0 Migration Guide

This guide summarizes the major updates in the Agents 1.0 branch and provides steps for migrating your current agent implementation. The changes include dependency updates, API and module restructuring, new features, and some minor refactoring.

1. Dependency Updates
	*	Plugin Version Bumps:
	Several plugins now require updated versions. For example:
		*	ElevenLabs, Deepgram, Google, and others have new patch or minor version bumps.
	*	Update your requirements to use the versions specified in the changesets (e.g., deepgram to `≥0.6.19`, elevenlabs to `≥0.7.13`).
	Refer to the changesets in the diff for specific version bumps.
	*	Agent Package Version:
		* Ensure you upgrade to the latest livekit-agents version (now reflecting the 1.0-compatible changes). Adjust your dependency files (e.g., `requirements.txt`) accordingly.

2. API and Module Restructuring
	*	Module Consolidation:
	*	Old Structure: Previously, you might have imported functionality from separate modules such as multimodal, pipeline, or voice_assistant.
	*	New Structure: These have been consolidated under the voice module.
	*	Action: Replace imports like:

`from livekit.agents.voice_assistant import SomeClass`

with:

`from livekit.agents.voice import VoiceAgent, SomeClass`


Check the updated `livekit-agents/livekit/agents/__init__.py` for the new export list.   ￼

*	New Features:
	*	Streaming AudioDecoder:
	The internal audio processing now uses a streaming AudioDecoder to handle compressed encoding. If your agent has custom audio handling, verify that it aligns with the new streaming-based approach.
	*	`tts.prewarm` Method:
	A new method, `tts.prewarm`, has been added to initialize the TTS connection pool early.
	*	Action: If you depend on TTS latency, consider invoking `tts.prewarm()` before starting synthesis.
	*	Deprecated Options:
	Some options (like ElevenLabs’ `optimize_stream_latency`) have been deprecated. Remove or replace these with the new recommended configurations.
	
3. Code Formatting and Minor Refactors
	*	Function Signatures and Formatting:
	*	Some functions (e.g., in `update_versions.py` and various agent examples) have been reformatted to simplify the signatures.
	*	Check for minor differences such as in exception initializations (e.g., using a single-line signature) and adjust your code if necessary.
	*	File Writing and String Handling:
	Minor changes (such as joining strings for log output) might require small adjustments if your code directly manipulates these parts.

4. Updating Example Implementations
	*	Avatar Example:
	*	New files like `agent_worker.py`, `avatar_runner.py`, and `dispatcher.py` show updated patterns for:
	*	Connecting to the LiveKit room.
	*	Creating a worker that streams audio and video.
	*	Using the new data sinks (for example, DataStreamAudioSink).
	*	Action: Compare your current agent’s connection and streaming logic with these updated examples to spot differences.
	*	Minimal and Other Worker Examples:
	*	Review changes in the `minimal_worker.py` and other example files to update how you instantiate and start your VoiceAgent or any other agent type.
	*	Notice the removal of deprecated parameters and the new initialization patterns.

5. Testing and Validation
	*	End-to-End Testing:
	After making the updates, test your agent in a controlled environment to:
	*	Ensure room connections, audio/video streams, and TTS/STT integrations work correctly.
	*	Validate that any new features (like `tts.prewarm`) are functioning as intended.
	*	Compare with Updated Examples:
	Use the provided examples as a reference point. Although the examples in the repository might not all be fully updated, they include many of the changes required for 1.0 compatibility.

## Final Checklist

1.	Dependencies: Update your package versions as per the new requirements.
2.	Imports: Replace deprecated module imports (e.g., from voice_assistant/multimodal to voice).
3.	API Adjustments:
	*	Use the new streaming AudioDecoder where needed.
	*	Integrate the tts.prewarm method if your TTS provider benefits from early connection setup.
4.	Refactor Code: Make minor adjustments to function signatures and logging as indicated by the diff.
5.	Review Examples: Compare your code with updated examples in the examples/ folder for additional context.

Following this guide should help you update your agent for Agents 1.0 compatibility. If you run into any issues or have specific questions about parts of your implementation, feel free to ask!