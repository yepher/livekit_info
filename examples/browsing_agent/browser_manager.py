import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page
from PIL import Image, ImageOps
import io
from livekit import rtc

logger = logging.getLogger("browser-manager")

WIDTH = 640
HEIGHT = 480

DEFAULT_URL = "https://docs.livekit.io/agents/v1/"
#DEFAULT_URL = "https://deepwiki.com/livekit/agents"

class BrowserAutomation:
    def __init__(self, page: Page):
        self.page = page
        self.auto_scroll_task = None
        self.auto_scroll_speed = 1.0
        self.auto_scroll_direction = 0  # 0: stopped, 1: down, -1: up

    async def check_page(self) -> bool:
        """Checks if the page is still responsive."""
        try:
            await self.page.evaluate("1 + 1")
            return True
        except Exception as e:
            logger.error(f"Page check failed: {e}")
            return False

    async def wait_for_load(self) -> bool:
        """Waits for the page to be fully loaded."""
        try:
            # Increase timeout to 60 seconds
            await self.page.wait_for_load_state("networkidle", timeout=60000)
            await self.page.wait_for_load_state("domcontentloaded", timeout=60000)
            return True
        except Exception as e:
            logger.error(f"Wait for load failed: {e}")
            # If we get a timeout, try to continue anyway
            if "Timeout" in str(e):
                logger.warning("Continuing despite timeout - page may not be fully loaded")
                return True
            return False

    async def navigate_to(self, url: str) -> bool:
        try:
            if not await self.check_page():
                return False
            await self.page.goto(url)
            return await self.wait_for_load()
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False

    async def go_back(self) -> bool:
        try:
            if not await self.check_page():
                return False
            await self.page.go_back()
            return True
        except Exception as e:
            logger.error(f"Go back error: {e}")
            return False

    async def go_forward(self) -> bool:
        try:
            if not await self.check_page():
                return False
            await self.page.go_forward()
            return True
        except Exception as e:
            logger.error(f"Go forward error: {e}")
            return False

    async def reload(self) -> bool:
        try:
            if not await self.check_page():
                return False
            await self.page.reload()
            return True
        except Exception as e:
            logger.error(f"Reload error: {e}")
            return False

    async def scroll_down(self, pixels: int = 100) -> bool:
        try:
            if not await self.check_page():
                return False
            await self.page.evaluate(f"window.scrollBy(0, {pixels})")
            return True
        except Exception as e:
            logger.error(f"Scroll down error: {e}")
            return False

    async def scroll_up(self, pixels: int = 100) -> bool:
        try:
            if not await self.check_page():
                return False
            await self.page.evaluate(f"window.scrollBy(0, -{pixels})")
            return True
        except Exception as e:
            logger.error(f"Scroll up error: {e}")
            return False

    async def start_auto_scroll(self, direction: int, speed: float = 1.0) -> str:
        try:
            if not await self.check_page():
                return "failed"
            self.auto_scroll_direction = direction
            self.auto_scroll_speed = max(0.2, min(3.0, speed))
            
            if self.auto_scroll_task:
                self.auto_scroll_task.cancel()
            
            self.auto_scroll_task = asyncio.create_task(self._auto_scroll())
            return "done"
        except Exception as e:
            logger.error(f"Start auto-scroll error: {e}")
            return "failed"

    async def stop_auto_scroll(self) -> str:
        try:
            if self.auto_scroll_task:
                self.auto_scroll_task.cancel()
                self.auto_scroll_task = None
            self.auto_scroll_direction = 0
            return "done"
        except Exception as e:
            logger.error(f"Stop auto-scroll error: {e}")
            return "failed"

    async def _auto_scroll(self):
        while self.auto_scroll_direction != 0:
            try:
                # Check if we've reached the page boundaries
                scroll_position = await self.page.evaluate("""() => {
                    return {
                        scrollTop: window.scrollY,
                        scrollHeight: document.documentElement.scrollHeight,
                        clientHeight: document.documentElement.clientHeight
                    };
                }""")
                
                # Stop if we've reached the bottom (scrolling down) or top (scrolling up)
                if (self.auto_scroll_direction > 0 and 
                    scroll_position["scrollTop"] + scroll_position["clientHeight"] >= scroll_position["scrollHeight"]):
                    logger.info("Reached bottom of page, stopping auto-scroll")
                    self.auto_scroll_direction = 0
                    return "I've reached the bottom of the page, so I stopped scrolling."
                elif (self.auto_scroll_direction < 0 and 
                      scroll_position["scrollTop"] <= 0):
                    logger.info("Reached top of page, stopping auto-scroll")
                    self.auto_scroll_direction = 0
                    return "I've reached the top of the page, so I stopped scrolling."
                
                # Continue scrolling if we haven't reached the boundaries
                pixels = int(10 * self.auto_scroll_speed)
                await self.page.evaluate(f"window.scrollBy(0, {pixels * self.auto_scroll_direction})")
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Auto-scroll error: {e}")
                break
        return None

    async def click_at(self, x: int, y: int) -> bool:
        try:
            if not await self.check_page():
                return False
            
            # Wait for the page to be stable
            await self.page.wait_for_load_state("networkidle")
            await self.page.mouse.click(x, y)
            return True
        except Exception as e:
            logger.error(f"Click at coordinates error: {e}")
            return False

    async def click_by_text(self, text: str) -> bool:
        try:
            if not await self.check_page():
                return False
            
            # Wait for the element to be visible and clickable
            await self.page.wait_for_selector(f"text={text}", state="visible", timeout=5000)
            await self.page.click(f"text={text}")
            return True
        except Exception as e:
            logger.error(f"Click by text error: {e}")
            return False

    async def fill_input(self, selector: str, value: str) -> bool:
        try:
            if not await self.check_page():
                return False
            
            # Wait for the input to be visible and enabled
            await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            
            # Clear any existing value
            await self.page.fill(selector, "")
            
            # Type the new value
            await self.page.type(selector, value)
            return True
        except Exception as e:
            logger.error(f"Fill input error: {e}")
            return False

    async def select_option(self, selector: str, value: str) -> bool:
        try:
            if not await self.check_page():
                return False
            
            # Wait for the select element to be visible and enabled
            await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            await self.page.select_option(selector, value)
            return True
        except Exception as e:
            logger.error(f"Select option error: {e}")
            return False

    async def list_input_fields(self) -> List[Dict[str, Any]]:
        try:
            if not await self.check_page():
                return []
            fields = await self.page.evaluate("""() => {
                const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
                return inputs.map(input => ({
                    type: input.tagName.toLowerCase(),
                    name: input.name || '',
                    id: input.id || '',
                    placeholder: input.placeholder || '',
                    value: input.value || '',
                    label: input.labels ? Array.from(input.labels).map(l => l.textContent).join(', ') : ''
                }));
            }""")
            return fields
        except Exception as e:
            logger.error(f"List input fields error: {e}")
            return []

    async def read_page_content(self) -> str:
        try:
            if not await self.check_page():
                return ""
            content = await self.page.evaluate("""() => {
                const content = [];
                const elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, a');
                elements.forEach(el => {
                    const text = el.textContent.trim();
                    if (text) {
                        if (el.tagName.startsWith('H')) {
                            content.push(`#${el.tagName[1]} ${text}`);
                        } else if (el.tagName === 'A') {
                            content.push(`[${text}](${el.href})`);
                        } else {
                            content.push(text);
                        }
                    }
                });
                return content.join('\\n\\n');
            }""")
            return content
        except Exception as e:
            logger.error(f"Read page content error: {e}")
            return ""

    async def get_page_title(self) -> str:
        try:
            if not await self.check_page():
                return ""
            return await self.page.title()
        except Exception as e:
            logger.error(f"Get page title error: {e}")
            return ""

    async def scroll_to_section(self, text: str) -> bool:
        try:
            if not await self.check_page():
                return False

            section_text = text.lower()
            
            selectors = [
                "h1, h2, h3, h4, h5, h6",
                "section",
                "div[id*='section']",
                "div[class*='section']",
                "[role='region']", 
                "div"
            ]
            
            for selector in selectors:
                elements = self.page.locator(selector).get_by_text(text, exact=False)
                count = await elements.count()
                
                if count > 0:
                    element = elements.first
                    await element.evaluate("element => element.scrollIntoView({block: 'start', behavior: 'smooth'})")
                    await self.page.evaluate("window.scrollBy(0, -50)")

                    await self.page.wait_for_timeout(500)
                    return True
            
            logger.warning(f"No section {text} not found.")
            return False
            
        except Exception as e:
            logger.error(f"Error scrolling to section '{text}': {e}")
            return False

    async def press_enter(self) -> bool:
        """Simulates pressing the Enter key."""
        try:
            if not await self.check_page():
                return False
            
            # Wait for the page to be stable
            await self.page.wait_for_load_state("networkidle")
            
            # Press Enter key
            await self.page.keyboard.press("Enter")
            return True
        except Exception as e:
            logger.error(f"Press Enter error: {e}")
            return False

