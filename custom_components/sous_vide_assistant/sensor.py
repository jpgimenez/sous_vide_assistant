from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from .const import DOMAIN, TARGET_TEMP_SENSOR, TIME_REMAINING_SENSOR
import openai
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    api_key = entry.data["openai_api_key"]
    model = entry.data.get("model", "gpt-4")
    openai.api_key = api_key

    guess_sensor = SousVideGuessSensor(hass, model)
    icon_sensor = SousVideIconSensor(hass, model)
    async_add_entities([guess_sensor, icon_sensor])

    @callback
    async def infer_dish(event):
        temp = hass.states.get(TARGET_TEMP_SENSOR)
        time = hass.states.get(TIME_REMAINING_SENSOR)

        if not temp or not time:
            return

        prompt = (
            f"Dado un baño sous vide con temperatura de {temp.state}°C y "
            f"{int(int(time.state)/60)} minutos restantes, ¿qué plato se está cocinando?"
            " Respondé solo el nombre del plato. Usá emojis si corresponde."
        )

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30,
            )
            dish = response.choices[0].message.content.strip()
            guess_sensor.set_value(dish)
            icon_sensor.set_value(dish)
        except Exception as e:
            _LOGGER.error("Error al inferir plato sous vide: %s", e)

    async_track_state_change_event(hass, [TARGET_TEMP_SENSOR, TIME_REMAINING_SENSOR], infer_dish)

class SousVideGuessSensor(Entity):
    def __init__(self, hass, model):
        self._attr_name = "Sous Vide Dish Guess"
        self._attr_unique_id = "sous_vide_dish_guess"
        self._state = None

    def set_value(self, value):
        self._state = value
        self.schedule_update_ha_state()

    @property
    def state(self):
        return self._state

class SousVideIconSensor(Entity):
    def __init__(self, hass, model):
        self._attr_name = "Sous Vide Icon Guess"
        self._attr_unique_id = "sous_vide_icon_guess"
        self._state = None

    def set_value(self, value):
        self._state = self._extract_emoji(value)
        self.schedule_update_ha_state()

    @property
    def state(self):
        return self._state

    def _extract_emoji(self, text):
        return "".join([char for char in text if char in ("🍳", "🥩", "🐟", "🍗", "🦐", "🐖", "🐑", "🐄")])