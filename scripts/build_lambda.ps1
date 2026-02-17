# Build Lambda deployment package for Extraction Job API
# Run from project root: .\scripts\build_lambda.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PackageDir = Join-Path $ProjectRoot "package"
$ZipPath = Join-Path $ProjectRoot "lambda.zip"

# Clean previous build
if (Test-Path $PackageDir) { Remove-Item -Recurse -Force $PackageDir }
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }

# Create package directory
New-Item -ItemType Directory -Path $PackageDir | Out-Null

# Install dependencies
pip install -r (Join-Path $ProjectRoot "requirements.txt") -t $PackageDir --quiet

# Copy application code (exclude tests, venv, etc.)
$AppFiles = @(
    "main.py", "auth.py", "database.py", "db_models.py", "models.py",
    "repository.py", "schemas.py", "service.py", "lambda_handler.py"
)
foreach ($f in $AppFiles) {
    Copy-Item (Join-Path $ProjectRoot $f) -Destination $PackageDir
}

# Create zip
Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -Force

# Cleanup package dir
Remove-Item -Recurse -Force $PackageDir

Write-Host "Built lambda.zip at $ZipPath"
