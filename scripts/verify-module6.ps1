$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$database = 'GolBet_Module6Verify_' + [Guid]::NewGuid().ToString('N')
$connectionKey = 'ConnectionStrings__DefaultConnection'
$previousConnection = [Environment]::GetEnvironmentVariable($connectionKey, 'Process')
$previousEnvironment = $env:ASPNETCORE_ENVIRONMENT
$appProcess = $null
$logDirectory = Join-Path ([IO.Path]::GetTempPath()) $database
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
$listener.Start()
$port = $listener.LocalEndpoint.Port
$listener.Stop()
$url = "http://127.0.0.1:$port"

try {
    dotnet build (Join-Path $projectRoot 'GolBet.sln') --no-restore
    if ($LASTEXITCODE -ne 0) { throw 'La compilación falló.' }
    New-Item -ItemType Directory -Path $logDirectory | Out-Null
    [Environment]::SetEnvironmentVariable($connectionKey,
        "Server=localhost;Database=$database;Trusted_Connection=True;TrustServerCertificate=True", 'Process')
    $env:ASPNETCORE_ENVIRONMENT = 'Development'
    $webRoot = Join-Path $projectRoot 'GolBet.Web'
    $assembly = Join-Path $webRoot 'bin\Debug\net8.0\GolBet.Web.dll'
    $appProcess = Start-Process dotnet -ArgumentList "`"$assembly`" --urls $url" -WorkingDirectory $webRoot `
        -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'stdout.log') `
        -RedirectStandardError (Join-Path $logDirectory 'stderr.log')
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($appProcess.HasExited) { throw "La aplicación se detuvo. Ver logs: $logDirectory" }
        try {
            $response = Invoke-WebRequest "$url/Teams" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (!$ready) { throw "La aplicación no inició. Ver logs: $logDirectory" }
    python -X utf8 (Join-Path $PSScriptRoot 'verify-module6.py') $url $database
    if ($LASTEXITCODE -ne 0) { throw 'Falló la verificación del módulo 6.' }
} finally {
    if ($null -ne $appProcess -and !$appProcess.HasExited) {
        Stop-Process -Id $appProcess.Id
        $appProcess.WaitForExit()
    }
    [Environment]::SetEnvironmentVariable($connectionKey, $previousConnection, 'Process')
    $env:ASPNETCORE_ENVIRONMENT = $previousEnvironment
    # This name is generated here, exclusively for this run. Never drop the application's database.
    sqlcmd -S localhost -E -C -b -Q "IF DB_ID(N'$database') IS NOT NULL BEGIN ALTER DATABASE [$database] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [$database]; END"
    if ($LASTEXITCODE -ne 0) { Write-Warning "No se pudo eliminar la base temporal $database." }
    Write-Host "Logs de verificación: $logDirectory"
}
