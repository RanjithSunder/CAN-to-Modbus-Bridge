# CAN to Modbus Bridge

A Python-based bridge application that translates between CAN bus and Modbus TCP protocols, specifically designed for MV (Motor Vehicle) and PVC (Power Voltage Control) systems.

## Features

- **CAN Bus Reception**: Receives and decodes CAN messages using DBC files
- **Modbus TCP Server**: Exposes received CAN data via Modbus TCP protocol
- **Bidirectional Communication**: Supports both CAN→Modbus and Modbus→CAN data flow
- **Watchdog Protection**: Automatically resets Modbus registers when CAN messages timeout
- **Multi-threaded Architecture**: Concurrent handling of CAN reception, Modbus serving, and watchdog monitoring

## Supported Messages

### Incoming CAN Messages (CAN → Modbus)
- **MV_User_Msg01** (CAN IDs: 0x3E8, 0x1C2)
  - Mode Actual
  - Current Available (A)
  - Alarm State
  - Counter
  - Relay User Precharge Close
  - Relay User Main Close

- **PVC_Computed_Msg01** (CAN ID: 0x532)
  - Stack Voltage (V)
  - Stack Current (A)

### Outgoing CAN Messages (Modbus → CAN)
- **UVR_User_Msg01**
  - Request Mode
  - Control Mode
  - Request Power (kW)
  - Request Current (A)

## Requirements

- Python 3.7+
- Kvaser CAN interface hardware
- DBC file ending with `DBC_CAN_User.dbc`

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd can-modbus-bridge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Place your DBC file in the project directory (must end with `DBC_CAN_User.dbc`)

## Configuration

### Network Settings
- **Modbus TCP Server**: 192.168.0.50:5020
- **CAN Interface**: Kvaser, Channel 0, 500kbps

### Modbus Register Mapping
- MV messages: Registers 0-19
- PVC messages: Registers 20-49  
- UVR messages: Registers 50-69

### Timeouts
- CAN message timeout: 0.5 seconds
- Watchdog check interval: 1 second
- UVR message send interval: 100ms

## Usage

1. Connect your Kvaser CAN interface
2. Ensure the CAN network is active
3. Run the bridge:
```bash
python main.py
```

4. Connect your Modbus TCP client to `192.168.0.50:5020`

## Architecture

The application uses a multi-threaded architecture:

- **Main Thread**: Starts the Modbus TCP server
- **CAN Receive Thread**: Continuously receives and processes CAN messages
- **Watchdog Thread**: Monitors CAN message timeouts and resets stale data
- **CAN Send Thread**: Periodically sends UVR messages based on Modbus register values

## Data Format

All floating-point values are converted to/from IEEE 754 32-bit format and stored as pairs of 16-bit Modbus registers (big-endian).

## Error Handling

- CAN decoding errors are logged but don't stop operation
- Missing DBC files cause startup failure
- CAN interface errors are logged and recovered automatically
- Modbus client disconnections don't affect CAN operation

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please create an issue in the GitHub repository.
