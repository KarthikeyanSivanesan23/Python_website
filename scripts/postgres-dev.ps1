# PostgreSQL helpers: dot-sourcing this file performs no startup or filesystem writes.
function Invoke-PostgresTool {
    param([string]$Bin, [string]$Tool, [string[]]$Arguments)
    $ErrorActionPreference = 'Continue'
    $output = & (Join-Path $Bin $Tool) @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    [PSCustomObject]@{ Code = $exitCode; Text = ($output | ForEach-Object { $_.ToString() }) -join "`n" }
}

function Assert-PostgresPortOwner {
    param([string]$DataDirectory, [int]$Port)
    $expected = $DataDirectory.Replace('\', '/').TrimEnd('/').ToLowerInvariant()
    foreach ($listener in @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
        $command = if ($owner.CommandLine) { $owner.CommandLine.Replace('\', '/').ToLowerInvariant() } else { '' }
        if ($owner.Name -ne 'postgres.exe' -or !$command.Contains($expected)) {
            throw "Port $Port belongs to a different or unidentifiable process (PID $($listener.OwningProcess), $($owner.Name)). No process was stopped and PostgreSQL was not started."
        }
    }
}

function Get-PostgresState {
    param([string]$Bin, [string]$DataDirectory)
    $status = Invoke-PostgresTool -Bin $Bin -Tool 'pg_ctl.exe' -Arguments @('-D', $DataDirectory, 'status')
    $ready = Invoke-PostgresTool -Bin $Bin -Tool 'pg_isready.exe' -Arguments @('-h', '127.0.0.1', '-p', '55432', '-U', 'studio_test', '-d', 'python_studio', '-t', '2')
    if ($status.Code -notin @(0, 3)) {
        throw "Cannot establish PostgreSQL cluster status (exit $($status.Code)): $($status.Text). No startup attempted."
    }
    [PSCustomObject]@{ Running = $status.Code -eq 0; Ready = $ready.Code -eq 0; StatusText = $status.Text; ReadyText = $ready.Text }
}

function Show-PostgresDiagnostics {
    param([string]$Bin, [string]$DataDirectory, [string]$LogPath)
    $state = Get-PostgresState -Bin $Bin -DataDirectory $DataDirectory
    Write-Host $state.StatusText
    Write-Host $state.ReadyText
    foreach ($path in @($LogPath, (Join-Path $DataDirectory 'server.log'))) {
        if (Test-Path -LiteralPath $path) {
            Write-Host "Recent PostgreSQL log lines: $path"
            Get-Content -LiteralPath $path -Tail 35 | ForEach-Object { Write-Host $_ }
        }
    }
    return $state
}

function Ensure-ProjectPostgres {
    param(
        [string]$Bin,
        [string]$DataDirectory,
        [string]$LogPath,
        [int]$TimeoutSeconds = 60
    )
    if (!(Test-Path -LiteralPath $DataDirectory -PathType Container)) {
        throw "Existing PGDATA was not found: $DataDirectory. Startup never runs initdb or recreates databases."
    }
    foreach ($tool in @('pg_ctl.exe', 'pg_isready.exe', 'postgres.exe')) {
        if (!(Test-Path -LiteralPath (Join-Path $Bin $tool))) { throw "Missing PostgreSQL tool: $tool" }
    }
    # The caller holds a project startup mutex. Every invocation checks both tools first.
    $state = Get-PostgresState -Bin $Bin -DataDirectory $DataDirectory
    Assert-PostgresPortOwner -DataDirectory $DataDirectory -Port 55432
    if ($state.Running -and $state.Ready) {
        Write-Host 'PostgreSQL ready: reusing the existing cluster at 127.0.0.1:55432 (studio_test / python_studio).'
        Write-Host $state.StatusText
        return
    }
    if ($state.Ready -and !$state.Running) {
        throw 'Port 55432 responds, but pg_ctl does not identify this cluster as running. Resolve the ownership mismatch before startup.'
    }

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    if (!$state.Running) {
        # Inspect effective file-based logging configuration before the next controlled start.
        $collector = Invoke-PostgresTool -Bin $Bin -Tool 'postgres.exe' -Arguments @('-D', $DataDirectory, '-C', 'logging_collector')
        $destination = Invoke-PostgresTool -Bin $Bin -Tool 'postgres.exe' -Arguments @('-D', $DataDirectory, '-C', 'log_destination')
        if ($collector.Code -ne 0 -or $destination.Code -ne 0 -or $collector.Text.Trim() -ne 'off' -or $destination.Text.Trim() -ne 'stderr') {
            throw 'Logging configuration differs from the verified stderr/collector-off configuration. Inspect it before starting so log destinations are not duplicated or conflicted.'
        }
        $parent = Split-Path -Parent $LogPath
        if (!(Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
        Write-Host "Starting PostgreSQL once. Startup log: $LogPath"
        # -W returns immediately; the one bounded polling loop below covers recovery.
        $start = Invoke-PostgresTool -Bin $Bin -Tool 'pg_ctl.exe' -Arguments @('-D', $DataDirectory, '-l', $LogPath, '-o', '-p 55432 -h 127.0.0.1', '-W', 'start')
        Write-Host $start.Text
        if ($start.Code -ne 0) { Write-Host 'pg_ctl reported a startup error; checking status through the deadline without issuing another start.' }
    } else {
        Write-Host 'The cluster is already running but not ready, possibly recovering. Waiting without issuing pg_ctl start.'
    }

    do {
        Assert-PostgresPortOwner -DataDirectory $DataDirectory -Port 55432
        $state = Get-PostgresState -Bin $Bin -DataDirectory $DataDirectory
        if ($state.Running -and $state.Ready) {
            Write-Host 'PostgreSQL is ready at 127.0.0.1:55432.'
            return
        }
        $remaining = [Math]::Max(0, [int]($deadline - [DateTime]::UtcNow).TotalSeconds)
        Write-Host "Waiting for PostgreSQL readiness ($remaining seconds remaining): $($state.ReadyText)"
        if ([DateTime]::UtcNow -lt $deadline) { Start-Sleep -Seconds 1 }
    } while ([DateTime]::UtcNow -lt $deadline)

    $final = Show-PostgresDiagnostics -Bin $Bin -DataDirectory $DataDirectory -LogPath $LogPath
    if ($final.Running -and $final.Ready) {
        Write-Host 'PostgreSQL became ready at the final deadline check; reusing it.'
        return
    }
    throw "PostgreSQL did not become ready within $TimeoutSeconds seconds. No repeated start, restart, PID-file deletion, or forced shutdown was attempted. Recovery may still be continuing."
}
