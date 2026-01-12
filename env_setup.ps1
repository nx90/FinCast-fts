# PowerShell script to setup the conda environment
# Usage: .\env_setup.ps1

$ErrorActionPreference = "Stop"

$ENV_NAME = "fincast_v1"
$PYTHON_VERSION = "3.11.11"

Write-Host "🔧 Creating Conda environment: $ENV_NAME with Python $PYTHON_VERSION..." -ForegroundColor Cyan
conda create --yes --name "$ENV_NAME" python="$PYTHON_VERSION"

Write-Host "✅ Conda environment '$ENV_NAME' created successfully." -ForegroundColor Green
Write-Host "👉 Next step: Run 'conda activate $ENV_NAME' and then '.\dep_install.ps1'" -ForegroundColor Yellow
