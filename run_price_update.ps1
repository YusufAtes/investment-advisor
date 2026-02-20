# Investment Advisor - Price Update Runner
# Runs the price fetcher, portfolio updater, and evaluator every 24 hours
# Frequency: Every 24 hours
# NOTE: This does NOT run the advisory executor. That only runs
#       after the main advisory pipeline (72h cycle) via main.py.

$ProjectDir = "C:\investment advisor"
$LastRunFile = "$ProjectDir\last_price_update.txt"
$LogFile = "$ProjectDir\logs\price_update.log"
$Today = Get-Date -Format "yyyy-MM-dd"

# Run frequency in hours
$RunFrequencyHours = 24

# Conda paths (adjust if your Anaconda is installed elsewhere)
$CondaPath = "$env:USERPROFILE\anaconda3"
$PythonExe = "$CondaPath\envs\invest\python.exe"

# Create logs directory if it doesn't exist
if (!(Test-Path "$ProjectDir\logs")) {
    New-Item -ItemType Directory -Path "$ProjectDir\logs" -Force | Out-Null
}

# Function to write log
function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "=== Price Update Runner Started ==="
Write-Log "Project Dir: $ProjectDir"
Write-Log "Python Exe: $PythonExe"
Write-Log "Run Frequency: Every $RunFrequencyHours hours"

# Check if enough time has passed since last run
if (Test-Path $LastRunFile) {
    $LastRunString = (Get-Content $LastRunFile -First 1).Trim()
    try {
        $LastRunTime = [datetime]::Parse($LastRunString)
        $HoursSinceLastRun = ((Get-Date) - $LastRunTime).TotalHours
        
        if ($HoursSinceLastRun -lt $RunFrequencyHours) {
            $HoursRemaining = [math]::Round($RunFrequencyHours - $HoursSinceLastRun, 1)
            Write-Log "Price update last ran at $LastRunString ($([math]::Round($HoursSinceLastRun, 1)) hours ago). Next run in ~$HoursRemaining hours. Skipping."
            exit 0
        } else {
            Write-Log "Last run was $([math]::Round($HoursSinceLastRun, 1)) hours ago (threshold: $RunFrequencyHours hours). Proceeding."
        }
    } catch {
        Write-Log "WARNING: Could not parse last run time '$LastRunString'. Proceeding with run."
    }
}

# Verify python exists
if (!(Test-Path $PythonExe)) {
    Write-Log "ERROR: Python not found at $PythonExe"
    Write-Log "Please update the CondaPath variable in this script"
    exit 1
}

Write-Log "Running price update pipeline..."

try {
    Set-Location $ProjectDir

    # Use & (call operator) + file redirection instead of Start-Process so the task
    # runs reliably when scheduled (Start-Process with -RedirectStandardOutput in
    # a non-interactive session can yield bogus exit codes like -1066598273).
    $Step1Log = "$ProjectDir\logs\price_update_${Today}_step1.log"
    $Step2Log = "$ProjectDir\logs\price_update_${Today}_step2.log"
    $Step3Log = "$ProjectDir\logs\price_update_${Today}_step3.log"

    # Step 1: Fetch prices
    Write-Log "Step 1: Fetching prices..."
    & $PythonExe "tracking/price_fetcher.py" *> $Step1Log 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: Price fetcher failed with exit code: $LASTEXITCODE"
        Get-Content $Step1Log -ErrorAction SilentlyContinue | ForEach-Object { Write-Log $_ }
        exit 1
    }
    Write-Log "Step 1: Price fetcher completed."

    # Step 2: Update portfolio prices
    Write-Log "Step 2: Updating portfolio prices..."
    & $PythonExe "tracking/update_portfolio.py" *> $Step2Log 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: Portfolio updater failed with exit code: $LASTEXITCODE"
        Get-Content $Step2Log -ErrorAction SilentlyContinue | ForEach-Object { Write-Log $_ }
        exit 1
    }
    Write-Log "Step 2: Portfolio prices updated."

    # Step 3: Evaluate and generate plots
    Write-Log "Step 3: Running evaluation..."
    & $PythonExe "tracking/evaluate.py" *> $Step3Log 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: Evaluation failed with exit code: $LASTEXITCODE"
        Get-Content $Step3Log -ErrorAction SilentlyContinue | ForEach-Object { Write-Log $_ }
        exit 1
    }
    Write-Log "Step 3: Evaluation completed."
    
    # Mark as completed
    (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") | Out-File -FilePath $LastRunFile -Force
    Write-Log "Price update pipeline completed successfully!"
    
} catch {
    Write-Log "Error running price update pipeline: $_"
}

Write-Log "=== Price Update Runner Finished ==="
