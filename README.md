## Gtasks-Ha a Google Tasks Custom Component for Home Assistant
Forked from original repo by [@BlueBlueBlob](https://github.com/blueblueblob)

You will probably also want to install the lovelace card to make best use of this. [lovelace-gtasks-card](https://github.com/myntath/lovelace-gtasks-card)

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `gtasks`.
4. Download _all_ the files from the `custom_components/gtasks/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Setup your configuration.yaml file, see exemple below
7. Restart Home Assistant
8. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Google Tasks"

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/gtasks/.translations/en.json
custom_components/gtasks/__init__.py
custom_components/gtasks/binary_sensor.py
custom_components/gtasks/config_flow.py
custom_components/gtasks/const.py
custom_components/gtasks/manifest.json
custom_components/gtasks/sensor.py
```

## Example configuration.yaml

```yaml
gtasks:
  credentials_location: /path/credentials.json
  default_list: 'My task list'
  force_login: false
  token_location: /config/token.pickle
```

