import re
import os
import logging
import requests
from pathlib import Path
from typing import AsyncIterable, Optional, List, Dict
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero
from livekit.agents.llm import function_tool

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

HOMEAUTOMAITON_TOKEN = os.getenv("HOMEAUTOMAITON_TOKEN")
HOMEAUTOMATION_URL = os.getenv("HOMEAUTOMATION_URL", "http://localhost:8123")

class HomeAgent(Agent):  
    def __init__(self) -> None:  
        super().__init__(  
            instructions="""  
                You are a helpful agent that can control home automation devices.
                You can list available devices and control them by turning them on or off.
                When asked about devices, first list what's available and then help control them.
            """,  
            stt=deepgram.STT(),  
            llm=openai.LLM(),  
            tts=openai.TTS(),  
            vad=silero.VAD.load()  
        )  
        self.hot_word_detected = False  
        self.hot_word = "hey casa"  
      
    async def on_enter(self):  
        logger.info(f"Waiting for hot word: '{self.hot_word}'")  
        self.session.say(f"Waiting for hot word: {self.hot_word}")

      
    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:  
        parent_stream = super().stt_node(text, model_settings)  
          
        if parent_stream is None:  
            return None  
              
        async def process_stream():  
            async for event in parent_stream:  
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:  
                    transcript = event.alternatives[0].text.lower()  
                    logger.info(f"Received transcript: '{transcript}'")
                    
                    # Clean the transcript by removing punctuation and extra spaces
                    cleaned_transcript = re.sub(r'[^\w\s]', '', transcript)  # Remove punctuation
                    cleaned_transcript = ' '.join(cleaned_transcript.split())  # Normalize spaces
                    logger.info(f"Cleaned transcript: '{cleaned_transcript}'")
                      
                    if not self.hot_word_detected:  
                        # Check for hot word in cleaned transcript
                        if self.hot_word in cleaned_transcript:  
                            logger.info(f"Hot word detected: '{self.hot_word}'")  
                            self.hot_word_detected = True  
                              
                            # Extract content after the hot word  
                            content_after_hot_word = cleaned_transcript.split(self.hot_word, 1)[-1].strip()  
                            if content_after_hot_word:  
                                # Replace the transcript with only the content after the hot word  
                                event.alternatives[0].text = content_after_hot_word  
                                yield event  
                        # If hot word not detected, don't yield the event (discard input)  
                    else:  
                        # Hot word already detected, process this utterance  
                        yield event  
                          
                        # After end of utterance, reset to look for hot word again  
                        if str(event.type) == "SpeechEventType.END_OF_SPEECH":  
                            logger.info("End of utterance detected, waiting for hot word again")  
                            self.hot_word_detected = False  
                elif self.hot_word_detected:  
                    # Pass through other event types (like START_OF_SPEECH) when hot word is active  
                    yield event  
                  
        return process_stream()  
    

    @function_tool()
    async def list_devices(self) -> List[Dict[str, str]]:
        """List all available devices in the home automation system."""
        if not HOMEAUTOMAITON_TOKEN:
            self.session.say("Sorry, I can't list devices right now - the token is not configured")
            return []

        url = f"{HOMEAUTOMATION_URL}/api/states"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                devices = response.json()
                # Filter for relevant devices (lights, switches, etc.)
                relevant_devices = []
                for device in devices:
                    entity_id = device['entity_id']
                    if any(entity_id.startswith(prefix) for prefix in ['light.', 'switch.', 'binary_sensor.']):
                        relevant_devices.append({
                            'entity_id': entity_id,
                            'state': device['state'],
                            'name': device['attributes'].get('friendly_name', 'Unnamed')
                        })
                return relevant_devices
            else:
                self.session.say("Sorry, I couldn't get the list of devices")
                return []
        except requests.exceptions.RequestException:
            self.session.say("Sorry, I'm having trouble connecting to the home automation system")
            return []

    @function_tool()
    async def control_device(self, entity_id: str, state: str) -> None:
        """Turn a device on or off.
        
        Args:
            entity_id: The ID of the device to control (e.g. 'light.kitchen')
            state: Either 'on' or 'off'
        """
        if not HOMEAUTOMAITON_TOKEN:
            self.session.say("Sorry, I can't control devices right now - the token is not configured")
            return

        if state not in ['on', 'off']:
            self.session.say("Sorry, I can only turn devices on or off")
            return

        service = "turn_on" if state == "on" else "turn_off"
        domain = entity_id.split(".")[0]
        url = f"{HOMEAUTOMATION_URL}/api/services/{domain}/{service}"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        
        try:
            response = requests.post(url, headers=headers, json={"entity_id": entity_id}, timeout=10)
            if response.status_code in (200, 201):
                self.session.say(f"Ok, I've turned {entity_id} {state}")
            else:
                self.session.say(f"Sorry, I couldn't control {entity_id}")
        except requests.exceptions.RequestException:
            self.session.say("Sorry, I'm having trouble connecting to the home automation system")
        
        return None

    @function_tool()
    async def get_energy_usage(self) -> Dict[str, float]:
        """Get current energy usage information."""
        if not HOMEAUTOMAITON_TOKEN:
            self.session.say("Sorry, I can't get energy usage right now - the token is not configured")
            return {}

        url = f"{HOMEAUTOMATION_URL}/api/states"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                states = response.json()
                energy_data = {
                    'current_usage': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.energy_usage')),
                    'daily_usage': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.daily_usage')),
                    'monthly_usage': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.monthly_usage')),
                    'yearly_usage': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.yearly_usage'))
                }
                return energy_data
            else:
                self.session.say("Sorry, I couldn't get the energy usage data")
                return {}
        except requests.exceptions.RequestException:
            self.session.say("Sorry, I'm having trouble connecting to the home automation system")
            return {}

    @function_tool()
    async def get_temperatures(self) -> Dict[str, float]:
        """Get temperature readings from all sensors."""
        if not HOMEAUTOMAITON_TOKEN:
            self.session.say("Sorry, I can't get temperature readings right now - the token is not configured")
            return {}

        url = f"{HOMEAUTOMATION_URL}/api/states"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                states = response.json()
                temp_data = {
                    'living_room': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.livingroom_thermostat_air_temperature')),
                    'bathroom': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.bathroom_air_temperature')),
                    'kitchen': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.kitchen_flood_sensor_air_temperature')),
                    'tool_room': float(next(s['state'] for s in states if s['entity_id'] == 'sensor.tool_room_temperature'))
                }
                return temp_data
            else:
                self.session.say("Sorry, I couldn't get the temperature readings")
                return {}
        except requests.exceptions.RequestException:
            self.session.say("Sorry, I'm having trouble connecting to the home automation system")
            return {}

    @function_tool()
    async def get_thermostat_info(self, entity_id: str) -> Dict[str, str]:
        """Get current thermostat state and settings.
        
        Args:
            entity_id: The ID of the thermostat to query (e.g. 'climate.livingroom_thermostat')
        """
        if not HOMEAUTOMAITON_TOKEN:
            self.session.say("Sorry, I can't get thermostat information right now - the token is not configured")
            return {}

        url = f"{HOMEAUTOMATION_URL}/api/states/{entity_id}"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                thermostat = response.json()
                return {
                    'mode': thermostat['state'],
                    'current_temperature': thermostat['attributes']['current_temperature'],
                    'target_temperature': thermostat['attributes']['temperature'],
                    'humidity': thermostat['attributes']['current_humidity']
                }
            else:
                self.session.say("Sorry, I couldn't get the thermostat information")
                return {}
        except requests.exceptions.RequestException:
            self.session.say("Sorry, I'm having trouble connecting to the home automation system")
            return {}

    @function_tool()
    async def set_thermostat(self, entity_id: str, mode: str, temperature: float) -> None:
        """Set thermostat mode and temperature.
        
        Args:
            entity_id: The ID of the thermostat to control (e.g. 'climate.livingroom_thermostat')
            mode: Either 'heat', 'cool', or 'off'
            temperature: Temperature to set (in Fahrenheit)
        """
        if not HOMEAUTOMAITON_TOKEN:
            self.session.say("Sorry, I can't control the thermostat right now - the token is not configured")
            return

        if mode not in ['heat', 'cool', 'off']:
            self.session.say("Sorry, I can only set the thermostat to heat, cool, or off")
            return

        url = f"{HOMEAUTOMATION_URL}/api/services/climate/set_hvac_mode"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        data = {"entity_id": entity_id, "hvac_mode": mode}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code in (200, 201):
                temp_url = f"{HOMEAUTOMATION_URL}/api/services/climate/set_temperature"
                temp_data = {
                    "entity_id": entity_id,
                    "temperature": temperature
                }
                temp_response = requests.post(temp_url, headers=headers, json=temp_data, timeout=10)
                if temp_response.status_code in (200, 201):
                    self.session.say(f"Ok, I've set the thermostat to {mode} mode and temperature to {temperature}°F")
                else:
                    self.session.say(f"Ok, I've set the thermostat to {mode} mode, but couldn't set the temperature")
            else:
                self.session.say("Sorry, I couldn't control the thermostat")
        except requests.exceptions.RequestException:
            self.session.say("Sorry, I'm having trouble connecting to the home automation system")

    @function_tool()
    async def list_thermostats(self) -> List[Dict[str, str]]:
        """List all available thermostats in the home automation system."""
        if not HOMEAUTOMAITON_TOKEN:
            self.session.say("Sorry, I can't list thermostats right now - the token is not configured")
            return []

        url = f"{HOMEAUTOMATION_URL}/api/states"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                states = response.json()
                thermostats = []
                for state in states:
                    if state['entity_id'].startswith('climate.'):
                        thermostats.append({
                            'entity_id': state['entity_id'],
                            'name': state['attributes'].get('friendly_name', 'Unnamed Thermostat'),
                            'current_temperature': state['attributes'].get('current_temperature', 'Unknown'),
                            'mode': state['state']
                        })
                return thermostats
            else:
                self.session.say("Sorry, I couldn't get the list of thermostats")
                return []
        except requests.exceptions.RequestException:
            self.session.say("Sorry, I'm having trouble connecting to the home automation system")
            return []

    async def on_user_turn_completed(self, chat_ctx, new_message=None):  
        # Only generate a reply if the hot word was detected  
        if self.hot_word_detected:  
            # Let the default behavior happen  
            result = await super().on_user_turn_completed(chat_ctx, new_message)
            # Reset the hot word detection after processing the response
            self.hot_word_detected = False
            logger.info("Response completed, waiting for hot word again")
            return result
        # Otherwise, don't generate a reply  
        from livekit.agents.voice.agent_activity import StopResponse  
        raise StopResponse()

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()

    await session.start(
        agent=HomeAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))