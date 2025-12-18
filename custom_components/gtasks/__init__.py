"""
Component to integrate with gtasks.

For more details about this component, please refer to
https://github.com/BlueBlueBlob/gtasks
"""
import os
from datetime import timedelta, date, datetime
import unicodedata
import logging
import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.core import callback

from .gtasks_api import GtasksAPI

from integrationhelper.const import CC_STARTUP_VERSION

from .const import (
    CONF_BINARY_SENSOR,
    CONF_NAME,
    CONF_SENSOR,
    DEFAULT_NAME,
    DEFAULT_TOKEN_LOCATION,
    DEFAULT_CREDENTIALS_LOCATION,
    DOMAIN_DATA,
    DOMAIN,
    ISSUE_URL,
    REQUIRED_FILES,
    VERSION,
    CONF_CREDENTIALS_LOCATION,
    CONF_TOKEN_PATH,
    CONF_TASKS_LISTS,
    ATTR_TASK_TITLE,
    ATTR_TASKS_LIST,
    ATTR_DUE_DATE,
    SERVICE_NEW_TASK,
    SERVICE_COMPLETE_TASK,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

NEW_TASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TASK_TITLE): cv.string,
        vol.Required(ATTR_TASKS_LIST): cv.string,
        vol.Optional(ATTR_DUE_DATE): cv.date,
    }
)

