# Stop CyberForeSight Backend (Node) and Frontend (Vite/Node)
Write-Host "========================================" -ForegroundColor Red
Write-Host " Stopping CyberForeSight Services...    " -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red

# Function to stop process listening on a port
function Stop-PortProcess([int]$Port) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connections) {
            $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($p in $pids) {
                if ($p -gt 0) {
                    Write-Host "Killing process (PID: $p) on port $Port..." -ForegroundColor Yellow
                    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                }
            }
            Write-Host "Port $Port freed." -ForegroundColor Green
        } else {
            Write-Host "No active process listening on port $Port." -ForegroundColor Gray
        }
    } catch {
        Write-Host "Could not query port $Port: $_" -ForegroundColor DarkGray
    }
}

# Free Backend Port (5000)
Write-Host "`n[1/2] Stopping Backend on port 5000..." -ForegroundColor Cyan
Stop-PortProcess -Port 5000

# Free Frontend Port (5173)
Write-Host "`n[2/2] Stopping Frontend on port 5173..." -ForegroundColor Cyan
Stop-PortProcess -Port 5173

Write-Host "`nAll CyberForeSight services stopped successfully." -ForegroundColor Green
