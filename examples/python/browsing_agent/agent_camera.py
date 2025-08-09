import asyncio
import logging
from pathlib import Path
from PIL import Image
import numpy as np
from livekit import rtc

logger = logging.getLogger("agent-camera")

class AgentCamera:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.source = rtc.VideoSource(480, 640)
        self.track = rtc.LocalVideoTrack.create_video_track("agent", self.source)
        self.publication = None
        
        # Load and prepare the agent image
        img = Image.open(image_path)
        img = img.resize((480, 640), Image.Resampling.LANCZOS)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        self.img_array = np.array(img)

    async def start(self, room: rtc.Room):
        # Publish video track
        options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_CAMERA)
        self.publication = await room.local_participant.publish_track(self.track, options)
        logger.info("published track", extra={"track_sid": self.publication.sid})
        
        # Start drawing task
        self._draw_task = asyncio.create_task(self._draw_agent())

    async def stop(self, room: rtc.Room):
        # Stop drawing task
        if hasattr(self, '_draw_task'):
            self._draw_task.cancel()
            try:
                await self._draw_task
            except asyncio.CancelledError:
                pass

        # Unpublish track
        if self.publication:
            await room.local_participant.unpublish_track(self.publication.track.sid)
            self.publication = None

    async def _draw_agent(self):
        while True:
            await asyncio.sleep(0.1)  # 100ms
            frame = rtc.VideoFrame(480, 640, rtc.VideoBufferType.RGBA, self.img_array.tobytes())
            self.source.capture_frame(frame) 