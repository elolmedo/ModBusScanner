# modbus_scanner_interactive.py (Versión Final con lectura de bloque)

import sys
import time
import logging
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException

# Configuración para silenciar los logs de pymodbus
logging.basicConfig()
log = logging.getLogger("pymodbus")
log.setLevel(logging.CRITICAL)

try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    print("ADVERTENCIA: La librería 'colorama' no está instalada. No se mostrarán colores.")
    print("Por favor, instálala con: pip install colorama")
    class Fore: pass
    class Style: pass
    Fore.RED = Fore.GREEN = Fore.YELLOW = Fore.CYAN = Fore.WHITE = ""
    Style.BRIGHT = Style.RESET_ALL = ""

def print_welcome():
    """Imprime el mensaje de bienvenida."""
    print(Style.BRIGHT + Fore.CYAN + "--- Escáner de Dispositivos Modbus Interactivo ---")
    print("Esta herramienta te guiará para encontrar dispositivos en tu red.")
    print("-" * 50)

def get_validated_input(prompt, cast_to=str, valid_options=None, default=None):
    """Pide un valor al usuario, lo valida y lo devuelve."""
    while True:
        default_text = f" (por defecto: {default})" if default is not None else ""
        try:
            user_input = input(f"{prompt}{default_text}: ").strip()
            if not user_input and default is not None:
                return default
            
            value = cast_to(user_input)
            
            if valid_options:
                check_value = value
                if isinstance(value, str):
                    check_value = value.upper()
                
                if isinstance(valid_options, range) and check_value not in valid_options:
                    raise ValueError(f"El valor debe estar entre {valid_options.start} y {valid_options.stop - 1}.")
                
                if isinstance(valid_options, list) and check_value not in valid_options:
                    raise ValueError(f"Opción no válida. Elige una de: {valid_options}")
            return value
        except (ValueError, TypeError) as e:
            print(Fore.RED + f"Error: {e}. Inténtalo de nuevo.")

def get_modbus_parameters():
    """Pide al usuario los parámetros comunes de Modbus."""
    print(Style.BRIGHT + "\n2. Parámetros de la prueba Modbus")
    function_map = {'1': "Coils", '2': "Inputs", '3': "Holding", '4': "InputReg"}
    function_code_str = get_validated_input(
        "Código de función (1:Coils, 2:Inputs, 3:Holding, 4:InputReg)", 
        str, ['1', '2', '3', '4']
    )
    function_code = int(function_code_str)
    function_name = function_map[function_code_str]

    register = get_validated_input("Registro a leer para la prueba en formato decimal", int, default=0)
    
    # --- NUEVO: Preguntar por el número de registros a leer ---
    count = get_validated_input("Número de registros a leer", int, range(1, 126), default=1)

    timeout = get_validated_input("Timeout en segundos para cada intento", float, default=0.5)
    return function_code, function_name, register, count, timeout

def run_scan(client, function_code, function_name, register, count):
    """
    Ejecuta el bucle de escaneo mostrando los IDs en una cuadrícula de colores.
    """
    found_devices = []
    print(Style.BRIGHT + "\n3. Iniciando escaneo...")
    
    # --- ACTUALIZADO: El texto de la consulta ahora incluye el número de registros ---
    query_text = f"Consulta: Leer {count} registro(s) desde {register} (Función {function_code}: {function_name})"
    print(Fore.CYAN + query_text)
    print(f"Buscando dispositivos... {Fore.RED}Rojo = No encontrado{Style.RESET_ALL}, {Style.BRIGHT}{Fore.WHITE}Blanco = Encontrado{Style.RESET_ALL}")
    print("-" * 50)

    for slave_id in range(1, 255):
        is_found = False
        try:
            result = None
            # --- ACTUALIZADO: Se usa la variable 'count' en todas las lecturas ---
            if function_code == 1:
                result = client.read_coils(address=register, count=count, slave=slave_id)
            elif function_code == 2:
                result = client.read_discrete_inputs(address=register, count=count, slave=slave_id)
            elif function_code == 3:
                result = client.read_holding_registers(address=register, count=count, slave=slave_id)
            elif function_code == 4:
                result = client.read_input_registers(address=register, count=count, slave=slave_id)
            
            if result and not result.isError():
                is_found = True

        except ModbusException:
            is_found = False
        except Exception as e:
            print(f"\n{Fore.RED}Error inesperado en el esclavo {slave_id}: {e}")

        if is_found:
            found_devices.append(slave_id)
            print(f"{Style.BRIGHT}{Fore.WHITE}{slave_id:<4}{Style.RESET_ALL}", end="")
        else:
            print(f"{Fore.RED}{slave_id:<4}{Style.RESET_ALL}", end="")

        sys.stdout.flush()

        if slave_id % 20 == 0:
            print()

    print("\n\n" + Style.BRIGHT + "--- Escaneo Finalizado ---")
    if found_devices:
        print(f"Se encontraron {len(found_devices)} dispositivos:")
        print(f"Unidades ID: {Style.BRIGHT}{Fore.WHITE}", ', '.join(map(str, found_devices)))
    else:
        print(Fore.YELLOW + "No se encontraron dispositivos con los parámetros especificados.")

def main():
    """Función principal del programa."""
    print_welcome()
    
    mode_str = get_validated_input("Elige el modo (1: TCP, 2: RTU)", str, ['1', '2'])
    mode = int(mode_str)
    
    client = None
    if mode == 1:
        print(Style.BRIGHT + "\n1. Configuración de Modbus TCP")
        ip = get_validated_input("Introduce la dirección IP del dispositivo/pasarela")
        port = get_validated_input("Puerto TCP", int, range(1, 65536), 502)
        function_code, function_name, register, count, timeout = get_modbus_parameters()
        client = ModbusTcpClient(ip, port=port, timeout=timeout)
    else:
        print(Style.BRIGHT + "\n1. Configuración de Modbus RTU")
        com_port = get_validated_input("Puerto Serie (ej. COM3 en Windows)")
        baud = get_validated_input("Baud rate (velocidad)", int, default=9600)
        parity_choice = get_validated_input("Paridad (N: None, E: Even, O: Odd)", str, ['N', 'E', 'O'], 'N')
        bytesize = get_validated_input("Bits de datos", int, [7, 8], 8)
        stopbits = get_validated_input("Bits de parada", int, [1, 2], 1)
        function_code, function_name, register, count, timeout = get_modbus_parameters()
        client = ModbusSerialClient(
            port=com_port, baudrate=baud, bytesize=bytesize, 
            parity=parity_choice, stopbits=stopbits, timeout=timeout
        )
    
    if not client.connect():
        print(Fore.RED + Style.BRIGHT + "\n[ERROR CRÍTICO] No se pudo establecer la conexión inicial.")
        print("Verifica los parámetros (IP/Puerto COM) y la conexión física.")
        return

    run_scan(client, function_code, function_name, register, count)
    client.close()
    print("\nConexión cerrada.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n\n" + Fore.RED + Style.BRIGHT + "Ha ocurrido un error fatal e inesperado:")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir.")

