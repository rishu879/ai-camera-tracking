# Doctor diagnostic script for AI Camera Tracking
$ErrorActionPreference = "Continue"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  AI Camera Tracking Environment & Network Doctor" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$results = @()

function Test-Check {
    param(
        [string]$Name,
        [scriptblock]$CheckBlock,
        [string]$FixHint
    )
    try {
        $status = & $CheckBlock
        if ($status) {
            Write-Host " [PASS] $Name" -ForegroundColor Green
            return @{ Name = $Name; Status = "PASS"; Details = $status }
        } else {
            Write-Host " [FAIL] $Name" -ForegroundColor Red
            Write-Host "        Hint: $FixHint" -ForegroundColor Yellow
            return @{ Name = $Name; Status = "FAIL"; Details = $FixHint }
        }
    } catch {
        Write-Host " [FAIL] $Name ($($_.Exception.Message))" -ForegroundColor Red
        Write-Host "        Hint: $FixHint" -ForegroundColor Yellow
        return @{ Name = $Name; Status = "FAIL"; Details = $_.Exception.Message }
    }
}

# 1. Python environment check (primary)
Test-Check -Name "Python >= 3.10" -CheckBlock {
    $pyVer = (python --version) 2>$null
    if ($pyVer -match "3\.(\d+)") {
        if ([int]$matches[1] -ge 10) { return "Found $pyVer" }
    }
    return $null
} -FixHint "Install Python 3.10 or higher"

# 2. Python .venv check
Test-Check -Name "Python Virtual Environment (.venv)" -CheckBlock {
    $py = ".\.venv\Scripts\python.exe"
    if (Test-Path $py) {
        $ver = & $py --version
        return "Found $ver"
    }
    return $null
} -FixHint "Create virtualenv: python -m venv .venv and pip install -r requirements.txt"

# 3. Python core dependencies
Test-Check -Name "Python Core Modules (FastAPI, OpenCV, NumPy, SciPy)" -CheckBlock {
    $py = ".\.venv\Scripts\python.exe"
    $test = & $py -c "import fastapi, cv2, numpy, scipy; print('OK')" 2>$null
    if ($test -match "OK") { return "Modules verified" }
    return $null
} -FixHint "Run: .\.venv\Scripts\pip.exe install -r requirements.txt"

# 4. Frontend assets check
Test-Check -Name "Frontend Web Assets (client/index.html)" -CheckBlock {
    if (Test-Path ".\client\index.html") {
        return "Frontend console assets verified"
    }
    return $null
} -FixHint "Ensure client/ directory with index.html exists"

# 5. Environment configuration (.env)
Test-Check -Name "Environment Configuration (.env)" -CheckBlock {
    if (Test-Path ".\.env") {
        return ".env present"
    }
    return $null
} -FixHint "Copy .env.example to .env"

# 6. Active Wi-Fi IPv4 address
$lanIP = $null
Test-Check -Name "Wi-Fi IPv4 Address Detection" -CheckBlock {
    $wifi = Get-NetIPAddress -InterfaceAlias "Wi-Fi" -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "169.254*" }
    if ($wifi) {
        $script:lanIP = $wifi[0].IPAddress
        return "Detected LAN IP: $script:lanIP"
    }
    return $null
} -FixHint "Ensure Wi-Fi is connected and active"

# 7. Network Profile Category (Private vs Public)
Test-Check -Name "Network Category is 'Private' (Required for LAN Access)" -CheckBlock {
    $profile = Get-NetConnectionProfile -InterfaceAlias "Wi-Fi" -ErrorAction SilentlyContinue
    if ($profile -and $profile.NetworkCategory -eq "Private") {
        return "Network profile is Private ('$($profile.Name)')"
    } elseif ($profile) {
        throw "Network profile for '$($profile.Name)' is '$($profile.NetworkCategory)'. Must be set to 'Private' to allow incoming LAN connections."
    }
    return $null
} -FixHint "In Administrator PowerShell run: Set-NetConnectionProfile -Name '$($profile.Name)' -NetworkCategory Private"

# 8. Test Suite
Test-Check -Name "Full Test Suite (pytest 56/56)" -CheckBlock {
    $py = ".\.venv\Scripts\pytest.exe"
    $res = & $py --tb=no -q 2>$null
    if ($LASTEXITCODE -eq 0) { return "All tests passed" }
    return $null
} -FixHint "Run: .\.venv\Scripts\pytest.exe to inspect failing tests"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Doctor Summary Complete" -ForegroundColor Cyan
if ($script:lanIP) {
    Write-Host "  Mission Control URL:    http://localhost:8000" -ForegroundColor Green
    Write-Host "  Network / Wi-Fi URL:    http://$($script:lanIP):8000" -ForegroundColor Green
    Write-Host "  Health Check URL:       http://$($script:lanIP):8000/health" -ForegroundColor White
}
Write-Host "================================================================" -ForegroundColor Cyan
