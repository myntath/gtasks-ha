"""Binary sensor platform for gtasks."""
import logging
from datetime import date, datetime
from uuid import getnode as get_mac
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import (
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN_DATA,
    DOMAIN,
    CONF_BINARY_SENSOR,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    tasks_lists = hass.data[DOMAIN_DATA]["tasks_lists"]
    for list_item in tasks_lists:
        async_add_devices([GtasksBinarySensor(hass, {}, list_item)], True)


class GtasksBinarySensor(BinarySensorEntity):
    """gtasks binary_sensor class."""

    def __init__(self, hass, config, list_item):
        self.hass = hass
        self.attr = {}
        self._status = False
        self._list = list_item
        self._name = f"{config.get('name', DEFAULT_NAME)}_{self._list}"
        self._unique_id = f"{get_mac()}-{CONF_BINARY_SENSOR}-{self._name}"

    async def async_update(self):
        """Update the binary_sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN_DATA]["client"].update_binary_data(self._list)

        # Get new data (if any)
        passed_list = self.hass.data[DOMAIN_DATA].get(
                        self._list + CONF_BINARY_SENSOR + "_data", None
                        )
        data = []
        # Check the data and update the value.
        if not passed_list or passed_list is None:
            self._status = False
        else:
            for task in passed_list:
                task_dict = {}
                task_dict['task_title'] = task['title']
                task_dict['due_date'] = datetime.strftime(datetime.strptime(task['due'],
                                                          '%Y-%m-%dT00:00:00.000Z').date(),
                                                          '%Y-%m-%d'
                                                         )
                tdelta = date.today() - datetime.strptime(task['due'],
                                                          '%Y-%m-%dT00:00:00.000Z'
                                                         ).date()
                task_dict['days_overdue'] = tdelta.days
                data.append(task_dict)
            self._status = True

        # Set/update attributes
        self.attr["attribution"] = ATTRIBUTION
        self.attr["tasks"] = data

    @property
    def unique_id(self):
        """Return a unique ID to use for this binary_sensor."""
        return self._unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN,'google')},
            "name": DOMAIN,
            "manufacturer": "Gtasks",
        }

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._status

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self.attr
