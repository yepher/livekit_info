# Common Terms

There are many terms used commonly throughout the code base and documentation. Some of them are defined here:


| Acronym | Full Form | Description | Reference Link |
|---------|-----------|-------------|----------------|
| **API** | Application Programming Interface | Service endpoints | [AWS Definition](https://aws.amazon.com/what-is/api/) |
| **AV1** | AOMedia Video 1 | Open codec | [AOMedia Spec](https://aomediacodec.github.io/av1-spec/) |
| **BL** | Base Layer | SVC foundation | [ITU SVC Docs](https://www.itu.int/rec/T-REC-H.264-201704-I/en) |
| **CDN** | Content Delivery Network | Content caching | [Cloudflare CDN](https://www.cloudflare.com/learning/cdn/what-is-a-cdn/) |
| **CLI** | Command-Line Interface | Tool to run and manage the worker (dev/prod, connect, download) | [Wikipedia](https://en.wikipedia.org/wiki/Command-line_interface) |
| **CPU** | Central Processing Unit | Processor | [TechTarget Definition](https://www.techtarget.com/whatis/definition/processor) |
| **DTLS** | Datagram Transport Layer Security | UDP encryption | [RFC 9147](https://datatracker.ietf.org/doc/html/rfc9147) |
| **E2EE** | End-to-End Encryption | Encryption where only endpoints can read the data | [Wikipedia](https://en.wikipedia.org/wiki/End-to-end_encryption) |
| **EL** | Enhancement Layer | SVC improvements | [ITU SVC Docs](https://www.itu.int/rec/T-REC-H.264-201704-I/en) |
| **EOU** | End Of Utterance | Decision point marking the end of the user's turn | [Turn-taking](https://en.wikipedia.org/wiki/Turn-taking) |
| **FEC** | Forward Error Correction | Error recovery | [RFC 5109](https://datatracker.ietf.org/doc/html/rfc5109) |
| **GPU** | Graphics Processing Unit | Accelerator used for model inference | [Wikipedia](https://en.wikipedia.org/wiki/Graphics_processing_unit) |
| **gRPC** | Google Remote Procedure Call | RPC framework | [gRPC Official](https://grpc.io/) |
| **H.264** | MPEG-4 AVC | Video standard | [ITU-T H.264](https://www.itu.int/rec/T-REC-H.264) |
| **HLS** | HTTP Live Streaming | Adaptive streaming | [Apple HLS](https://developer.apple.com/streaming/) |
| **HTTP** | Hypertext Transfer Protocol | Application protocol for requests/responses | [MDN](https://developer.mozilla.org/docs/Web/HTTP) |
| **HTTPS** | Hypertext Transfer Protocol Secure | HTTP over TLS (`https://`) | [Wikipedia](https://en.wikipedia.org/wiki/HTTPS) |
| **ICE** | Interactive Connectivity Establishment | NAT traversal framework | [RFC 8445](https://datatracker.ietf.org/doc/html/rfc8445) |
| **IPC** | Inter-Process Communication | Messaging between worker and child processes | [Wikipedia](https://en.wikipedia.org/wiki/Inter-process_communication) |
| **JSON** | JavaScript Object Notation | Text data format used for APIs and metrics | [RFC 8259](https://datatracker.ietf.org/doc/html/rfc8259) |
| **JWT** | JSON Web Token | Authentication standard | [RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519) |
| **LLM** | Large Language Model | Generates text and tools; used for agent replies | [Wikipedia](https://en.wikipedia.org/wiki/Large_language_model) |
| **NACK** | Negative Acknowledgement | Loss feedback | [RFC 4585](https://datatracker.ietf.org/doc/html/rfc4585) |
| **NAT** | Network Address Translation | IP translation | [Cloudflare Explanation](https://www.cloudflare.com/learning/network-layer/what-is-nat/) |
| **ONNX** | Open Neural Network Exchange | Open format for ML models (used by Silero VAD) | [ONNX](https://onnx.ai/) |
| **Opus** | Opus Audio Codec | Audio codec | [RFC 6716](https://datatracker.ietf.org/doc/html/rfc6716) |
| **P2P** | Peer-to-Peer | Direct communication | [IETF P2P Architecture](https://datatracker.ietf.org/wg/p2psip/documents/) |
| **QoS** | Quality of Service | Network prioritization | [Cisco QoS](https://www.cisco.com/c/en/us/tech/quality-of-service-qos/tech-qos-best-effort.html) |
| **RTC** | Real-Time Communication | Low-latency media | [W3C WebRTC](https://webrtc.org/) |
| **RTMP** | Real-Time Messaging Protocol | Streaming protocol | [Adobe RTMP](https://www.adobe.com/devnet/rtmp.html) |
| **RTT** | Round-Trip Time | Latency measure | [IETF Definition](https://www.ietf.org/rfc/rfc2681.txt) |
| **SCTP** | Stream Control Transmission Protocol | Data transport | [RFC 4960](https://datatracker.ietf.org/doc/html/rfc4960) |
| **SDK** | Software Development Kit | Client libraries | [Red Hat Definition](https://www.redhat.com/en/topics/cloud-native-apps/what-is-SDK) |
| **SDP** | Session Description Protocol | Media negotiation | [RFC 4566](https://datatracker.ietf.org/doc/html/rfc4566) |
| **SFU** | Selective Forwarding Unit | Media routing server | [WebRTC Glossary](https://webrtcglossary.com/sfu/) |
| **SIP** | Session Initiation Protocol | VoIP protocol | [RFC 3261](https://datatracker.ietf.org/doc/html/rfc3261) |
| **SLA** | Service Level Agreement | Performance contract | [Microsoft Azure SLA](https://azure.microsoft.com/en-us/support/legal/sla/) |
| **SRTP** | Secure Real-time Transport Protocol | Media encryption | [RFC 3711](https://datatracker.ietf.org/doc/html/rfc3711) |
| **STUN** | Session Traversal Utilities for NAT | NAT discovery protocol | [RFC 8489](https://datatracker.ietf.org/doc/html/rfc8489) |
| **STT** | Speech-to-Text | Converts audio to text (streaming or non‑streaming) | [Wikipedia](https://en.wikipedia.org/wiki/Speech_recognition) |
| **SVC** | Scalable Video Coding | Layered video encoding | [ITU-T H.264 Annex G](https://www.itu.int/rec/T-REC-H.264) |
| **TCP** | Transmission Control Protocol | Transport protocol | [RFC 793](https://datatracker.ietf.org/doc/html/rfc793) |
| **TTFB** | Time To First Byte | Latency to the first audio frame/byte from a response | [Wikipedia](https://en.wikipedia.org/wiki/Time_to_first_byte) |
| **TTFT** | Time To First Token | Latency to the first generated token from an LLM |  |
| **TTS** | Text-to-Speech | Synthesizes audio from text (streaming or non‑streaming) | [Wikipedia](https://en.wikipedia.org/wiki/Speech_synthesis) |
| **TURN** | Traversal Using Relays around NAT | Relay protocol | [RFC 8656](https://datatracker.ietf.org/doc/html/rfc8656) |
| **UDP** | User Datagram Protocol | Transport protocol | [RFC 768](https://datatracker.ietf.org/doc/html/rfc768) |
| **URL** | Uniform Resource Locator | Address of a resource (e.g., LiveKit server) | [Wikipedia](https://en.wikipedia.org/wiki/URL) |
| **UUID** | Universally Unique Identifier | 128-bit unique identifier (RFC 4122) | [RFC 4122](https://datatracker.ietf.org/doc/html/rfc4122) |
| **VAD** | Voice Activity Detection | Detects speech segments in audio streams | [Wikipedia](https://en.wikipedia.org/wiki/Voice_activity_detection) |
| **VOD** | Video On Demand | Fast Forward, Rewind, Pause | |
| **VP8/9** | Video Processing 8/9 | Video codecs | [RFC 6386 (VP8)](https://datatracker.ietf.org/doc/html/rfc6386) |
| **WebRTC** | Web Real-Time Communication | Framework for real-time media | [WebRTC Overview](https://webrtc.org/) |
| **WHIP** | WebRTC-HTTP Ingestion Protocol | Ingest protocol | [IETF Draft](https://datatracker.ietf.org/doc/draft-ietf-wish-whip/) |
| **WS** | WebSocket (ws://) | Unencrypted WebSocket scheme | [RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455) |
| **WSS** | WebSocket Secure (wss://) | WebSocket over TLS | [RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455) |





## Helpful Overviews

* [How LiveKit built a globally distributed mesh network to scale WebRTC](https://blog.livekit.io/scaling-webrtc-with-distributed-mesh/)