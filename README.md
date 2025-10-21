# netbox-dev

A pre-configured environment to quickly develop against Netbox locally.

## Quickstart

To get up and running, run the following:

```bash
# Start databases
docker compose up -d

# On first start
ln -s $PWD/configuration.py netbox/netbox/netbox/configuration.py
just run-netbox makemigrate
just run-netbox createsuperuser

# For every new shell: start the Netbox server
export `grep -ve "^#" env/netbox.env | xargs`
just run-netbox runserver
```

### Starting Netbox Dependencies

Netbox relies on a Postgres database, Redis Store, and a Redis Cache.
These can all be spun up with docker compose:

```bash
docker compose up -d
```

### Starting Netbox

#### First Start

All of Netbox's settings are configured through `configuration.py`.
We provide a reference configuration at the top-level of this repository.
Symlink this to the expected directory:

```bash
ln -s $PWD/configuration.py netbox/netbox/netbox/configuration.py
```

On first start, the Netbox database will need to be bootstrapped with the database
migrations and superuser credentials.
You can access django project management script using the provided `justfile`:

```bash
just run-netbox makemigrate
just run-netbox createsuperuser
```

#### Running the Netbox server

The developer environment variables are given in `env/netbox.env`.
Source this environment:

```bash
export `grep -ve "^#" env/netbox.env | xargs`
just run-netbox runserver
```

## Plugins

### Open-Source

Plugins can be run from source by installing them in editable mode.
To get started, clone the desired plugin (preferably to a close-by directory, like `plugins/`) and run the following command in your virtualenv:

```bash
pip install -e plugins/{plugin_name}
```

### Custom Plugins

Custom plugins are identical to open-source plugins, except for the fact that they may be actively developed against.
To get started with a new plugin, run the following in your virtual environment:

```bash
just new-plugin
pip install -e plugins/{{plugin_name}}

# add the plugin to PLUGINS in configuration.py
just run-netbox makemigrate
```

#### References

- [Netbox Plugin Development Docs](https://netboxlabs.com/docs/netbox/plugins/development/)
- [Netbox Plugin Development Tutorial](https://github.com/netbox-community/netbox-plugin-tutorial)
- [Netbox Plugin Demo](https://github.com/netbox-community/netbox-plugin-demo)

### Debugging

Netbox is a Django app, and Django has a large amount of developer tooling built around it.
This repository has a preconfigured `launch.json`, which allows you to run a Python debugger (`debugpy`) against the Netbox source in VSCode (or any `launch.json`-compatible IDE).
Additionally, if you've installed plugins locally (either from source or custom-developed), then you will be able to debug this source as well.
