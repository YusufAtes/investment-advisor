# Investment Advisor - Scheduled Runner Script
# Runs the pipeline once every 72 hours when computer starts
# Frequency: Every 72 hours (3 days)

$ProjectDir = "C:\investment advisor"
$LastRunFile = "$ProjectDir\last_run.txt"
$LogFile = "$ProjectDir\logs\daily_run.log"
$Today = Get-Date -Format "yyyy-MM-dd"

# Run frequency in hours (72 hours = 3 days)
$RunFrequencyHours = 72

# Conda paths (adjust if your Anaconda is installed elsewhere)
$CondaPath = "$env:USERPROFILE\anaconda3"
$CondaExe = "$CondaPath\Scripts\conda.exe"
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

Write-Log "=== Scheduled Runner Started ==="
Write-Log "Project Dir: $ProjectDir"
Write-Log "Python Exe: $PythonExe"
Write-Log "Run Frequency: Every $RunFrequencyHours hours"

# Check if enough time has passed since last run (72-hour window)
if (Test-Path $LastRunFile) {
    $LastRunString = (Get-Content $LastRunFile -First 1).Trim()
    try {
        $LastRunTime = [datetime]::Parse($LastRunString)
        $HoursSinceLastRun = ((Get-Date) - $LastRunTime).TotalHours
        
        if ($HoursSinceLastRun -lt $RunFrequencyHours) {
            $HoursRemaining = [math]::Round($RunFrequencyHours - $HoursSinceLastRun, 1)
            Write-Log "Pipeline last ran at $LastRunString ($([math]::Round($HoursSinceLastRun, 1)) hours ago). Next run in ~$HoursRemaining hours. Skipping."
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

Write-Log "Running investment advisor pipeline for $Today..."

# Run the pipeline using the conda environment's Python directly
try {
    Set-Location $ProjectDir
    
    $PipelineLog = "$ProjectDir\logs\pipeline_$Today.log"
    
    # Run main.py using the invest environment's Python directly
    $Process = Start-Process -FilePath $PythonExe -ArgumentList "main.py" -WorkingDirectory $ProjectDir -Wait -PassThru -NoNewWindow -RedirectStandardOutput $PipelineLog -RedirectStandardError "$ProjectDir\logs\pipeline_${Today}_error.log"
    
    if ($Process.ExitCode -eq 0) {
        # Mark as completed with full datetime for accurate 72-hour tracking
        (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") | Out-File -FilePath $LastRunFile -Force
        Write-Log "Pipeline completed successfully!"
        Write-Log "Output saved to: $PipelineLog"
    } else {
        Write-Log "Pipeline failed with exit code: $($Process.ExitCode)"
        Write-Log "Check error log: $ProjectDir\logs\pipeline_${Today}_error.log"
    }
} catch {
    Write-Log "Error running pipeline: $_"
}

Write-Log "=== Scheduled Runner Finished ==="
