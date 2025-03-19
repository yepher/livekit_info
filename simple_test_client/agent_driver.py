import asyncio
import logging
from signal import SIGINT, SIGTERM
import os
import argparse

from livekit import rtc
from test_script import TestScript
from room_handlers import setup_room_handlers
from room_manager import run_room, cleanup

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Publish audio to a LiveKit room')
    parser.add_argument('--room', default='my-room', help='Name of the LiveKit room to join')
    parser.add_argument('--test', help='Name of the test to run (without .json extension)')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler("publish_wave.log"), logging.StreamHandler()],
    )

    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    room = rtc.Room(loop=loop)

    # Load test script if provided
    script = None
    if args.test:
        try:
            script_path = os.path.join('tests', f'{args.test}.json')
            if not os.path.exists(script_path):
                logging.error(f"Test script not found: {script_path}")
                os._exit(1)
            script = TestScript(script_path, room)
            logging.info(f"Loaded test script: {args.test}")
        except Exception as e:
            logging.error(f"Failed to load script: {e}")
            os._exit(1)

    # Set up room handlers
    setup_room_handlers(room, script)

    async def main():
        """Main function to run the agent driver."""
        try:
            await run_room(room, args.room, script)
            # Keep the main task running until cleanup is called
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("Main task cancelled")
            os._exit(0)
        except rtc.ConnectError as e:
            logging.error("Connection error in main task: %s", e)
            os._exit(1)
        except RuntimeError as e:
            logging.error("Runtime error in main task: %s", e)
            os._exit(1)

    # Start the main task
    main_task = asyncio.ensure_future(main())

    # Handle signals
    def signal_handler():
        logging.info("Received signal, shutting down...")
        os._exit(0)

    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, signal_handler)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
        os._exit(0)
    finally:
        loop.close()
