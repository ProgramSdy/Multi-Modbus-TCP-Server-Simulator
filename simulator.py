import asyncio

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusDeviceContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer
from pymodbus import ModbusDeviceIdentification
import logging

# Disable spammy pymodbus logging (optional)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("multi-modbus")


# -----------------------------------------------------
# Build a device context (4 blocks, each size=100)
# -----------------------------------------------------
def build_device():
    """Create a ModbusDeviceContext with 4 blocks (co, di, hr, ir)."""

    # Coils: 100 bits, default False
    co_block = ModbusSequentialDataBlock(0, [0] * 100)

    # Discrete Inputs: 100 bits, default False
    di_block = ModbusSequentialDataBlock(0, [0] * 100)

    # Holding registers: 100 registers, default 0
    hr_block = ModbusSequentialDataBlock(0, [0] * 100)

    # Input registers: 100 registers, default 0
    ir_block = ModbusSequentialDataBlock(0, [0] * 100)

    device_context = ModbusDeviceContext(
        di=di_block,
        co=co_block,
        hr=hr_block,
        ir=ir_block,
    )

    return device_context


# -----------------------------------------------------
# Build ModbusServerContext (single-device, unit-id=1)
# -----------------------------------------------------
def build_context():
    return ModbusServerContext(
        devices={1: build_device()},  # only device 1
        single=False,  # must be False when using dict
    )


# -----------------------------------------------------
# Start a single async server on one IP
# -----------------------------------------------------
async def start_single_server(ip, server_index):
    context = build_context()
    asyncio.create_task(register_updater(context, ip, server_index))

    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "MultiModbusSim",
            "ProductCode": "SIM",
            "ProductName": "Multi-IP Modbus TCP Simulator",
            "ModelName": "AsyncModbusServer",
            "MajorMinorRevision": "1.0",
        }
    )

    log.info(f"[START] Modbus TCP server {server_index} @ {ip}:502")

    await StartAsyncTcpServer(
        context=context,
        identity=identity,
        address=(ip, 502),
    )

# -----------------------------------------------------
# Updater register value
# -----------------------------------------------------
async def register_updater(context, ip, server_index):
    func_code = 3          # holding registers
    address = 0            # HR[0]
    count = 1              # just one register

    while True:
        await asyncio.sleep(1)
        unit_id = 1
        
        try:
            # read current value
            values = context[unit_id].getValues(func_code, address, count=count)
            current = values[0]

            # increment
            new_value = (current + 1) % 10000

            # write new value
            context[unit_id].setValues(func_code, address, [new_value])

            print(f"[Server {server_index}] [Address: {ip}] [Unit {unit_id}] HR[0] = {new_value}")

        except Exception as e:
            print(f"[Server {server_index}] [Address: {ip}] [Unit {unit_id}] ERROR: {e}")


# -----------------------------------------------------
# Launch all servers concurrently
# -----------------------------------------------------
async def main():
    # Try to load Pi-specific config
    try:
        from local_config import PI_IP_LIST
        ips = PI_IP_LIST
        print("Using Pi local IP configuration.")
    except ImportError:
        # Default for laptop
        ips = [f"172.16.1.{i}" for i in range(201, 211)]
        print("Using default laptop IP configuration.")

    log.info("Launching all Modbus servers...")

    tasks = []
    for idx, ip in enumerate(ips, start=1):
        tasks.append(asyncio.create_task(start_single_server(ip, idx)))

    log.info("All servers started. Running forever...")

    # Run servers forever
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
