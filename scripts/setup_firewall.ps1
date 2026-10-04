# Setup script for Windows Firewall and Network Profile (Run as Administrator)
param (
    [switch]$Rollback
)

$ruleName = "AI Camera Tracking (Vite & FastAPI)"
$ports = "5173,8000"

if ($Rollback) {
    Write-Host "Rolling back firewall rules..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    Write-Host "Firewall rule '$ruleName' removed." -ForegroundColor Green
    exit 0
}

# Check Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell -> 'Run as Administrator', then execute:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\setup_firewall.ps1" -ForegroundColor Cyan
    exit 1
}

# 1. Switch active Wi-Fi network profile to Private
$wifiProfile = Get-NetConnectionProfile -InterfaceAlias "Wi-Fi" -ErrorAction SilentlyContinue
if ($wifiProfile) {
    Write-Host "Configuring network profile '$($wifiProfile.Name)' to Private..." -ForegroundColor Cyan
    Set-NetConnectionProfile -Name $wifiProfile.Name -NetworkCategory Private
    Write-Host "Network profile '$($wifiProfile.Name)' set to Private." -ForegroundColor Green
} else {
    Write-Host "No active Wi-Fi interface detected." -ForegroundColor Yellow
}

# 2. Add or update Firewall Rule
Write-Host "Adding Inbound Firewall Rule for ports $ports on Private network profile..." -ForegroundColor Cyan
Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName $ruleName `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5173, 8000 `
    -Action Allow `
    -Profile Private `
    -Description "Allows incoming traffic to AI Camera Tracking Vite dev server (5173) and FastAPI backend (8000) on Private Wi-Fi."

Write-Host "Inbound firewall rule created successfully!" -ForegroundColor Green
Write-Host "Your application is now reachable by any phone/laptop on your Wi-Fi." -ForegroundColor Green
