@echo off
setlocal enabledelayedexpansion

:: ============================================================
:: lcc.bat — Singularity Works Local Claude Code Launcher
:: Wires: LM Studio + Claude Code + Forge into one command
::
:: Usage:
::   lcc                  — show status, list loaded models
::   lcc --auto           — launch with best coder model auto-selected
::   lcc --reasoner       — launch with the 35B reasoning model
::   lcc --ghost          — launch with the 0.8B ghost model
::   lcc "model-name"     — launch with a specific model
::   lcc --validate file  — run forge validation only, no Claude Code
::   lcc --fix file       — run dialectic fix loop on a file
::   lcc --models         — list detected models and their roles
:: ============================================================

:: ---------- Configuration (override via environment) ----------
if "%LM_HOST%"=="" set LM_HOST=127.0.0.1
if "%LM_PORT%"=="" set LM_PORT=1234
if "%FORGE_DIR%"=="" set FORGE_DIR=%~dp0..\sw_v19
if "%CONTEXT_FILE%"=="" set CONTEXT_FILE=.forge-context.json

set LM_BASE=http://%LM_HOST%:%LM_PORT%
set BRIDGE=%~dp0forge_bridge.py
set CTX_MGR=%~dp0forge_context.py

:: ---------- Check Python available ----------
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found in PATH. Install Python 3.10+ and retry.
    exit /b 1
)

:: ---------- No args: show status ----------
if "%~1"=="" goto :show_status

:: ---------- Dispatch on first arg ----------
if /i "%~1"=="--models"    goto :list_models
if /i "%~1"=="--validate"  goto :do_validate
if /i "%~1"=="--fix"       goto :do_fix
if /i "%~1"=="--auto"      goto :launch_auto
if /i "%~1"=="--reasoner"  goto :launch_reasoner
if /i "%~1"=="--ghost"     goto :launch_ghost
if /i "%~1"=="--help"      goto :show_help
if /i "%~1"=="-h"          goto :show_help

:: Otherwise: treat first arg as explicit model name
set EXPLICIT_MODEL=%~1
shift
goto :launch_model

:: ============================================================
:show_status
:: ============================================================
echo.
echo  ╔═══════════════════════════════════════════════════╗
echo  ║     Singularity Works — Local Claude Code         ║
echo  ╚═══════════════════════════════════════════════════╝
echo.
echo  LM Studio : %LM_BASE%

:: Check if LM Studio is running
curl -sf "%LM_BASE%/health" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  Status    : [OFFLINE] LM Studio not running
    echo.
    echo  Start LM Studio, load a model, then run lcc again.
    echo  Make sure the server is started in LM Studio settings.
    goto :eof
)
echo  Status    : [ONLINE]

:: Get model info via bridge
echo.
echo  Detected models and roles:
python "%BRIDGE%" status 2>nul
echo.

:: Check forge
if exist "%FORGE_DIR%\singularity_works\orchestration.py" (
    echo  Forge     : [READY] %FORGE_DIR%
) else (
    echo  Forge     : [NOT FOUND] set FORGE_DIR to your sw_v19 path
)

:: Check project context
if exist "%CONTEXT_FILE%" (
    echo.
    echo  Project context:
    python "%CTX_MGR%" summary --file "%CONTEXT_FILE%" 2>nul
) else (
    echo.
    echo  No project context. Run: lcc --init "ProjectName"
)
echo.
echo  Usage: lcc --auto  ^|  lcc --reasoner  ^|  lcc "model-name"
goto :eof

:: ============================================================
:list_models
:: ============================================================
python "%BRIDGE%" models 2>nul
goto :eof

:: ============================================================
:do_validate
:: ============================================================
if "%~2"=="" (
    echo [ERROR] Usage: lcc --validate ^<file^>
    exit /b 1
)
echo Running forge validation on: %~2
python "%BRIDGE%" validate "%~2"
goto :eof

:: ============================================================
:do_fix
:: ============================================================
if "%~2"=="" (
    echo [ERROR] Usage: lcc --fix ^<file^>
    exit /b 1
)
:: Check LM Studio
curl -sf "%LM_BASE%/health" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] LM Studio not running. Cannot run dialectic loop.
    exit /b 1
)
echo Running dialectic fix loop on: %~2
python "%BRIDGE%" fix "%~2"
goto :eof

:: ============================================================
:launch_auto
:: ============================================================
shift
:: Get best coder model from bridge
for /f "tokens=*" %%i in ('python "%BRIDGE%" best-coder 2^>nul') do set AUTO_MODEL=%%i
if "%AUTO_MODEL%"=="" (
    echo [ERROR] No models loaded in LM Studio.
    exit /b 1
)
echo Auto-selected model: %AUTO_MODEL%
set SELECTED_MODEL=%AUTO_MODEL%
goto :do_launch

