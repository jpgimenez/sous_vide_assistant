from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry):
    hass.async_create_task(
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )
    return True