COMPLETE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TASK_TITLE): cv.string,
        vol.Required(ATTR_TASKS_LIST): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_CREDENTIALS_LOCATION, default=DEFAULT_CREDENTIALS_LOCATION): cv.isfile,
                vol.Required(CONF_TASKS_LISTS): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_TOKEN_PATH, default=DEFAULT_TOKEN_LOCATION): cv.isdir,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up this component using YAML."""
    # Create DATA dict
    hass.data[DOMAIN_DATA] = {}
    _LOGGER.debug('setup_config_data: %s', config)
    return True


def add_task_helper(client, list_id, task):
    """Async helper function for adding task."""
    client._service.tasks().insert(tasklist=list_id, body=task).execute()


def complete_task_helper(service, client, list_id, task_name):
    """Async helper function for completing task."""
    task_id = client.gapi.get_task_id(list_id, task_name)
    task_to_complete = service.tasks().get(tasklist=list_id, task=task_id).execute()
    task_to_complete['status'] = 'completed'
    service.tasks().update(tasklist=list_id, task=task_to_complete['id'], body=task_to_complete).execute()


async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""

    conf = hass.data.get(DOMAIN_DATA)
    if config_entry.source == config_entries.SOURCE_IMPORT:
        if conf is None:
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
        return False

    # Print startup message
    _LOGGER.debug(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )

    # Get "global" configuration.
    creds = config_entry.data.get("creds")
    token_file = config_entry.data.get("token_file")
    tasks_lists = config_entry.data.get("tasks_lists")

    # Configure the client.
    hass.data[DOMAIN_DATA]["creds"] = creds
    hass.data[DOMAIN_DATA]["token_file"] = token_file
    hass.data[DOMAIN_DATA]["tasks_lists"] = tasks_lists
    try:
        gapi = await hass.async_add_executor_job(GtasksAPI, creds, token_file)
        _LOGGER.info('gapi : %s', gapi)
    except Exception as error:
        _LOGGER.exception(error)
        return False
    try:
        hass.data[DOMAIN_DATA]["gapi"] = gapi
        hass.data[DOMAIN_DATA]["client"] = await hass.async_add_executor_job(GtasksData, hass, gapi, tasks_lists)
        _LOGGER.info('client : %s', hass.data[DOMAIN_DATA]["client"])
    except Exception as error:
        _LOGGER.exception(error)
        return False
    _LOGGER.info('data : %s', hass.data[DOMAIN_DATA])
    # Add sensor and binary_sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setups(config_entry, ["binary_sensor","sensor"])
    )

    @callback
    async def new_task(call):
        title = call.data.get(ATTR_TASK_TITLE)
        task_list = call.data.get(ATTR_TASKS_LIST)
        due_date = call.data.get(ATTR_DUE_DATE, None)
        client = hass.data[DOMAIN_DATA]["client"]
        list_id = client.tasks_lists_id[task_list]
        task = {}
        task['title'] = title
        if due_date:
            task['due'] = datetime.strftime(due_date, '%Y-%m-%dT00:00:00.000Z')

        _LOGGER.debug('task : %s', task)
        try:
            task_list = unicodedata.normalize('NFKD', task_list).encode('ascii', 'ignore').decode("utf-8").translate({ord(c): None for c in '!@#$'})
            await hass.async_add_executor_job(add_task_helper, client, list_id, task)
        except Exception as error:
            _LOGGER.exception(error)

    @callback
    async def complete_task(call):
        task_name = call.data.get(ATTR_TASK_TITLE)
        task_list = call.data.get(ATTR_TASKS_LIST)
        client = hass.data[DOMAIN_DATA]["client"]
        list_id = client.tasks_lists_id[task_list]
        service = client._service
        try:
            task_list = unicodedata.normalize('NFKD', task_list).encode('ascii', 'ignore').decode("utf-8").translate({ord(c): None for c in '!@#$'})
            await hass.async_add_executor_job(complete_task_helper, service, client, list_id, task_name)
        except Exception as error:
            _LOGGER.exception(error)

    # Register "new_task" service
    hass.services.async_register(
        DOMAIN, SERVICE_NEW_TASK, new_task, schema=NEW_TASK_SCHEMA
    )

    # Register "comple_task" service
    hass.services.async_register(
        DOMAIN, SERVICE_COMPLETE_TASK, complete_task, schema=COMPLETE_TASK_SCHEMA
    )

    return True


class GtasksData:
    """This class handle communication and stores the data."""

    def __init__(self, hass, gapi, tasks_lists):
        """Initialize the class."""
        self.hass = hass
        self.gapi = gapi
        self._service = self.gapi.service
        self.tasks_lists_id = {}
        _LOGGER.debug('gapi : %s , service : %s', self.gapi, self._service)
        self.tasks_lists = tasks_lists
        for task_list in tasks_lists:
            self.tasks_lists_id[task_list] = self.gapi.get_taskslist_id(task_list)
        _LOGGER.debug('task list id : %s', self.tasks_lists_id)

    async def update_data(self, list_name):
        """Runs the update of the main sensor."""
        request_sensor = self._service.tasks().list(tasklist=self.tasks_lists_id[list_name], showCompleted=False, maxResults=100)
        tag_sensor = list_name + CONF_SENSOR + "_data"
        try:
            tasks_list_sensor = await self.hass.async_add_executor_job(request_sensor.execute)
            self.hass.data[DOMAIN_DATA][tag_sensor] = tasks_list_sensor.get('items', None)
            _LOGGER.debug('tasks_list : %s', tasks_list_sensor)
        except Exception as error:
            _LOGGER.exception(error)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update_binary_data(self, list_name):
        """Runs the update of the binary sensor."""
        today = date.today().strftime('%Y-%m-%dT00:00:00.000Z')
        request_binary_sensor = self._service.tasks().list(tasklist=self.tasks_lists_id[list_name], showCompleted=False, dueMax=today, maxResults=100)
        tag_binary = list_name + CONF_BINARY_SENSOR + "_data"
        try:
            tasks_list_binary = await self.hass.async_add_executor_job(request_binary_sensor.execute)
            self.hass.data[DOMAIN_DATA][tag_binary] = tasks_list_binary.get('items', None)
            _LOGGER.debug('tasks_list_binary : %s', tasks_list_binary)
        except Exception as error:
            _LOGGER.exception(error)


async def check_files(hass):
    """Return bool that indicates if all files are present."""
    # Verify that the user downloaded all files.
    base = f"{hass.config.path()}/custom_components/{DOMAIN}/"
    missing = []
    for file in REQUIRED_FILES:
        fullpath = f"{base}{file}"
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        _LOGGER.critical("The following files are missing: %s", str(missing))
        returnvalue = False
    else:
        returnvalue = True

    return returnvalue


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, "binary_sensor"
        )

    except ValueError as error:
        _LOGGER.error(error)
    _LOGGER.info(
            "Successfully removed binary_sensor from the gtasks integration"
        )
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")

    except ValueError as error:
        _LOGGER.error(error)
    _LOGGER.info("Successfully removed sensor from the gtasks integration")