:: ============================================================
:launch_reasoner
:: ============================================================
shift
for /f "tokens=*" %%i in ('python "%BRIDGE%" status 2^>nul ^| python -c "import sys,json; d=json.load(sys.stdin); print(d[\"roles\"].get(\"reasoner\") or \"\")" 2^>nul') do set REASONER_MODEL=%%i
if "%REASONER_MODEL%"=="" (
    echo [WARN] No reasoner model identified. Using best-coder fallback.
    for /f "tokens=*" %%i in ('python "%BRIDGE%" best-coder 2^>nul') do set REASONER_MODEL=%%i
)
if "%REASONER_MODEL%"=="" (
    echo [ERROR] No models loaded in LM Studio.
    exit /b 1
)
echo Reasoner model: %REASONER_MODEL%
set SELECTED_MODEL=%REASONER_MODEL%
goto :do_launch

:: ============================================================
:launch_ghost
:: ============================================================
shift
for /f "tokens=*" %%i in ('python "%BRIDGE%" status 2^>nul ^| python -c "import sys,json; d=json.load(sys.stdin); print(d[\"roles\"].get(\"ghost\") or d[\"roles\"].get(\"coder\") or \"\")" 2^>nul') do set GHOST_MODEL=%%i
if "%GHOST_MODEL%"=="" (
    echo [WARN] No ghost model found. Using coder fallback.
    for /f "tokens=*" %%i in ('python "%BRIDGE%" best-coder 2^>nul') do set GHOST_MODEL=%%i
)
set SELECTED_MODEL=%GHOST_MODEL%
goto :do_launch

:: ============================================================
:launch_model
:: ============================================================
set SELECTED_MODEL=%EXPLICIT_MODEL%
goto :do_launch

:: ============================================================
:do_launch
:: ============================================================
:: Verify LM Studio is running
curl -sf "%LM_BASE%/health" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] LM Studio not running at %LM_BASE%
    echo Load a model in LM Studio and enable the local server first.
    exit /b 1
)

:: Set Claude Code environment to point at LM Studio
set ANTHROPIC_BASE_URL=%LM_BASE%
set ANTHROPIC_AUTH_TOKEN=local
set ANTHROPIC_API_KEY=
set CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
set FORGE_DIR=%FORGE_DIR%

:: Initialize forge context if not present in current directory
if not exist "%CONTEXT_FILE%" (
    echo Initializing forge context for this project...
    for %%i in (.) do set PROJ_NAME=%%~ni
    python "%CTX_MGR%" init --name "!PROJ_NAME!" --root "." --file "%CONTEXT_FILE%" >nul 2>&1
    echo Context initialized: %CONTEXT_FILE%
)

echo.
echo  ┌─ Launching Singularity Works ──────────────────────┐
echo  │  Model   : %SELECTED_MODEL%
echo  │  Backend : %LM_BASE%
echo  │  Forge   : %FORGE_DIR%
echo  │  Context : %CONTEXT_FILE%
echo  └────────────────────────────────────────────────────┘
echo.

:: Launch Claude Code with the selected model
:: Pass through any remaining args
claude --model "%SELECTED_MODEL%" %*
goto :eof

:: ============================================================
:show_help
:: ============================================================
echo.
echo  lcc — Singularity Works Local Claude Code Launcher
echo.
echo  COMMANDS:
echo    lcc                      Show status ^& loaded models
echo    lcc --auto               Launch with best available coder model
echo    lcc --reasoner           Launch with 35B reasoning model
echo    lcc --ghost              Launch with 0.8B ghost model
echo    lcc "model-name"         Launch with a specific model name
echo    lcc --validate ^<file^>    Run forge validation (no Claude Code)
echo    lcc --fix ^<file^>         Run dialectic fix loop on a file
echo    lcc --models             List detected models and assigned roles
echo.
echo  ENVIRONMENT:
echo    LM_HOST      LM Studio host (default: 127.0.0.1)
echo    LM_PORT      LM Studio port (default: 1234)
echo    FORGE_DIR    Path to sw_v19 forge directory
echo    CONTEXT_FILE Project context file (default: .forge-context.json)
echo.
echo  EXAMPLES:
echo    lcc --auto
echo    lcc --validate src\auth.py
echo    lcc --fix src\database.py
echo    lcc qwen2.5-coder-7b-instruct-abliterated
echo.
goto :eof
