"""Constants for gtasks."""
# Base component constants
DOMAIN = "gtasks"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
PLATFORMS = ["sensor"]
REQUIRED_FILES = [
    ".translations/en.json",
    "const.py",
    "config_flow.py",
    "manifest.json",
    "sensor.py",
    "services.yaml",
]
ISSUE_URL = "https://github.com/BlueBlueBlob/gtasks/issues"
ATTRIBUTION = "Data from this is provided by gtasks."

# Icons
ICON = "mdi:check-bold"

# Device classes


# Configuration
CONF_BINARY_SENSOR = "binary_sensor"
CONF_SENSOR = "sensor"
CONF_NAME = "name"
CONF_CREDENTIALS_LOCATION = "credentials_location"
CONF_DEFAULT_LIST = "default_list"

# Defaults
DEFAULT_NAME = DOMAIN

#Services attributes
ATTR_TASK_TITLE = "task_title"
ATTR_DUE_DATE = "due_date"
ATTR_LIST_TITLE = "list_title"

#Services names
SERVICE_NEW_TASK = "new_task"
SERVICE_NEW_LIST = "new_list"
SERVICE_COMPLETE_TASK = "complete_task"

