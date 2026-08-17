$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Processes = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()

function Import-DotEnv {
    param([Parameter(Mandatory = $true)][string] $Path)

    if (-not (Test-Path $Path)) {
        return
    }

    foreach ($Line in Get-Content $Path) {
        $TrimmedLine = $Line.Trim()
        if (-not $TrimmedLine -or $TrimmedLine.StartsWith("#")) {
            continue
        }

        $Parts = $TrimmedLine.Split("=", 2)
        if ($Parts.Count -ne 2 -or $Parts[0] -notmatch "^[A-Za-z_][A-Za-z0-9_]*$") {
            continue
        }

        $Name = $Parts[0]
        if (Test-Path "Env:$Name") {
            continue
        }

        $Value = $Parts[1].Trim()
        if (
            $Value.Length -ge 2 -and
            (($Value.StartsWith('"') -and $Value.EndsWith('"')) -or
                ($Value.StartsWith("'") -and $Value.EndsWith("'")))
        ) {
            $Value = $Value.Substring(1, $Value.Length - 2)
        }
        Set-Item "Env:$Name" $Value
    }
}

function Invoke-CheckedCommand {
    param([Parameter(Mandatory = $true)][scriptblock] $Command)

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "명령 실행에 실패했습니다 (종료 코드: $LASTEXITCODE)."
    }
}

function Stop-AppProcesses {
    foreach ($Process in $Processes) {
        if (-not $Process.HasExited) {
            try {
                $Process.Kill($true)
                $Process.WaitForExit()
            }
            catch {
                Write-Warning "$($Process.ProcessName) 프로세스를 종료하지 못했습니다: $_"
            }
        }
    }
}

Push-Location $RepoRoot
try {
    Import-DotEnv (Join-Path $RepoRoot ".env")

    $BackendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }
    $FrontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "5173" }
    $McpPort = if ($env:MCP_PORT) { $env:MCP_PORT } else { "8001" }
    if (-not $env:VITE_BACKEND_ORIGIN) {
        $env:VITE_BACKEND_ORIGIN = "http://localhost:$BackendPort"
    }

    if (
        -not $env:NEIS_API_KEY -and
        $env:NEIS_FIXTURE_MODE -ne "true"
    ) {
        throw "NEIS_API_KEY를 설정하거나 NEIS_FIXTURE_MODE=true를 지정하세요."
    }

    if (-not (Test-Path "src/web/node_modules")) {
        Write-Host "==> 프론트엔드 의존성 설치"
        Push-Location "src/web"
        try {
            Invoke-CheckedCommand { npm ci }
        }
        finally {
            Pop-Location
        }
    }

    $UvCommand = (Get-Command uv -ErrorAction Stop).Source
    $NpmCommand = (Get-Command npm -ErrorAction Stop).Source

    Write-Host "==> 백엔드 시작: http://localhost:$BackendPort"
    $Backend = Start-Process -FilePath $UvCommand -WorkingDirectory "src/api" `
        -ArgumentList @(
            "run", "fastapi", "dev", "src/bsl_api/main.py",
            "--host", "0.0.0.0", "--port", $BackendPort
        ) -NoNewWindow -PassThru
    $Processes.Add($Backend)

    Write-Host "==> MCP 서버 시작: http://localhost:$McpPort/mcp"
    $env:MCP_PORT = $McpPort
    $Mcp = Start-Process -FilePath $UvCommand -WorkingDirectory "src/mcp" `
        -ArgumentList @("run", "bsl-mcp") -NoNewWindow -PassThru
    $Processes.Add($Mcp)

    Write-Host "==> 프론트엔드 시작: http://localhost:$FrontendPort"
    $Frontend = Start-Process -FilePath $NpmCommand -WorkingDirectory "src/web" `
        -ArgumentList @(
            "run", "dev", "--", "--host", "0.0.0.0",
            "--port", $FrontendPort
        ) -NoNewWindow -PassThru
    $Processes.Add($Frontend)

    Write-Host "CTRL+C를 누르면 모든 앱을 종료합니다."

    while (
        -not $Backend.HasExited -and
        -not $Mcp.HasExited -and
        -not $Frontend.HasExited
    ) {
        Start-Sleep -Milliseconds 500
    }

    $StoppedProcess = if ($Backend.HasExited) {
        $Backend
    } elseif ($Mcp.HasExited) {
        $Mcp
    } else {
        $Frontend
    }
    if ($StoppedProcess.ExitCode -ne 0) {
        throw "앱 프로세스가 종료 코드 $($StoppedProcess.ExitCode)로 종료되었습니다."
    }
}
finally {
    Stop-AppProcesses
    Pop-Location
}
