$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeProjectName = "bsl-pyconkr-tests"
$TestFrontendPort = if ($env:TEST_FRONTEND_PORT) {
    $env:TEST_FRONTEND_PORT
} else {
    "15173"
}
$TestBackendPort = if ($env:TEST_BACKEND_PORT) {
    $env:TEST_BACKEND_PORT
} else {
    "18000"
}
$TestMcpPort = if ($env:TEST_MCP_PORT) {
    $env:TEST_MCP_PORT
} else {
    "18001"
}
$TestAgentPort = if ($env:TEST_AGENT_PORT) {
    $env:TEST_AGENT_PORT
} else {
    "18002"
}
$OriginalEnvironment = @{
    NEIS_FIXTURE_MODE = $env:NEIS_FIXTURE_MODE
    NEIS_API_KEY = $env:NEIS_API_KEY
    FRONTEND_PORT = $env:FRONTEND_PORT
    BACKEND_PORT = $env:BACKEND_PORT
    E2E_BASE_URL = $env:E2E_BASE_URL
    MCP_PORT = $env:MCP_PORT
    AGENT_PORT = $env:AGENT_PORT
    AGENT_FIXTURE_MODE = $env:AGENT_FIXTURE_MODE
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "명령 실행에 실패했습니다 (종료 코드: $LASTEXITCODE)."
    }
}

Push-Location $RepoRoot
try {
    Write-Host "==> 백엔드 테스트"
    Push-Location "src/api"
    try {
        Invoke-CheckedCommand { uv sync --locked }
        Invoke-CheckedCommand { uv run pytest }
    }
    finally {
        Pop-Location
    }

    Write-Host "==> 프론트엔드 테스트"
    Push-Location "src/web"
    try {
        Invoke-CheckedCommand { npm ci }
        Invoke-CheckedCommand { npm test }
    }
    finally {
        Pop-Location
    }

    Write-Host "==> MCP 서버 테스트"
    Push-Location "src/mcp"
    try {
        Invoke-CheckedCommand { uv sync --locked }
        Invoke-CheckedCommand { uv run pytest }
    }
    finally {
        Pop-Location
    }

    Write-Host "==> 에이전트 앱 테스트"
    Push-Location "src/agent"
    try {
        Invoke-CheckedCommand { uv sync --locked }
        Invoke-CheckedCommand { uv run pytest }
    }
    finally {
        Pop-Location
    }

    Write-Host "==> E2E 테스트용 애플리케이션 시작"
    $env:NEIS_FIXTURE_MODE = "true"
    $env:NEIS_API_KEY = ""
    $env:FRONTEND_PORT = $TestFrontendPort
    $env:BACKEND_PORT = $TestBackendPort
    $env:MCP_PORT = $TestMcpPort
    $env:AGENT_PORT = $TestAgentPort
    $env:AGENT_FIXTURE_MODE = "true"
    Invoke-CheckedCommand {
        docker compose --project-name $ComposeProjectName up --build --detach `
            --wait --wait-timeout 120
    }

    Write-Host "==> Playwright E2E 테스트"
    Push-Location "src/e2e"
    try {
        Invoke-CheckedCommand { npm ci }
        Invoke-CheckedCommand { npx playwright install chromium }
        $env:E2E_BASE_URL = "http://localhost:$TestFrontendPort"
        Invoke-CheckedCommand { npm test }
    }
    finally {
        Pop-Location
    }
}
finally {
    & docker compose --project-name $ComposeProjectName down --volumes `
        --remove-orphans 2>$null

    foreach ($Name in $OriginalEnvironment.Keys) {
        $Value = $OriginalEnvironment[$Name]
        if ($null -eq $Value) {
            Remove-Item "Env:$Name" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item "Env:$Name" $Value
        }
    }

    Pop-Location
}
