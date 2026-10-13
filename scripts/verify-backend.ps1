function Assert-BackendDatabase {
    param([string]$Url, [string]$ExpectedEngine)
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10
    } catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 'no HTTP response' }
        throw "Backend database verification request failed: HTTP $status at $Url. Check endpoint routing, authentication, and backend logs; this is not evidence of a different database."
    }
    if ($response.StatusCode -ne 200) { throw "Backend database verification returned HTTP $($response.StatusCode), expected 200." }
    if ($response.Headers['Content-Type'] -notmatch 'application/json') { throw 'Backend database verification returned a non-JSON content type. Check routing or a redirect to authentication.' }
    try { $data = $response.Content | ConvertFrom-Json } catch { throw 'Backend database verification returned invalid JSON.' }
    if ($data.database -isnot [bool] -or $data.local_cluster_match -isnot [bool] -or $data.database_engine -isnot [string] -or !$data.identity) {
        throw 'Backend database verification response has an unexpected shape. A stale backend may be serving an older endpoint. Required: database:boolean, database_engine:string, local_cluster_match:boolean, identity:object.'
    }
    if (!$data.database) {
        throw "Backend database probe failed during '$($data.failure.phase)' ($($data.failure.type)). $($data.database_message) Check the running server's environment and applied migrations."
    }
    if ($data.database_engine -ne $ExpectedEngine) {
        throw "Backend database engine mismatch: expected $ExpectedEngine, observed $($data.database_engine). The running server may have inherited a different USE_SQLITE setting."
    }
    if ($ExpectedEngine -eq 'postgresql' -and !$data.local_cluster_match) {
        $observed = $data.identity.observed
        $configured = $data.identity.configured
        throw "Backend database identity mismatch in fields [$($data.identity.mismatched_fields -join ', ')]. Observed: host=$($observed.host), port=$($observed.port), user=$($observed.user), database=$($observed.name). Configured: host=$($configured.host), port=$($configured.port), user=$($configured.user), database=$($configured.name). No credentials are included."
    }
    Write-Host "Running backend database ready ($($data.database_engine)); identity check passed."
    if ($ExpectedEngine -eq 'postgresql') {
        $observed = $data.identity.observed
        Write-Host "Verified: $($observed.host):$($observed.port), user=$($observed.user), database=$($observed.name)."
    }
    return $data
}
