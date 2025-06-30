# modbus_scanner.py (Versión 3.0 - Final)

import argparse
import sys
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException

def get_function_name(code):
    """Devuelve el nombre de la función Modbus a partir de su código."""
    return {
        1: "Read Coils",
        2: "Read Discrete Inputs",
        3: "Read Holding Registers",
        4: "Read Input Registers"
    }.get(code, f"Unknown function ({code})")

def scan_modbus_tcp(ip, port, function_code, register, timeout):
    """
    Escanea todos los esclavos (1-254) en una dirección IP y puerto TCP específicos.
    """
    print(f"--- Iniciando escaneo Modbus TCP ---")
    print(f"IP de destino: {ip}:{port}")
    print(f"Función: {get_function_name(function_code)} (Código {function_code})")
    print(f"Registro a leer: {register}")
    print("-" * 40)

    found_devices = []
    
    client = ModbusTcpClient(ip, port=port, timeout=timeout)
    
    if not client.connect():
        print(f"[ERROR] No se pudo conectar a {ip}:{port}. Verifica la dirección y el puerto.")
        return

    for slave_id in range(1, 255):
        try:
            sys.stdout.write(f"\rProbando esclavo {slave_id}... ")
            sys.stdout.flush()

            result = None
            # >>> CORRECCIÓN FINAL: Usamos argumentos por nombre (keyword arguments) para máxima compatibilidad.
            if function_code == 1:
                result = client.read_coils(address=register, count=1, slave=slave_id)
            elif function_code == 2:
                result = client.read_discrete_inputs(address=register, count=1, slave=slave_id)
            elif function_code == 3:
                result = client.read_holding_registers(address=register, count=1, slave=slave_id)
            elif function_code == 4:
                result = client.read_input_registers(address=register, count=1, slave=slave_id)
            
            if result.isError():
                pass
            else:
                print(f"\r¡Dispositivo ENCONTRADO en la unidad ID {slave_id}!")
                found_devices.append(slave_id)

        except ModbusException:
            pass
            
    client.close()
    
    print("\n--- Escaneo TCP finalizado ---")
    if found_devices:
        print(f"Dispositivos encontrados: {len(found_devices)}")
        print(f"Unidades ID: {', '.join(map(str, found_devices))}")
    else:
        print("No se encontraron dispositivos Modbus en la red.")


def scan_modbus_rtu(com_port, baud, bytesize, parity, stopbits, function_code, register, timeout):
    """
    Escanea todos los esclavos (1-254) en un puerto serie (COM) específico.
    """
    print(f"--- Iniciando escaneo Modbus RTU ---")
    print(f"Puerto COM: {com_port}")
    print(f"Configuración: {baud} baud, {bytesize} bits, Paridad: {parity}, Paro: {stopbits}")
    print(f"Función: {get_function_name(function_code)} (Código {function_code})")
    print(f"Registro a leer: {register}")
    print("-" * 40)

    found_devices = []
    client = ModbusSerialClient(
        port=com_port, baudrate=baud, bytesize=bytesize,
        parity=parity, stopbits=stopbits, timeout=timeout
    )

    if not client.connect():
        print(f"[ERROR] No se pudo abrir el puerto {com_port}. ¿Está en uso o no existe?")
        return

    for slave_id in range(1, 255):
        try:
            sys.stdout.write(f"\rProbando esclavo {slave_id}... ")
            sys.stdout.flush()

            result = None
            # >>> CORRECCIÓN FINAL: Usamos argumentos por nombre (keyword arguments) para máxima compatibilidad.
            if function_code == 1:
                result = client.read_coils(address=register, count=1, slave=slave_id)
            elif function_code == 2:
                result = client.read_discrete_inputs(address=register, count=1, slave=slave_id)
            elif function_code == 3:
                result = client.read_holding_registers(address=register, count=1, slave=slave_id)
            elif function_code == 4:
                result = client.read_input_registers(address=register, count=1, slave=slave_id)
            
            if result.isError():
                pass
            else:
                print(f"\r¡Dispositivo ENCONTRADO en la unidad ID {slave_id}!")
                found_devices.append(slave_id)

        except ModbusException:
            pass

    client.close()

    print("\n--- Escaneo RTU finalizado ---")
    if found_devices:
        print(f"Dispositivos encontrados: {len(found_devices)}")
        print(f"Unidades ID: {', '.join(map(str, found_devices))}")
    else:
        print("No se encontraron dispositivos Modbus en este bus.")


def main():
    parser = argparse.ArgumentParser(
        description="Escáner de dispositivos Modbus TCP y RTU.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
--------------------
Ejemplos de uso:
--------------------
# Escanear una red TCP usando la función 3 y el registro por defecto (0)
  python %(prog)s -f 3 tcp --ip 192.168.1.10

# Escanear una red TCP usando la función 3 y un registro específico (40108)
  python %(prog)s -f 3 -r 40108 tcp --ip 192.168.1.10 --port 502

# Escanear un bus RTU en COM4 (9600, 8N1) usando la función 4
  python %(prog)s -f 4 rtu --port COM4

# Escanear un bus RTU con parámetros específicos
  python %(prog)s -f 1 -r 120 rtu --port COM4 --baud 19200 --parity E
"""
    )
    parser.add_argument(
        '-f', '--function', type=int, required=True, choices=[1, 2, 3, 4],
        help="""Código de función Modbus a usar (obligatorio):
  1: Read Coils
  2: Read Discrete Inputs
  3: Read Holding Registers
  4: Read Input Registers"""
    )
    parser.add_argument(
        '-r', '--register', type=int, default=0,
        help="Dirección del registro a leer para probar el esclavo (por defecto: 0)."
    )
    parser.add_argument(
        '-t', '--timeout', type=float, default=0.5,
        help="Timeout en segundos para cada intento (ej. 0.2)."
    )
    
    subparsers = parser.add_subparsers(dest='mode', required=True, help='Modo de operación: tcp o rtu')

    tcp_parser = subparsers.add_parser('tcp', help='Modo Modbus TCP/IP')
    tcp_parser.add_argument('--ip', type=str, required=True, help='Dirección IP del dispositivo o pasarela Modbus.')
    tcp_parser.add_argument('--port', type=int, default=502, help='Puerto TCP (por defecto: 502).')
    
    rtu_parser = subparsers.add_parser('rtu', help='Modo Modbus RTU (Serie)')
    rtu_parser.add_argument('--port', type=str, required=True, help='Puerto serie (ej. COM3 en Windows).')
    rtu_parser.add_argument('--baud', type=int, default=9600, help='Baud rate (velocidad, ej. 9600, 19200).')
    rtu_parser.add_argument('--bytesize', type=int, default=8, choices=[7, 8], help='Bits de datos (7 u 8).')
    rtu_parser.add_argument('--parity', type=str, default='N', choices=['N', 'E', 'O'], help='Paridad (N=None, E=Even, O=Odd).')
    rtu_parser.add_argument('--stopbits', type=int, default=1, choices=[1, 2], help='Bits de parada (1 o 2).')

    args = parser.parse_args()
    
    register_to_use = args.register
    register_display = f"{args.register}"
    if '-r' not in sys.argv and '--register' not in sys.argv:
        register_display += " (por defecto)"

    if args.mode == 'tcp':
        scan_modbus_tcp(args.ip, args.port, args.function, register_to_use, args.timeout)
    elif args.mode == 'rtu':
        # Pasamos el string formateado a la función para que lo muestre
        scan_modbus_rtu(args.port, args.baud, args.bytesize, args.parity, args.stopbits, args.function, register_display, args.timeout)


if __name__ == "__main__":
    main()
