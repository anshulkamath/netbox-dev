import pynetbox, os
import time
from netboxlabs.diode.sdk import DiodeClient
from netboxlabs.diode.sdk.ingester import (
    Device,
    Module,
    ModuleBay,
    ModuleType,
    Interface,
    IPAddress,
    Entity,
)

nb = pynetbox.api(os.getenv("NETBOX_ENDPOINT"), os.getenv("NETBOX_TOKEN"))
dc = DiodeClient(
    target=os.getenv("DIODE_ENDPOINT"), app_name="test", app_version="v0.0.1"
)


SITE = "Test Site"
MFCT = "Test Manufacturer"
DEVICE_TYPE = "Test Device Type"
DEVICE_ROLE = "Test Role"
IFACE_NAME = "eth0"
IFACE_TYPE = "100gbase-x-qsfpdd"
MODULE_TYPE = "Test Module Type"
MODULE_BAY = "Tray"


def get_netbox_info():
    print("Netbox Docker version: v4.3.7-3.3.0")
    print("Diode Version: v1.7.1")
    print("Diode Plugin version: netboxlabs-diode-netbox-plugin==1.3.1")
    print("Python Diode SDK version: netboxlabs-diode-sdk==1.4.0")
    print("-------------------")


def setup():
    site = nb.dcim.sites.get(name=SITE)
    if site == None:
        site = nb.dcim.sites.create(name=SITE, slug="test-site")
        print(f"Created site {site}")

    mfct = nb.dcim.manufacturers.get(name=MFCT)
    if mfct == None:
        mfct = nb.dcim.manufacturers.create(name=MFCT, slug="test-manufacturer")
        print(f"Created manufacturer {mfct}")

    dtype = nb.dcim.device_types.get(slug="test-device-type")
    if dtype == None:
        dtype = nb.dcim.device_types.create(
            model=DEVICE_TYPE,
            slug="test-device-type",
            manufacturer={"name": mfct["name"]},
            u_height=1,
        )
        print(f"Created device type {dtype}")

    drole = nb.dcim.device_roles.get(slug="test-role")
    if drole == None:
        drole = nb.dcim.device_roles.create(
            name=DEVICE_ROLE,
            slug="test-role",
        )
        print(f"Created device role {drole}")

    mbay = nb.dcim.module_bay_templates.get(device_type=dtype["id"], name=MODULE_BAY)
    if mbay == None:
        mbay = nb.dcim.module_bay_templates.create(
            device_type=dtype["id"], name=MODULE_BAY
        )
        print(f"Created module bay template {mbay} for device type {dtype}")

    iface = nb.dcim.interface_templates.get(device_type=dtype["id"], name=IFACE_NAME)
    if iface == None:
        iface = nb.dcim.interface_templates.create(
            device_type=dtype["id"], name=IFACE_NAME, type="100gbase-x-qsfpdd"
        )
        print(f"Created interface template {iface} for device type {dtype}")

    module = nb.dcim.module_types.get(model=MODULE_TYPE)
    if module == None:
        module = nb.dcim.module_types.create(
            model=MODULE_TYPE,
            manufacturer={"name": mfct["name"]},
        )
        print(f"Created module type {module}")


def instantiate_devices_with_modules():
    NITER = 1
    for i in range(NITER):
        device = Device(
            name=f"Device {i}",
            device_type=DEVICE_TYPE,
            role=DEVICE_ROLE,
            manufacturer=MFCT,
            site=SITE,
        )

        module = Module(
            device=device,
            module_bay=ModuleBay(
                device=device,
                name=MODULE_BAY,
            ),
            module_type=ModuleType(model=MODULE_TYPE, manufacturer=MFCT),
        )

        iface = Interface(
            device=device,
            type="400gbase-x-qsfpdd",
            name="eth0",
        )

        entities = [
            # Entity(device=device),
            # Entity(module=module),
            Entity(interface=iface),
        ]
        dc.ingest(entities=entities)


def instantiate_devices_with_ips():
    NITER = 3
    device = Device(
        name=f"Device 0",
        device_type=DEVICE_TYPE,
        role=DEVICE_ROLE,
        manufacturer=MFCT,
        site=SITE,
    )

    for _ in range(NITER):
        ip = IPAddress(
            device=device,
            address=f"192.168.1.1/32",
            assigned_object_interface=Interface(
                device=device,
                name=IFACE_NAME,
            ),
            vrf="mgmt",
        )

        entities = [Entity(device=device), Entity(ip_address=ip)]
        dc.ingest(entities=entities)


def print_duplicate_module_bays():
    # For all devices except the first, there are duplicate module bays
    NITER = 1
    for i in range(NITER):
        device_name = f"Device {i}"
        bays = list(nb.dcim.module_bays.filter(name=MODULE_BAY, device=device_name))
        print(f"There are {len(bays)} module bays found for device {device_name}")


def print_duplicate_ips():
    device_name = "Device 0"
    ips = list(nb.ipam.ip_addresses.filter(name=MODULE_BAY, device=device_name))
    unique = {(ip["address"], ip["vrf"]["name"]) for ip in ips}
    print(
        f"There are {len(ips)} IP addresses found for device {device_name} ({len(unique)} unique)"
    )


def main():
    get_netbox_info()

    setup()

    # Running this once will duplicate modules for all devices except the first
    instantiate_devices_with_modules()

    # Running this once will duplicate IPs
    # instantiate_devices_with_ips()

    # Give diode time to ingest
    print("Sleeping for 3 second to let diode ingest")
    time.sleep(3)

    # Print counts. Expect at most one module bay and IP per device
    # print_duplicate_module_bays()
    # print_duplicate_ips()


main()
