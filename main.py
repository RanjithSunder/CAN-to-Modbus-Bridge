import os
import time
import threading
import struct
import cantools
import can
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from threading import Event
from collections import defaultdict

# Constants
UNIT_ID = 1
CAN_TIMEOUT = 0.5  # seconds

# Per-message timeout tracking
last_received_time = defaultdict(lambda: 0)

# CAN to Modbus field mappings
MV_USER_MSG01_MAP = {
    "MV_001S_ModeActual": 0,
    "MV_003S_CurrentAvailable_A": 2,
    "MV_008S_AlarmState": 4,
    "MV_008S_Counter": 6,
    "MV_410S_RelayUserPrecharge_Close": 8,
    "MV_410S_RelayUserMain_Close": 10,
}

PVC_COMPUTED_MSG01_MAP = {
    "PVC_400V_StackVoltage_V": 20,
    "PVC_400I_StackCurrent_A": 22,
}

UVR_USER_MSG01_MAP = {
    "UVR_001S_RequestMode": 50,
    "UVR_002S_ControlMode_bol": 52,
    "UVR_004S_RequestPower_kW": 54,
    "UVR_003S_RequestCurrent_A": 56,
}

def float_to_registers(value):
    packed = struct.pack('>f', float(value))
    return struct.unpack('>HH', packed)

def registers_to_float(registers):
    packed = struct.pack('>HH', *registers)
    return struct.unpack('>f', packed)[0]

store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0] * 3000), zero_mode=True)
context = ModbusServerContext(slaves={UNIT_ID: store}, single=False)

def find_dbc_file():
    for file in os.listdir("."):
        if file.endswith("DBC_CAN_User.dbc"):
            return file
    raise FileNotFoundError("No DBC file found in current directory.")

def decode_message(db, can_id, can_data):
    try:
        if can_id in [0x3E8, 0x1C2]:
            msg = db.get_message_by_name("MV_User_Msg01")
            return "MV_User_Msg01", db.decode_message(msg.frame_id, can_data)
        elif can_id == 0x532:
            msg = db.get_message_by_name("PVC_Computed_Msg01")
            return "PVC_Computed_Msg01", db.decode_message(msg.frame_id, can_data)
    except Exception as e:
        print(f"[Decode Error] {e} for CAN ID {hex(can_id)}")
    return None, None

def receive_loop(bus, db, stop_event):
    while not stop_event.is_set():
        try:
            msg = bus.recv(timeout=1.0)
            if msg:
                msg_name, decoded = decode_message(db, msg.arbitration_id, msg.data)
                if decoded:
                    print(f"[RECEIVED] {msg_name} => {decoded}")
                    last_received_time[msg_name] = time.time()
                    if msg_name == "MV_User_Msg01":
                        for field, val in decoded.items():
                            if field in MV_USER_MSG01_MAP:
                                offset = MV_USER_MSG01_MAP[field]
                                regs = float_to_registers(val)
                                context[UNIT_ID].setValues(3, offset, list(map(int, regs)))
                    elif msg_name == "PVC_Computed_Msg01":
                        for field, val in decoded.items():
                            if field in PVC_COMPUTED_MSG01_MAP:
                                offset = PVC_COMPUTED_MSG01_MAP[field]
                                regs = float_to_registers(val)
                                context[UNIT_ID].setValues(3, offset, list(map(int, regs)))
        except Exception as e:
            print(f"[Receive Error] {e}")

def modbus_to_can_loop(bus, db, stop_event):
    next_send_time = time.time()
    while not stop_event.is_set():
        if time.time() >= next_send_time:
            try:
                msg = db.get_message_by_name("UVR_User_Msg01")
                data = {sig.name: 0.0 for sig in msg.signals}  # init all required fields

                for signal in msg.signals:
                    if signal.name in UVR_USER_MSG01_MAP:
                        offset = UVR_USER_MSG01_MAP[signal.name]
                        regs = context[UNIT_ID].getValues(3, offset, 2)
                        data[signal.name] = registers_to_float(regs)

                encoded = db.encode_message(msg.frame_id, data)
                can_msg = can.Message(arbitration_id=msg.frame_id, data=encoded, is_extended_id=False)
                bus.send(can_msg)
                print(f"[SENT] UVR_User_Msg01 => {data}")

            except Exception as e:
                print(f"[CAN SEND ERROR] {e}")

            next_send_time += 0.1
        time.sleep(0.001)

def can_watchdog_loop(stop_event):
    while not stop_event.is_set():
        now = time.time()
        for msg_name, field_map in [
            ("MV_User_Msg01", MV_USER_MSG01_MAP),
            ("PVC_Computed_Msg01", PVC_COMPUTED_MSG01_MAP)
        ]:
            last_time = last_received_time[msg_name]
            if now - last_time > CAN_TIMEOUT:
                for offset in field_map.values():
                    context[UNIT_ID].setValues(3, offset, [0, 0])
                print(f"[WATCHDOG] {msg_name} timeout - fields reset.")
        time.sleep(1)

def main():
    try:
        dbc_file = find_dbc_file()
        print(f"[INFO] Using DBC file: {dbc_file}")
        db = cantools.database.load_file(dbc_file)

        bus = can.interface.Bus(interface='kvaser', channel=0, bitrate=500000)
        stop_event = Event()

        threads = [
            threading.Thread(target=receive_loop, args=(bus, db, stop_event)),
            threading.Thread(target=can_watchdog_loop, args=(stop_event,)),
            threading.Thread(target=modbus_to_can_loop, args=(bus, db, stop_event)),
        ]

        for t in threads:
            t.start()

        identity = ModbusDeviceIdentification()
        identity.VendorName = "RanjithCANBridge"
        identity.ProductName = "CAN2Modbus Bridge"
        identity.ModelName = "MV_Bridge"
        identity.MajorMinorRevision = "2.1"

        StartTcpServer(context, identity=identity, address=("192.168.0.50", 5020))

    except Exception as e:
        print(f"[Startup Error] {e}")
    finally:
        print("Shutting down...")
        stop_event.set()
        for t in threads:
            t.join()
        bus.shutdown()

if __name__ == "__main__":
    main()
