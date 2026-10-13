param([switch]$UseSQLite)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$manage = Join-Path $backend 'manage.py'
$vite = Join-Path $frontend 'node_modules\vite\bin\vite.js'
$logs = Join-Path $root 'logs'
$pgBin = 'C:\Program Files\PostgreSQL\16\bin'
$pgData = 'C:\Users\karth\AppData\Local\Temp\opencode\python-studio-pg'
. (Join-Path $root 'scripts\postgres-dev.ps1')
. (Join-Path $root 'scripts\verify-backend.ps1')

function Get-ProjectListener([int]$Port) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    foreach ($listener in $listeners) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
        if (!$owner.CommandLine -or $owner.CommandLine.IndexOf($root, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
            throw "Port $Port belongs to another process (PID $($listener.OwningProcess)). No process was terminated."
        }
    }
    return $listeners.Count -gt 0
}

function Wait-Ready([string]$Url, [string]$Name) {
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($response.StatusCode -eq 200) { Write-Host "$Name ready: $Url"; return }
        } catch { }
        Write-Host "Waiting for $Name readiness..."
        Start-Sleep -Milliseconds 750
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "$Name did not become ready within 30 seconds. See $logs. No unrelated process was stopped."
}

function Read-DatabaseStatus([switch]$ConfigurationOnly) {
    $arguments = @($manage, 'check_database')
    if ($ConfigurationOnly) { $arguments += '--configuration-only' }
    elseif (!$UseSQLite) { $arguments += @('--expected-data-dir', $pgData) }
    $output = & $python @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Backend database validation failed. Check backend/.env locally; no passwords are printed by the diagnostic command.' }
    return ($output | ConvertFrom-Json)
}

# Serializes concurrent invocations for this Windows user's local cluster/project.
$mutex = New-Object System.Threading.Mutex($false, 'Local\PythonWebsiteStudioDevelopmentStartup')
$locked = $false
try {
    try { $locked = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
    if (!$locked) { throw 'Another project startup is already in progress. Wait for it to finish; no duplicate start was attempted.' }
    if (!(Test-Path -LiteralPath $python) -or !(Test-Path -LiteralPath $vite)) { throw 'Dependencies are missing. Follow README.md installation instructions.' }
    if (!(Test-Path -LiteralPath $logs)) { New-Item -ItemType Directory -Path $logs | Out-Null }
    if ($UseSQLite) {
        $env:USE_SQLITE = 'true'
        $env:DJANGO_DEBUG = 'true'
        Write-Host 'Explicit SQLite mode. The PostgreSQL cluster and its data will not be changed.'
    } else {
        # An explicit PostgreSQL start must not inherit a previous shell's SQLite test mode.
        $env:USE_SQLITE = 'false'
    }

    $backendRunning = Get-ProjectListener 8001
    $frontendRunning = Get-ProjectListener 5174
    $configuration = Read-DatabaseStatus -ConfigurationOnly
    if (!$UseSQLite) {
        if ($configuration.engine -ne 'django.db.backends.postgresql' -or $configuration.host -ne '127.0.0.1' -or $configuration.port -ne '55432' -or $configuration.user -ne 'studio_test' -or $configuration.name -ne 'python_studio') {
            throw 'Backend configuration does not match the local project cluster. Set DATABASE_URL host=127.0.0.1, port=55432, user=studio_test, database=python_studio, retaining any password. Check inherited environment overrides too.'
        }
        Ensure-ProjectPostgres -Bin $pgBin -DataDirectory $pgData -LogPath (Join-Path $logs 'postgresql.log') -TimeoutSeconds 60
    }

    $database = Read-DatabaseStatus
    Write-Host "Backend database query succeeded: $($database.name), user $($database.user), $($database.host):$($database.port)."
    if (!$UseSQLite) { Write-Host "Database identity verified; PostgreSQL started at $($database.server_started_at)." }

    # Apply only existing migrations. This does not reset data or recreate the database.
    & $python $manage migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Migration failed. Existing data was not reset.' }
    $database = Read-DatabaseStatus
    if ($database.counts.learning_lesson -eq 0) {
        & $python $manage seed_content
        if ($LASTEXITCODE -ne 0) { throw 'Initial curriculum seed failed.' }
    } else { Write-Host "Preserving $($database.counts.learning_lesson) existing lessons; automatic reseeding skipped." }

    if (!$backendRunning) {
        $server = Start-Process -FilePath $python -ArgumentList ('"' + $manage + '" runserver 127.0.0.1:8001 --noreload') -WorkingDirectory $backend -PassThru -RedirectStandardOutput (Join-Path $logs 'backend.log') -RedirectStandardError (Join-Path $logs 'backend-error.log')
        Write-Host "Started project backend, PID $($server.Id)."
    } else { Write-Host 'Reusing this project''s backend on port 8001.' }
    Wait-Ready 'http://127.0.0.1:8001/api/session/' 'Backend'

    # This probe queries the running backend's own database, not just this shell's settings.
    $expectedEngine = if ($UseSQLite) { 'sqlite' } else { 'postgresql' }
    $liveDatabase = Assert-BackendDatabase -Url 'http://127.0.0.1:8001/api/database-readiness/' -ExpectedEngine $expectedEngine

    if (!$frontendRunning) {
        $node = (Get-Command node.exe).Source
        $client = Start-Process -FilePath $node -ArgumentList ('"' + $vite + '" --host 127.0.0.1 --port 5174 --strictPort') -WorkingDirectory $frontend -PassThru -RedirectStandardOutput (Join-Path $logs 'frontend.log') -RedirectStandardError (Join-Path $logs 'frontend-error.log')
        Write-Host "Started project frontend, PID $($client.Id)."
    } else { Write-Host 'Reusing this project''s frontend on port 5174.' }
    Wait-Ready 'http://127.0.0.1:5174' 'Frontend'

    try {
        $ready = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/readiness/' -TimeoutSec 10
        Write-Host "Ollama reachable: $($ready.ollama.reachable); configured model available: $($ready.ollama.model_available)"
        if (!$ready.ollama.model_available) { Write-Host $ready.ollama.message }
    } catch { Write-Host 'Ollama readiness check unavailable. Lessons and Python execution remain independent; see /status.' }
    Write-Host 'Open http://127.0.0.1:5174. PostgreSQL logs will use logs/postgresql.log on its next controlled start.'
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
