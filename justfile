set dotenv-load := true
set dotenv-path := 'env/netbox.env'

run-netbox *cmd:
  @test -n "$VIRTUAL_ENV"
  @python3 netbox/netbox/manage.py {{cmd}}

update-netbox-config:
  @vim netbox/netbox/netbox/configuration.py

# List all available databases in this repository
[group('database')]
list-databases:
  @echo "\nAvailable database databases: \n$(ls databases | xargs -I{} echo "  - {}")"

# Generate a database dump
[group('database')]
dump-database fname:
  @docker compose exec -T postgres pg_dump -U netbox -Fc netbox > databases/{{fname}}
  @echo "Generating dump in databases/{{fname}}"

# Load a dump into a database
[group('database')]
load-database fname:
  @echo "Loading database databases/{{fname}}. This may take a minute..."
  @cat databases/{{fname}} | docker compose exec -T postgres pg_restore -U netbox -d netbox --clean --if-exists > /dev/null 2>&1
  @echo "Successfully loaded database databases/{{fname}}"

# Destroy the netbox database
clean-netbox-database:
    @docker compose exec -it postgres psql -U netbox -c 'TRUNCATE dcim_rack CASCADE; TRUNCATE dcim_device CASCADE;'
