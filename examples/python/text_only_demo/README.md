# LiveKit Text Chat Demo

This demo demonstrates a simple text chat application using LiveKit's Python SDK. It allows users to connect to a room and exchange text messages with other participants.

## Features

- Connect to a LiveKit room
- Send and receive text messages
- View detailed room and participant information
- Monitor room events (participant connections, track publications, etc.)
- Graceful shutdown and cleanup

## Prerequisites

- Python 3.9+
- LiveKit server URL and API credentials
- `python-dotenv` package for environment variable management

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the text chat client:
```bash
python listen_text.py [room_name]
```
If no room name is provided, it will default to "text-chat-room".

2. Once connected, you can:
   - Type messages to send them to other participants
   - Type 'exit' or 'quit' to exit the application
   - Press Ctrl+C to force quit

3. The application will display:
   - System messages about room events
   - Messages from other participants
   - Your own messages with a "You:" prefix

## Room Events

The application logs various room events including:
- Participant connections/disconnections
- Track publications and subscriptions
- Room metadata changes
- Participant metadata changes
- Connection quality changes
- Transcription events
- Data messages
- SIP DTMF events
- E2EE state changes
- Connection state changes

## Error Handling

The application includes error handling for:
- Connection issues
- Message processing errors
- Graceful shutdown on exit commands or signals

## Notes

- The application uses asyncio for asynchronous operations
- All room events are logged to the console
- The application maintains a set of active tasks to prevent garbage collection
- Signal handlers are set up for graceful shutdown on SIGINT and SIGTERM
