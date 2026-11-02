# SignAI — PowerShell Starter Script
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  SignAI — AI-Powered Multilingual Sign Language System" -ForegroundColor White
Write-Host "  Starting server at http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan

try {
    Start-Sleep -Seconds 1
    Start-Process "http://127.0.0.1:5000"
    python app.py
} catch {
    Write-Host "[ERROR] Failed to start server: $_" -ForegroundColor Red
}
