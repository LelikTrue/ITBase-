# ITBase Hardware Inventory Agent
# Скрипт для сбора информации о компонентах компьютера
# Генерирует JSON, соответствующий Pydantic-схемам ITBase

# Функция для конвертации байтов в мегабайты
function ConvertTo-MB {
    param([long]$Bytes)
    return [math]::Round($Bytes / 1MB)
}

# Функция для конвертации байтов в гигабайты
function ConvertTo-GB {
    param([long]$Bytes)
    return [math]::Round($Bytes / 1GB)
}

# Инициализация массива компонентов
$components = @()

Write-Host "=== ITBase Hardware Inventory Agent ===" -ForegroundColor Cyan
Write-Host "Сбор информации о компонентах..." -ForegroundColor Yellow

# 1. Сбор данных CPU
Write-Host "`nСбор данных CPU..." -ForegroundColor Green
try {
    $cpuInfo = Get-CimInstance -ClassName Win32_Processor
    foreach ($cpu in $cpuInfo) {
        $cpuComponent = @{
            type = "cpu"
            name = $cpu.Name.Trim()
            cores = $cpu.NumberOfCores
            threads = $cpu.NumberOfLogicalProcessors
            base_clock_mhz = $cpu.MaxClockSpeed
            serial_number = if ($cpu.ProcessorId) { $cpu.ProcessorId } else { $null }
            manufacturer = if ($cpu.Manufacturer) { $cpu.Manufacturer.Trim() } else { $null }
        }
        $components += $cpuComponent
        Write-Host "  ✓ CPU: $($cpu.Name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Ошибка при сборе данных CPU: $_" -ForegroundColor Red
}

# 2. Сбор данных RAM
Write-Host "`nСбор данных RAM..." -ForegroundColor Green
try {
    $ramInfo = Get-CimInstance -ClassName Win32_PhysicalMemory
    foreach ($ram in $ramInfo) {
        $ramComponent = @{
            type = "ram"
            name = if ($ram.PartNumber) { $ram.PartNumber.Trim() } else { "Unknown RAM Module" }
            size_mb = ConvertTo-MB -Bytes $ram.Capacity
            speed_mhz = $ram.Speed
            form_factor = switch ($ram.FormFactor) {
                8 { "DIMM" }
                12 { "SODIMM" }
                default { "Unknown" }
            }
            serial_number = if ($ram.SerialNumber) { $ram.SerialNumber.Trim() } else { $null }
            manufacturer = if ($ram.Manufacturer) { $ram.Manufacturer.Trim() } else { $null }
        }
        $components += $ramComponent
        Write-Host "  ✓ RAM: $($ramComponent.size_mb) MB @ $($ram.Speed) MHz" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Ошибка при сборе данных RAM: $_" -ForegroundColor Red
}

# 3. Сбор данных Storage
Write-Host "`nСбор данных Storage..." -ForegroundColor Green
try {
    $diskInfo = Get-CimInstance -ClassName Win32_DiskDrive
    foreach ($disk in $diskInfo) {
        # Определяем тип диска
        $diskType = "HDD"
        if ($disk.Model -match "SSD|Solid State|NVMe") {
            if ($disk.Model -match "NVMe") {
                $diskType = "NVMe"
            } else {
                $diskType = "SSD"
            }
        }
        
        # Определяем интерфейс
        $interface = switch -Regex ($disk.InterfaceType) {
            "SCSI" { "SATA" }
            "IDE" { "IDE" }
            "USB" { "USB" }
            default { $disk.InterfaceType }
        }
        
        $storageComponent = @{
            type = "storage"
            name = $disk.Model.Trim()
            type_label = $diskType
            capacity_gb = ConvertTo-GB -Bytes $disk.Size
            interface = $interface
            serial_number = if ($disk.SerialNumber) { $disk.SerialNumber.Trim() } else { $null }
            manufacturer = if ($disk.Manufacturer) { $disk.Manufacturer.Trim() } else { $null }
        }
        $components += $storageComponent
        Write-Host "  ✓ Storage: $($disk.Model) - $($storageComponent.capacity_gb) GB ($diskType)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Ошибка при сборе данных Storage: $_" -ForegroundColor Red
}

# 4. Сбор данных GPU
Write-Host "`nСбор данных GPU..." -ForegroundColor Green
try {
    $gpuInfo = Get-CimInstance -ClassName Win32_VideoController
    foreach ($gpu in $gpuInfo) {
        # Пропускаем виртуальные адаптеры
        if ($gpu.Name -notmatch "Microsoft|Remote|Virtual") {
            $gpuComponent = @{
                type = "gpu"
                name = $gpu.Name.Trim()
                memory_mb = if ($gpu.AdapterRAM) { ConvertTo-MB -Bytes $gpu.AdapterRAM } else { $null }
                serial_number = if ($gpu.PNPDeviceID) { $gpu.PNPDeviceID } else { $null }
                manufacturer = if ($gpu.AdapterCompatibility) { $gpu.AdapterCompatibility.Trim() } else { $null }
            }
            $components += $gpuComponent
            Write-Host "  ✓ GPU: $($gpu.Name)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  ✗ Ошибка при сборе данных GPU: $_" -ForegroundColor Red
}

# Формируем итоговый JSON
$output = @{
    components = $components
}

# Конвертируем в JSON
$jsonOutput = $output | ConvertTo-Json -Depth 10

# Выводим результат
Write-Host "`n=== Результат ===" -ForegroundColor Cyan
Write-Host "Собрано компонентов: $($components.Count)" -ForegroundColor Yellow
Write-Host "`nJSON:" -ForegroundColor Green
Write-Host $jsonOutput

# Сохраняем в файл
$outputPath = Join-Path -Path $PSScriptRoot -ChildPath "components.json"
$jsonOutput | Out-File -FilePath $outputPath -Encoding UTF8
Write-Host "`n✓ Данные сохранены в: $outputPath" -ForegroundColor Green

Write-Host "`nГотово! Загрузите файл components.json в ITBase." -ForegroundColor Cyan
