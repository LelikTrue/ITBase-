import ctypes
import json
import platform
import sys
import winreg

import wmi


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    """Перезапускает скрипт с правами администратора"""
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


def pause_exit(code=0):
    print("\nНажмите Enter, чтобы выйти...")
    input()
    sys.exit(code)


print("=== ITBase Inventory Agent v4.0 (Admin) ===")

# --- 0. Проверка прав Администратора ---
if not is_admin():
    print("[!] Требуются права Администратора для точного определения железа.")
    print("[*] Попытка перезапуска с правами Администратора...")
    try:
        run_as_admin()
        sys.exit(0)  # Завершаем текущий процесс, так как запустился новый
    except Exception as e:
        print(f"[ERROR] Не удалось получить права админа: {e}")
        print("Пожалуйста, запустите EXE файл правой кнопкой мыши -> 'Запуск от имени администратора'.")
        pause_exit(1)


# --- Инициализация WMI ---
try:
    print("[*] WMI (Standard)...", end=" ")
    c = wmi.WMI()
    print("OK")
except Exception as e:
    print(f"FAIL: {e}")
    pause_exit(1)


# Теперь, с правами админа, это должно сработать
try:
    print("[*] WMI (Storage)...", end=" ")
    wmi_storage = wmi.WMI(namespace="root/Microsoft/Windows/Storage")
    print("OK")
except Exception:
    print("SKIP (Not found)")
    wmi_storage = None


hostname = platform.node()
# ВАЖНО: Структура должна быть словарем, а не списком!
inventory = {
    "hostname": hostname,
    "components": []
}


# --- 1. Motherboard ---
print("1. Motherboard...", end=" ")
try:
    boards = c.Win32_BaseBoard()
    for board in boards:
        # Добавляем в компоненты как "motherboard"
        inventory["components"].append({
            "type": "motherboard",
            "name": board.Product.strip() if board.Product else "Unknown Board",
            "serial_number": board.SerialNumber.strip() if board.SerialNumber else None,
            "manufacturer": board.Manufacturer.strip() if board.Manufacturer else None
        })
    print("OK")
except Exception as e:
    print(f"ERR: {e}")


# --- 2. CPU ---
print("2. CPU...", end=" ")
try:
    for cpu in c.Win32_Processor():
        inventory["components"].append({
            "type": "cpu",
            "name": cpu.Name.strip(),
            "cores": int(cpu.NumberOfCores) if cpu.NumberOfCores else 1,
            "threads": int(cpu.NumberOfLogicalProcessors) if cpu.NumberOfLogicalProcessors else 1,
            "base_clock_mhz": int(cpu.MaxClockSpeed) if cpu.MaxClockSpeed else None,
            "serial_number": cpu.ProcessorId.strip() if cpu.ProcessorId else None,
            "manufacturer": cpu.Manufacturer.strip() if cpu.Manufacturer else None
        })
    print("OK")
except Exception as e:
    print(f"ERR: {e}")


# --- 3. RAM ---
print("3. RAM...", end=" ")
try:
    for mem in c.Win32_PhysicalMemory():
        size_mb = int(int(mem.Capacity) / (1024**2))
        inventory["components"].append({
            "type": "ram",
            "name": mem.PartNumber.strip() if mem.PartNumber else "Unknown RAM",
            "size_mb": size_mb,
            "speed_mhz": int(mem.Speed) if mem.Speed else None,
            "form_factor": "DIMM",
            "serial_number": mem.SerialNumber.strip() if mem.SerialNumber else None,
            "manufacturer": mem.Manufacturer.strip() if mem.Manufacturer else None
        })
    print("OK")
except Exception as e:
    print(f"ERR: {e}")


