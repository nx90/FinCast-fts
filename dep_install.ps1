# PowerShell script to install dependencies
# Usage: Make sure you have activated the environment first:
#        conda activate fincast_v1
#        .\dep_install.ps1

$ErrorActionPreference = "Stop"
$ENV_NAME = "fincast_v1"

# Check if running in the correct environment (Optional safety check)
if ($env:CONDA_DEFAULT_ENV -ne $ENV_NAME) {
    Write-Host "⚠️  Warning: It looks like you are in '$env:CONDA_DEFAULT_ENV', but this script is intended for '$ENV_NAME'." -ForegroundColor Yellow
    Write-Host "   If you proceed, packages will be installed in the CURRENT active environment." -ForegroundColor Yellow
    $userResponse = Read-Host "   Do you want to continue? (y/n)"
    if ($userResponse -ne 'y') {
        Write-Host "Aborting."
        exit
    }
}

Write-Host "📦 Installing pip dependencies..." -ForegroundColor Cyan
pip install -r requirement_v2.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -e .

# Installing PyTorch with CUDA 12.4 support (Compatible with your CUDA 13.0 driver)
Write-Host "🔥 Installing PyTorch 2.5.0 with CUDA 12.4..." -ForegroundColor Cyan
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124

Write-Host "✅ All packages installed successfully." -ForegroundColor Green
