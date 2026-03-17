$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $repoRoot "dist"
$packageDir = Join-Path $distDir "backend-lambda"
$zipPath = Join-Path $distDir "backend-lambda.zip"
$requirementsFile = Join-Path $repoRoot "backend\requirements-lambda.txt"
$repoRootUnix = $repoRoot -replace "\\", "/"

if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $packageDir | Out-Null

docker run --rm `
    -v "${repoRootUnix}:/var/task" `
    -w /var/task `
    --entrypoint /bin/sh `
    public.ecr.aws/lambda/python:3.11 `
    -c "python -m pip install --upgrade pip >/dev/null && python -m pip install -r backend/requirements-lambda.txt -t dist/backend-lambda"

Copy-Item -Path (Join-Path $repoRoot "backend\app") -Destination (Join-Path $packageDir "app") -Recurse
if (Test-Path (Join-Path $repoRoot "backend\resources")) {
    Copy-Item -Path (Join-Path $repoRoot "backend\resources") -Destination (Join-Path $packageDir "resources") -Recurse
}

Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath -Force
Write-Host "Created $zipPath"
