
# Script para descargar e importar chile-latest.osm.pbf de forma robusta

$DownloadUrl = "https://download.geofabrik.de/south-america/chile-latest.osm.pbf"
$OutputFile = "osrm-data\chile-latest.osm.pbf"
$TempFile = "$OutputFile.tmp"

Write-Host "[*] Descargando datos de Chile para OSRM..." -ForegroundColor Cyan

# Configurar tiempos de timeout más largos
$ProgressPreference = 'SilentlyContinue'
$WebClient = New-Object System.Net.WebClient
$WebClient.DownloadFileAsync($DownloadUrl, $TempFile)

# Mostrar progreso cada 10 segundos
$lastSize = 0
$noChangeCount = 0
while ($WebClient.IsBusy) {
    $currentSize = (Get-Item $TempFile -ErrorAction SilentlyContinue).Length
    if ($currentSize -gt $lastSize) {
        $sizeMB = [math]::Round($currentSize / 1MB, 2)
        Write-Host "[*] Descargado: $sizeMB MB" -ForegroundColor Green
        $lastSize = $currentSize
        $noChangeCount = 0
    } else {
        $noChangeCount++
    }
    
    if ($noChangeCount -gt 30) {
        Write-Host "[!] Timeout: No hay progreso en 5 minutos" -ForegroundColor Red
        $WebClient.CancelAsync()
        break
    }
    
    Start-Sleep -Seconds 10
}

if ($WebClient.IsBusy) {
    Write-Host "[!] Descarga cancelada" -ForegroundColor Red
    Remove-Item $TempFile -Force -ErrorAction SilentlyContinue
    exit 1
}

# Renombrar archivo temp a final
if (Test-Path $TempFile) {
    Remove-Item $OutputFile -Force -ErrorAction SilentlyContinue
    Rename-Item $TempFile $OutputFile
    $finalSize = (Get-Item $OutputFile).Length / 1MB
    Write-Host "[OK] Descarga completada: $([math]::Round($finalSize, 2)) MB" -ForegroundColor Green
} else {
    Write-Host "[!] Error: El archivo no se descargó correctamente" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Archivo listo: $OutputFile" -ForegroundColor Cyan
