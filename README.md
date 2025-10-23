# AWS S3 Folder Downloader

This repository contains scripts to download specific folders from an AWS S3 bucket using your existing AWS SSO profile.

## Prerequisites

- AWS CLI installed and configured
- AWS SSO profile named `production` configured
- For Python script: Python 3.7+ and pip

## Files

- `download-s3-folders.ps1` - PowerShell script using AWS CLI
- `download_s3_folders.py` - Python script using boto3
- `requirements.txt` - Python dependencies

## Usage

### PowerShell Script

```powershell
# Basic usage (uses default parameters)
.\download-s3-folders.ps1

# Custom parameters
.\download-s3-folders.ps1 -LocalPath "C:\MyDownloads" -Folders @("77580", "77667")

# Help
Get-Help .\download-s3-folders.ps1 -Full
```

**Default Parameters:**
- Bucket: `production-cb-offergenerator`
- Region: `eu-west-2`
- Profile: `production`
- Local Path: `.\downloads`
- Folders: All 12 specified folders

### Python Script

```bash
# Install dependencies
pip install -r requirements.txt

# Basic usage
python download_s3_folders.py

# Custom parameters
python download_s3_folders.py --local-path ./my_downloads --folders 77580 77667

# Help
python download_s3_folders.py --help
```

## Features

### PowerShell Script
- ✅ Uses AWS CLI with SSO profile
- ✅ Colored output for better readability
- ✅ Progress tracking and error handling
- ✅ Pre-flight checks (AWS CLI, profile, S3 access)
- ✅ Detailed summary with timing
- ✅ Maintains folder structure locally

### Python Script
- ✅ Uses boto3 with AWS SSO profile
- ✅ Progress bars with file-by-file tracking
- ✅ Comprehensive logging to file and console
- ✅ Detailed error handling and reporting
- ✅ Configurable via command-line arguments
- ✅ Maintains folder structure locally
- ✅ Summary statistics

## Folder List

The scripts are configured to download these folders:
- 77580/
- 77667/
- 77828/
- 77579/
- 77666/
- 77829/
- 77669/
- 77748/
- 77826/
- 77708/
- 77789/
- 77863/

## Authentication

Both scripts use your existing AWS SSO profile named `production`. Make sure you've run:

```bash
aws sso login --profile production
```

## Output

Files will be downloaded to the specified local path, maintaining the original folder structure:

```
downloads/
├── 77580/
│   ├── file1.txt
│   └── subfolder/
│       └── file2.txt
├── 77667/
│   └── file3.txt
└── ...
```

## Error Handling

Both scripts include comprehensive error handling for:
- Missing AWS CLI
- Invalid AWS profile
- S3 access permissions
- Network connectivity issues
- Individual file download failures

## Logging

- **PowerShell**: Colored console output with success/failure indicators
- **Python**: Detailed logging to both console and `s3_download.log` file