class BrowserState:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.is_open = False
        self.screen_source = None
        self.screen_track = None
        self.publication = None
        self.screenshare_task = None
        self.last_screenshot = None
        self.last_url = None
        self.last_update_time = 0
        self.last_content_hash = None
        self.automation = None
        self.pages = []
        self.active_tab_index = 0
        self.context = None
        self.pending_new_tab_notification = None

    async def check_and_recover(self) -> bool:
        """Checks if the browser is still responsive and recovers if needed."""
        try:
            if not self.page or not self.browser:
                return False
            # Try a simple operation to check if the page is still responsive
            await self.page.evaluate("1 + 1")
            return True
        except Exception as e:
            logger.error(f"Browser check failed: {e}")
            try:
                # Try to recover by creating a new page
                if self.browser:
                    self.page = await self.browser.new_page()
                    if self.automation:
                        self.automation.page = self.page
                    return True
            except Exception as e:
                logger.error(f"Browser recovery failed: {e}")
                return False
        return False

    async def get_screenshot(self):
        if not self.page:
            return None
            
        try:
            current_time = time.time()
            current_url = self.page.url
            
            time_since_last = current_time - self.last_update_time
            if time_since_last < 3 and self.last_screenshot is not None:
                if time_since_last < 1:
                    return self.last_screenshot
            
            # Check if URL changed (always capture on URL change)
            url_changed = current_url != self.last_url
            
            content_changed = False
            if not url_changed and self.last_screenshot is not None:
                try:
                    sample_screenshot = await self.page.screenshot(type='png', clip={'x': 0, 'y': 0, 'width': 100, 'height': 100})
                    import hashlib
                    current_hash = hashlib.md5(sample_screenshot).hexdigest()
                    if not hasattr(self, 'last_content_hash') or self.last_content_hash is None:
                        self.last_content_hash = current_hash
                        content_changed = True
                    else:
                        content_changed = current_hash != self.last_content_hash
                        self.last_content_hash = current_hash
                except Exception:
                    content_changed = True
            
            if (url_changed or content_changed or 
                self.last_screenshot is None or 
                time_since_last >= 3):
                
                self.last_screenshot = await self.page.screenshot(type='png')
                self.last_url = current_url
                self.last_update_time = current_time
                
            return self.last_screenshot
        except Exception as e:
            logger.error(f"Error getting screenshot: {e}")
            # Try to recover the browser
            if await self.check_and_recover():
                try:
                    self.last_screenshot = await self.page.screenshot(type='png')
                    self.last_url = self.page.url
                    self.last_update_time = time.time()
                    return self.last_screenshot
                except Exception as e:
                    logger.error(f"Failed to recover screenshot: {e}")
            return None

    async def open_browser(self, room: rtc.Room) -> bool:
        """Opens a browser window and starts screen sharing."""
        if not self.is_open:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True)
                self.context = await self.browser.new_context()
                
                self.context.on("page", self._on_new_page)
                
                self._initializing_browser = True
                
                self.page = await self.context.new_page()
                self.pages = [self.page]
                self.active_tab_index = 0
                self.is_open = True
                self.last_update_time = time.time()
                self.automation = BrowserAutomation(self.page)
                
                self._initializing_browser = False

                # Navigate to default page
                await self.automation.navigate_to(DEFAULT_URL)

                # Initialize screen share
                self.screen_source = rtc.VideoSource(WIDTH, HEIGHT)
                self.screen_track = rtc.LocalVideoTrack.create_video_track("browser", self.screen_source)
                options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_SCREENSHARE)
                self.publication = await room.local_participant.publish_track(
                    self.screen_track, options
                )
                logger.info("published track", extra={"track_sid": self.publication.sid})

                # Start screenshare task
                self.screenshare_task = asyncio.create_task(
                    self._draw_screenshare(self.screen_source)
                )
                return True
            except Exception as e:
                logger.error(f"Error opening browser: {e}")
                return False
        return True

    async def close_browser(self, room: rtc.Room) -> bool:
        """Closes the browser window and stops screen sharing."""
        if self.is_open:
            try:
                # Cancel screenshare task first
                if self.screenshare_task:
                    self.screenshare_task.cancel()
                    try:
                        await self.screenshare_task
                    except asyncio.CancelledError:
                        pass
                    self.screenshare_task = None

                # Unpublish track
                if self.publication:
                    # Unpublish the track
                    logger.info("unpublishing track", extra={"track_sid": self.publication.track.sid})
                    await room.local_participant.unpublish_track(self.publication.track.sid)
                    self.publication = None
                    self.screen_track = None
                    self.screen_source = None

                if self.pages:
                    for page in self.pages:
                        try:
                            await page.close()
                        except Exception as e:
                            logger.error(f"Error closing page: {e}")

                # Close browser context and browser
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()

                # Reset state
                self.browser = None
                self.page = None
                self.context = None
                self.pages = []
                self.active_tab_index = 0
                self.playwright = None
                self.is_open = False
                self.last_screenshot = None
                self.last_url = None
                self.last_update_time = 0
                self.automation = None
                return True
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
                return False
        return True

    async def _draw_screenshare(self, screen_source):
        if not self.is_open:
            return

        while self.is_open:
            try:
                await asyncio.sleep(0.1)  # Check frequently for changes
                
                # Get cached or new screenshot
                screenshot = await self.get_screenshot()
                if screenshot is None:
                    continue
                
                # Convert PNG to RGBA format and pad to fit
                img = Image.open(io.BytesIO(screenshot))
                img = img.convert('RGBA')
                img = ImageOps.pad(img, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS, color=(0, 0, 0, 0))
                
                # Create frame from image data
                frame = rtc.VideoFrame(WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, img.tobytes())
                screen_source.capture_frame(frame)
            except Exception as e:
                logger.error(f"Error capturing screenshot: {e}")
                break 

    async def perform_action(self, action: str, **kwargs) -> str:
        """Performs a browser action and returns a status message."""
        if not self.is_open:
            return "Browser is not open. Please open it first."
        
        if not self.automation:
            return "Browser automation is not initialized."

        try:
            success = False

            if action == "navigate_to":
                success = await self.automation.navigate_to(kwargs["url"])
                return "done" if success else "failed"
            
            elif action == "go_back":
                success = await self.automation.go_back()
                return "done" if success else "failed"
            
            elif action == "go_forward":
                success = await self.automation.go_forward()
                return "done" if success else "failed"
            
            elif action == "reload":
                success = await self.automation.reload()
                return "done" if success else "failed"
            
            elif action == "scroll_down":
                pixels = kwargs.get("pixels", 100)
                success = await self.automation.scroll_down(pixels)
                return "done" if success else "failed"
            
            elif action == "scroll_up":
                pixels = kwargs.get("pixels", 100)
                success = await self.automation.scroll_up(pixels)
                return "done" if success else "failed"
            
            elif action == "start_auto_scroll":
                direction = 1 if kwargs.get("direction", "down").lower() == "down" else -1
                speed = kwargs.get("speed", 1.0)
                result = await self.automation.start_auto_scroll(direction, speed)
                return result
            
            elif action == "stop_auto_scroll":
                result = await self.automation.stop_auto_scroll()
                return result
            
            elif action == "click_at":
                success = await self.automation.click_at(kwargs["x"], kwargs["y"])
                return "done" if success else "failed"
            
            elif action == "click_by_text":
                success = await self.automation.click_by_text(kwargs["text"])
                return "done" if success else "failed"
            
            elif action == "fill_input":
                success = await self.automation.fill_input(kwargs["selector"], kwargs["value"])
                return "done" if success else "failed"
            
            elif action == "select_option":
                success = await self.automation.select_option(kwargs["selector"], kwargs["value"])
                return "done" if success else "failed"
            
            elif action == "list_input_fields":
                fields = await self.automation.list_input_fields()
                if fields:
                    field_info = []
                    for field in fields:
                        info = f"- Type: {field['type']}"
                        if field['name']:
                            info += f", Name: {field['name']}"
                        if field['id']:
                            info += f", ID: {field['id']}"
                        if field['placeholder']:
                            info += f", Placeholder: {field['placeholder']}"
                        if field['label']:
                            info += f", Label: {field['label']}"
                        field_info.append(info)
                    return "Input fields on the page:\n" + "\n".join(field_info)
                return "No input fields found on the page."
            
            elif action == "read_page_content":
                content = await self.automation.read_page_content()
                if content:
                    return f"Page content:\n{content}"
                return "No content found on the page."
            
            elif action == "get_page_title":
                title = await self.automation.get_page_title()
                if title:
                    return f"The page title is: {title}"
                return "No title found for the current page."
            
            elif action == "scroll_to_section":
                success = await self.automation.scroll_to_section(kwargs["text"])
                return "done" if success else "failed"
            
            elif action == "press_enter":
                success = await self.automation.press_enter()
                return "done" if success else "failed"
            
            elif action == "list_tabs":
                return await self.list_tabs()
            
            elif action == "switch_tab":
                tab_index = kwargs.get("tab_index", 1)
                return await self.switch_tab(tab_index)
            
            elif action == "new_tab":
                url = kwargs.get("url")
                return await self.new_tab(url)
            
            elif action == "close_tab":
                tab_index = kwargs.get("tab_index", 1)
                return await self.close_tab(tab_index)
            
            else:
                return f"Unknown action: {action}"

            # Check if we need to recover the browser
            if not success and not await self.check_and_recover():
                return "The browser has crashed. Please ask me to reopen the browser."

        except Exception as e:
            logger.error(f"Error performing action {action}: {e}")
            return "failed"

    def _on_new_page(self, page):
        """Handler for when a new page/tab is opened automatically."""
        try:
            if not getattr(self, '_creating_manual_tab', False) and not getattr(self, '_initializing_browser', False):
                self.pages.append(page)
                logger.info(f"Automatic new tab detected. Total tabs: {len(self.pages)}")
                self.pending_new_tab_notification = len(self.pages)
                logger.info(f"Set pending_new_tab_notification to: {self.pending_new_tab_notification}")
            else:
                logger.info(f"Manual tab creation detected, not triggering notification")
        except Exception as e:
            logger.error(f"Error handling new page: {e}")

    async def list_tabs(self) -> str:
        """Returns a list of all open tabs with their titles and URLs."""
        if not self.is_open or not self.pages:
            return "No tabs are currently open."
        
        try:
            tab_info = []
            for i, page in enumerate(self.pages):
                try:
                    title = await page.title()
                    url = page.url
                    active_marker = " (ACTIVE)" if i == self.active_tab_index else ""
                    tab_info.append(f"{i + 1}. {title} - {url}{active_marker}")
                except Exception as e:
                    tab_info.append(f"{i + 1}. [Error getting tab info] - {str(e)}")
            
            return "Open tabs:\n" + "\n".join(tab_info)
        except Exception as e:
            logger.error(f"Error listing tabs: {e}")
            return "Error retrieving tab information."

    async def switch_tab(self, tab_index: int) -> str:
        """Switches to the specified tab (1-based index)."""
        if not self.is_open or not self.pages:
            return "No tabs are currently open."
        
        zero_based_index = tab_index - 1
        
        if zero_based_index < 0 or zero_based_index >= len(self.pages):
            return f"Invalid tab number. Please choose between 1 and {len(self.pages)}."
        
        try:
            target_page = self.pages[zero_based_index]
            await target_page.evaluate("1 + 1")
            
            self.page = target_page
            self.active_tab_index = zero_based_index
            
            if self.automation:
                self.automation.page = self.page
            
            self.last_screenshot = None
            self.last_url = None
            self.last_content_hash = None
            self.last_update_time = 0
            
            title = await self.page.title()
            return f"Switched to tab {tab_index}: {title}"
            
        except Exception as e:
            logger.error(f"Error switching to tab {tab_index}: {e}")
            self.pages.pop(zero_based_index)
            if self.active_tab_index >= len(self.pages):
                self.active_tab_index = max(0, len(self.pages) - 1)
            return f"Tab {tab_index} is no longer available and has been removed."

    async def new_tab(self, url: str = None) -> str:
        """Creates a new tab and optionally navigates to a URL."""
        if not self.is_open or not self.context:
            return "Browser is not open. Please open it first."
        
        try:
            self._creating_manual_tab = True
            
            new_page = await self.context.new_page()
            self.pages.append(new_page)
            
            self.page = new_page
            self.active_tab_index = len(self.pages) - 1
            
            if self.automation:
                self.automation.page = self.page
            
            self.last_screenshot = None
            self.last_url = None
            self.last_content_hash = None
            self.last_update_time = 0
            
            if url:
                success = await self.automation.navigate_to(url)
                if success:
                    return f"Created new tab and navigated to {url}"
                else:
                    return f"Created new tab but failed to navigate to {url}"
            else:
                return f"Created new tab {len(self.pages)}"
                
        except Exception as e:
            logger.error(f"Error creating new tab: {e}")
            return "Failed to create new tab."
        finally:
            self._creating_manual_tab = False

    async def close_tab(self, tab_index: int) -> str:
        """Closes the specified tab (1-based index)."""
        if not self.is_open or not self.pages:
            return "No tabs are currently open."
        
        if len(self.pages) == 1:
            return "Cannot close the last remaining tab. Use 'close browser' instead."
        
        zero_based_index = tab_index - 1
        
        if zero_based_index < 0 or zero_based_index >= len(self.pages):
            return f"Invalid tab number. Please choose between 1 and {len(self.pages)}."
        
        try:
            page_to_close = self.pages[zero_based_index]
            title = await page_to_close.title()
            
            await page_to_close.close()
            self.pages.pop(zero_based_index)
            
            if zero_based_index == self.active_tab_index:
                self.active_tab_index = max(0, zero_based_index - 1)
                self.page = self.pages[self.active_tab_index]
                
                if self.automation:
                    self.automation.page = self.page
                
                self.last_screenshot = None
                self.last_url = None
                self.last_content_hash = None
                self.last_update_time = 0
                
            elif zero_based_index < self.active_tab_index:
                self.active_tab_index -= 1
            
            return f"Closed tab: {title}"
            
        except Exception as e:
            logger.error(f"Error closing tab {tab_index}: {e}")
            return f"Failed to close tab {tab_index}."

    async def check_new_tab_notification(self) -> str:
        """Checks if there's a pending new tab notification and returns appropriate message."""
        logger.info(f"Checking new tab notification. pending_new_tab_notification: {self.pending_new_tab_notification}")
        if self.pending_new_tab_notification is not None:
            tab_number = self.pending_new_tab_notification
            self.pending_new_tab_notification = None
            logger.info(f"Processing notification for tab {tab_number}")
            
            try:
                new_tab_page = self.pages[tab_number - 1]
                title = await new_tab_page.title()
                message = f"A new tab was automatically opened: Tab {tab_number} - {title}. Would you like me to switch to it? Just say 'switch to tab {tab_number}' or 'yes'."
                logger.info(f"Generated notification message: {message}")
                return message
            except Exception as e:
                logger.error(f"Error getting new tab info: {e}")
                message = f"A new tab was automatically opened (Tab {tab_number}). Would you like me to switch to it? Just say 'switch to tab {tab_number}' or 'yes'."
                logger.info(f"Generated fallback notification message: {message}")
                return message
        
        logger.info("No pending new tab notification")
        return None              