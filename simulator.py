from pymodbus.server import ModbusTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from threading import Thread

def start_server(ip):
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [0] * 100)
    )
    context = ModbusServerContext(slaves=store, single=True)

    print(f"[OK] Starting Modbus TCP server at {ip}:502 ...")
    server = ModbusTcpServer(
        context,
        address=(ip, 502),
        ipv6=False    # IMPORTANT FIX FOR WINDOWS
    )
    server.serve_forever()


if __name__ == "__main__":
    ips = [f"172.16.1.{i}" for i in range(201, 210)]

    print("Launching Modbus servers, please wait...")

    for ip in ips:
        Thread(target=start_server, args=(ip,), daemon=True).start()

    print("All servers running. Press Enter to stop.")
    input()
