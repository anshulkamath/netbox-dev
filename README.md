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
