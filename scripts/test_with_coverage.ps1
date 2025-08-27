Param(
    [switch]$FailFast
)

# Ensures venv python is used; activate not required
$py = Join-Path $PSScriptRoot '..' | Join-Path -ChildPath 'venv' | Join-Path -ChildPath 'Scripts' | Join-Path -ChildPath 'python.exe'
if (!(Test-Path $py)) {
    Write-Error "python.exe not found in venv. Create venv first (python -m venv venv)."
    exit 2
}

# Clean previous coverage data to avoid branch/statement mismatch
& $py -m coverage erase | Out-Null

$pytestArgs = @(
    '-m', 'not slow',
    '--cov=benchmark',
    '--cov=run_benchmark',
    '--cov=validation',
    '--cov-report=term-missing',
    '--cov-report=xml',
    '--cov-report=html',
    '--cov-fail-under=62'
)
if ($FailFast) { $pytestArgs += @('--maxfail=1') }

Write-Host 'Running tests with coverage...' -ForegroundColor Cyan
& $py -m pytest @pytestArgs
$code = $LASTEXITCODE
if ($code -eq 0) {
    Write-Host 'Coverage run succeeded.' -ForegroundColor Green
} else {
    Write-Host "Coverage run failed (exit $code)." -ForegroundColor Red
}
exit $code