# --- 4. Storage (Modern) ---
print("4. Storage...", end=" ")
try:
    if wmi_storage:
        for disk in wmi_storage.MSFT_PhysicalDisk():
            # MediaType: 3=HDD, 4=SSD, 5=SCM
            media_type = getattr(disk, 'MediaType', 0)
            disk_type = "HDD"
            if media_type == 4:
                disk_type = "SSD"

            # BusType: 17=NVMe, 11=SATA
            bus_type = getattr(disk, 'BusType', 0)
            if bus_type == 17:
                disk_type = "SSD"  # NVMe is always SSD

            interface_map = {17: "NVMe", 11: "SATA", 7: "USB"}
            interface = interface_map.get(bus_type, "Unknown")

            size_gb = int(int(disk.Size) / (1024**3))

            inventory["components"].append({
                "type": "storage",
                "name": disk.FriendlyName.strip(),
                "type_label": disk_type,
                "capacity_gb": size_gb,
                "interface": interface,
                "serial_number": disk.SerialNumber.strip() if disk.SerialNumber else None,
                "manufacturer": getattr(disk, 'Manufacturer', None)
            })
    else:
        # Fallback
        for disk in c.Win32_DiskDrive():
            size_gb = int(int(disk.Size) / (1024**3))
            inventory["components"].append({
                "type": "storage",
                "name": disk.Model.strip(),
                "type_label": "HDD",
                "capacity_gb": size_gb,
                "interface": disk.InterfaceType,
                "serial_number": disk.SerialNumber.strip(),
                "manufacturer": None
            })
    print("OK")
except Exception as e:
    print(f"ERR: {e}")


# --- 5. GPU (Registry + Fixes) ---
print("5. GPU...", end=" ")


def _check_video_subkey(key_path, subkey_name, gpu_name):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"{key_path}\\{subkey_name}") as sk:
            desc = winreg.QueryValueEx(sk, "DriverDesc")[0]
            if gpu_name in desc or desc in gpu_name:
                vram = winreg.QueryValueEx(sk, "HardwareInformation.qwMemorySize")[0]
                if isinstance(vram, bytes):
                    vram = int.from_bytes(vram, 'little')
                mb = int(vram / (1024**2))
                if mb > 128:
                    return mb
    except Exception:
        pass
    return None


def get_gpu_vram(gpu_name):
    key_path = r"SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(key, i)
                    vram = _check_video_subkey(key_path, sub, gpu_name)
                    if vram:
                        return vram
                    i += 1
                except Exception:
                    break
    except Exception:
        pass
    return None


def collect_gpu_info(wmi_client):
    """Сбор информации о видеокартах с учетом проверок VRAM."""
    components = []
    count = 0

    for gpu in wmi_client.Win32_VideoController():
        name = str(gpu.Name)
        # Игнорируем виртуальные адаптеры и RDP
        if any(x in name for x in ["RDP", "VNC", "Remote", "Virtual", "Citrix", "Microsoft"]):
            continue

        mem_mb = get_gpu_vram(name)

        # Fallback to WMI if Registry failed
        if not mem_mb and hasattr(gpu, 'AdapterRAM') and gpu.AdapterRAM:
            try:
                raw = int(gpu.AdapterRAM)
                if raw < 0:
                    raw += 2**32
                calc_mb = int(raw / (1024**2))
                if calc_mb > 128:
                    mem_mb = calc_mb
            except Exception:
                pass

        # Если память все равно кривая или слишком мала, ставим None
        if mem_mb is not None and mem_mb < 128:
            mem_mb = None

        components.append({
            "type": "gpu",
            "name": name.strip(),
            "memory_mb": mem_mb,
            "serial_number": getattr(gpu, 'PNPDeviceID', None),
            "manufacturer": getattr(gpu, 'AdapterCompatibility', None)
        })
        count += 1

    return components, count


try:
    gpu_list, count = collect_gpu_info(c)
    inventory["components"].extend(gpu_list)
    print(f"Found: {count}")
except Exception as e:
    print(f"ERR: {e}")


# --- Save ---
filename = f"inventory_{hostname}.json"
try:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    print(f"\n[SUCCESS] Saved to: {filename}")
except Exception as e:
    print(f"[ERROR] Save failed: {e}")

pause_exit(0)
