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
# Configuration
# -----------------------------------------------------
try:
    from local_config import (
        PI_IP_LIST,
        PORT,
        DEVICE_ID,
        HR_ADDRESS,
    )

    ips = PI_IP_LIST

    print("Using Pi local configuration.")

except ImportError:

    # Default laptop configuration
    SERVER_HOST_ID_Start = 201
    SERVER_HOST_ID_Finish = 221

    ips = [
        f"172.16.1.{i}"
        for i in range(SERVER_HOST_ID_Start, SERVER_HOST_ID_Finish)
    ]

    PORT = 502
    DEVICE_ID = 2
    HR_ADDRESS = 20

    print("Using default laptop configuration.")


SERVER_HOST_Qty = len(ips)

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
        devices={DEVICE_ID: build_device()},
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

    log.info(f"[START] Modbus TCP server {server_index} @ {ip}:{PORT}")

    await StartAsyncTcpServer(
        context=context,
        identity=identity,
        address=(ip, PORT),
    )

# -----------------------------------------------------
# Updater register value
# -----------------------------------------------------
async def register_updater(context, ip, server_index):
    func_code = 3          # holding registers
    address = HR_ADDRESS   # HR[HR_ADDRESS]
    count = 1              # just one register

    while True:
        await asyncio.sleep(1)
        unit_id = DEVICE_ID
        
        try:
            # read current value
            values = context[unit_id].getValues(func_code, address, count=count)
            current = values[0]

            # increment
            new_value = (current + 1) % 10000

            # write new value
            context[unit_id].setValues(func_code, address, [new_value])

            print(f"[Server {server_index}] [Address: {ip}] [Unit {unit_id}] HR[{address}] = {new_value}")

        except Exception as e:
            print(f"[Server {server_index}] [Address: {ip}] [Unit {unit_id}] ERROR: {e}")


# -----------------------------------------------------
# Launch all servers concurrently
# -----------------------------------------------------
async def main():

    log.info(f"Launching all {SERVER_HOST_Qty} Modbus servers...")

    tasks = []
    for idx, ip in enumerate(ips, start=1):
        tasks.append(asyncio.create_task(start_single_server(ip, idx)))

    log.info("All servers started. Running forever...")

    # Run servers forever
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
