# AWS S3 Folder Download Script
# Downloads specific folders from S3 bucket using AWS CLI with SSO profile

param(
    [string]$BucketName = "production-cb-offergenerator",
    [string]$Region = "eu-west-2",
    [string]$Profile = "production",
    [string]$LocalPath = ".\downloads",
    [string[]]$Folders = @("77580", "77667", "77828", "77579", "77666", "77829", "77669", "77748", "77826", "77708", "77789", "77863")
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if AWS CLI is available
function Test-AWSCLI {
    try {
        $null = aws --version
        return $true
    }
    catch {
        Write-ColorOutput "ERROR: AWS CLI is not installed or not in PATH" "Red"
        return $false
    }
}

# Function to check if profile exists
function Test-AWSProfile {
    param([string]$ProfileName)
    
    try {
        $profiles = aws configure list-profiles 2>$null
        return $profiles -contains $ProfileName
    }
    catch {
        return $false
    }
}

# Function to download a single folder
function Download-S3Folder {
    param(
        [string]$FolderName,
        [string]$Bucket,
        [string]$Region,
        [string]$Profile,
        [string]$LocalPath
    )
    
    $folderPath = "$LocalPath\$FolderName"
    $s3Prefix = "$FolderName/"
    
    Write-ColorOutput "Starting download for folder: $FolderName" "Yellow"
    
    # Create local directory
    if (!(Test-Path $folderPath)) {
        New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
        Write-ColorOutput "Created local directory: $folderPath" "Green"
    }
    
    try {
        # Use AWS CLI to sync the folder
        $awsCommand = "aws s3 sync s3://$Bucket/$s3Prefix `"$folderPath`" --region $Region --profile $Profile --no-progress"
        
        Write-ColorOutput "Executing: $awsCommand" "Cyan"
        
        # Execute the command and capture output
        $result = Invoke-Expression $awsCommand 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "SUCCESS: Successfully downloaded folder: $FolderName" "Green"
            
            # Count downloaded files
            $fileCount = (Get-ChildItem -Path $folderPath -Recurse -File).Count
            Write-ColorOutput "  Files downloaded: $fileCount" "Green"
        }
        else {
            Write-ColorOutput "ERROR: Failed to download folder: $FolderName" "Red"
            Write-ColorOutput "  Error: $result" "Red"
        }
    }
    catch {
        Write-ColorOutput "ERROR: Exception occurred while downloading folder: $FolderName" "Red"
        Write-ColorOutput "  Error: $($_.Exception.Message)" "Red"
    }
}

# Main execution
Write-ColorOutput "=== AWS S3 Folder Download Script ===" "Magenta"
Write-ColorOutput "Bucket: $BucketName" "White"
Write-ColorOutput "Region: $Region" "White"
Write-ColorOutput "Profile: $Profile" "White"
Write-ColorOutput "Local Path: $LocalPath" "White"
Write-ColorOutput "Folders to download: $($Folders -join ', ')" "White"
Write-ColorOutput "=====================================" "Magenta"

# Pre-flight checks
if (!(Test-AWSCLI)) {
    exit 1
}

if (!(Test-AWSProfile -ProfileName $Profile)) {
    Write-ColorOutput "ERROR: AWS profile '$Profile' not found. Available profiles:" "Red"
    aws configure list-profiles
    exit 1
}

# Create local download directory
if (!(Test-Path $LocalPath)) {
    New-Item -ItemType Directory -Path $LocalPath -Force | Out-Null
    Write-ColorOutput "Created download directory: $LocalPath" "Green"
}

# Test S3 access
Write-ColorOutput "Testing S3 access..." "Yellow"
try {
    $testResult = aws s3 ls s3://$BucketName --region $Region --profile $Profile 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "ERROR: Cannot access S3 bucket '$BucketName'. Check your permissions and profile." "Red"
        Write-ColorOutput "Error: $testResult" "Red"
        exit 1
    }
    Write-ColorOutput "SUCCESS: S3 access confirmed" "Green"
}
catch {
    Write-ColorOutput "ERROR: Failed to test S3 access" "Red"
    exit 1
}

# Download each folder
$startTime = Get-Date
$successCount = 0
$totalFolders = $Folders.Count

Write-ColorOutput "`nStarting downloads..." "Yellow"

foreach ($folder in $Folders) {
    Download-S3Folder -FolderName $folder -Bucket $BucketName -Region $Region -Profile $Profile -LocalPath $LocalPath
    
    if ($LASTEXITCODE -eq 0) {
        $successCount++
    }
    
    Write-ColorOutput "" "White"  # Empty line for readability
}

# Summary
$endTime = Get-Date
$duration = $endTime - $startTime

Write-ColorOutput "=== Download Summary ===" "Magenta"
Write-ColorOutput "Total folders: $totalFolders" "White"
Write-ColorOutput "Successful: $successCount" "Green"
Write-ColorOutput "Failed: $($totalFolders - $successCount)" "Red"
Write-ColorOutput "Duration: $($duration.ToString('hh\:mm\:ss'))" "White"
Write-ColorOutput "Download location: $LocalPath" "White"
Write-ColorOutput "=======================" "Magenta"

if ($successCount -eq $totalFolders) {
    Write-ColorOutput "SUCCESS: All downloads completed successfully!" "Green"
    exit 0
}
else {
    Write-ColorOutput "WARNING: Some downloads failed. Check the output above for details." "Yellow"
    exit 1
}
