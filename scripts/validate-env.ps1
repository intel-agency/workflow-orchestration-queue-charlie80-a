#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validates environment configuration for workflow orchestration services.

.DESCRIPTION
    This script checks that all required environment variables are set
    and validates their format. It can be run to verify configuration
    before starting services.

.PARAMETER Strict
    Exit with error code 1 if validation fails. Default is true.

.PARAMETER ShowReport
    Print a detailed validation report. Default is true.

.PARAMETER CheckGitignore
    Verify that .env is in .gitignore. Default is true.

.PARAMETER CheckEnvFile
    Verify that .env file exists. Default is true.

.EXAMPLE
    ./scripts/validate-env.ps1
    Validates environment with all checks enabled.

.EXAMPLE
    ./scripts/validate-env.ps1 -Strict:$false
    Validates but doesn't fail on errors (useful for warnings).

.EXAMPLE
    ./scripts/validate-env.ps1 -CheckEnvFile:$false
    Skips checking for .env file (useful in CI where env vars come from secrets).

.NOTES
    Required environment variables:
    - GITHUB_TOKEN
    - ZHIPU_API_KEY
    - GITHUB_REPO
    - SENTINEL_BOT_LOGIN
    - SENTINEL_ID
    - WEBHOOK_SECRET
#>

[CmdletBinding()]
param(
    [bool]$Strict = $true,
    [bool]$ShowReport = $true,
    [bool]$CheckGitignore = $true,
    [bool]$CheckEnvFile = $true
)

# Colors for output (works in most terminals)
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Header = "Magenta"
}

# Placeholder values to reject
$PlaceholderValues = @(
    "YOUR_VALUE_HERE",
    "YOUR_TOKEN_HERE", 
    "YOUR_SECRET_HERE",
    "YOUR_API_KEY_HERE",
    "<YOUR_VALUE>",
    "<YOUR_TOKEN>",
    "<PLACEHOLDER>",
    "changeme",
    "placeholder",
    "xxx"
)

# Required variables by service
$RequiredVars = @{
    Shared = @("GITHUB_TOKEN", "ZHIPU_API_KEY")
    Sentinel = @("GITHUB_REPO", "SENTINEL_BOT_LOGIN", "SENTINEL_ID")
    Notifier = @("WEBHOOK_SECRET")
}

# Optional variables with defaults
$OptionalVars = @{
    Shared = @(
        @{ Name = "GITHUB_PERSONAL_ACCESS_TOKEN"; Default = "(uses GITHUB_TOKEN)" }
        @{ Name = "KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY"; Default = $null }
    )
    Sentinel = @(
        @{ Name = "POLL_INTERVAL"; Default = "60" }
        @{ Name = "MAX_BACKOFF"; Default = "300" }
        @{ Name = "SENTINEL_HEARTBEAT_INTERVAL"; Default = "300" }
        @{ Name = "SUBPROCESS_TIMEOUT"; Default = "1800" }
        @{ Name = "DAILY_BUDGET_LIMIT"; Default = "10.0" }
    )
    Notifier = @(
        @{ Name = "GITHUB_WEBHOOK_PORT"; Default = "8080" }
        @{ Name = "GITHUB_APP_ID"; Default = $null }
    )
    App = @(
        @{ Name = "LOG_LEVEL"; Default = "INFO" }
        @{ Name = "ENVIRONMENT"; Default = "development" }
    )
}

# Secret variable patterns
$SecretPatterns = @(
    "GITHUB_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ZHIPU_API_KEY",
    "KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY",
    "WEBHOOK_SECRET"
)

function Test-Placeholder {
    param([string]$Value)
    
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $true
    }
    
    $trimmed = $Value.Trim()
    foreach ($placeholder in $PlaceholderValues) {
        if ($trimmed -eq $placeholder -or $trimmed.ToUpper() -eq $placeholder.ToUpper()) {
            return $true
        }
    }
    return $false
}

function Test-VariableFormat {
    param(
        [string]$Name,
        [string]$Value
    )
    
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }
    
    switch ($Name) {
        "GITHUB_REPO" {
            if ($Value -notmatch "^[^/]+/[^/]+$") {
                return "Must be in 'owner/repo' format"
            }
        }
        "GITHUB_WEBHOOK_PORT" {
            try {
                $port = [int]$Value
                if ($port -lt 1024 -or $port -gt 65535) {
                    return "Port must be between 1024 and 65535"
                }
            } catch {
                return "Must be a valid integer"
            }
        }
        "POLL_INTERVAL" {
            try {
                $interval = [int]$Value
                if ($interval -lt 1 -or $interval -gt 3600) {
                    return "Must be between 1 and 3600"
                }
            } catch {
                return "Must be a valid integer"
            }
        }
        "LOG_LEVEL" {
            $valid = @("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            if ($Value.ToUpper() -notin $valid) {
                return "Must be one of: $($valid -join ', ')"
            }
        }
        "ENVIRONMENT" {
            $valid = @("development", "staging", "production", "test")
            if ($Value.ToLower() -notin $valid) {
                return "Must be one of: $($valid -join ', ')"
            }
        }
        "WEBHOOK_SECRET" {
            if ($Value.Length -lt 16) {
                return "Must be at least 16 characters"
            }
        }
    }
    
    return $null
}

function Get-StatusIcon {
    param([string]$Status)
    
    switch ($Status) {
        "OK" { return "✅" }
        "Missing" { return "❌" }
        "Placeholder" { return "❌" }
        "Invalid" { return "❌" }
        "Default" { return "⚪" }
        default { return "❓" }
    }
}

function Get-ValueDisplay {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Status
    )
    
    if ($Status -eq "Missing" -or $Status -eq "Default") {
        return $null
    }
    
    if ($Name -in $SecretPatterns) {
        return "(hidden)"
    }
    
    if ($Value.Length -gt 30) {
        return "'$($Value.Substring(0, 27))...'"
    }
    
    return "'$Value'"
}

# Track validation state
$ValidationErrors = @()
$MissingVars = @()
$InvalidVars = @()

if ($ShowReport) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $Colors.Header
    Write-Host " Environment Configuration Validation" -ForegroundColor $Colors.Header
    Write-Host "========================================" -ForegroundColor $Colors.Header
}

# Check required variables
if ($ShowReport) {
    Write-Host ""
    Write-Host "Required Variables:" -ForegroundColor $Colors.Info
}

foreach ($service in $RequiredVars.Keys) {
    if ($ShowReport) {
        Write-Host ""
        Write-Host "  [$service]" -ForegroundColor $Colors.Info
    }
    
    foreach ($var in $RequiredVars[$service]) {
        $value = [Environment]::GetEnvironmentVariable($var)
        
        if ($null -eq $value) {
            $status = "Missing"
            $MissingVars += $var
            $ValidationErrors += "Missing required variable: $var"
        } elseif (Test-Placeholder -Value $value) {
            $status = "Placeholder"
            $InvalidVars += "$var=$value"
            $ValidationErrors += "Variable $var has placeholder value"
        } else {
            $formatError = Test-VariableFormat -Name $var -Value $value
            if ($formatError) {
                $status = "Invalid"
                $InvalidVars += "$var=$value"
                $ValidationErrors += "$var format error: $formatError"
            } else {
                $status = "OK"
            }
        }
        
        if ($ShowReport) {
            $icon = Get-StatusIcon -Status $status
            $valueDisplay = Get-ValueDisplay -Name $var -Value $value -Status $status
            
            $message = "    $icon $var"
            if ($valueDisplay) {
                $message += ": $valueDisplay"
            }
            
            $color = if ($status -eq "OK") { $Colors.Success } else { $Colors.Error }
            Write-Host $message -ForegroundColor $color
            
            if ($status -eq "Invalid" -and $formatError) {
                Write-Host "       Error: $formatError" -ForegroundColor $Colors.Error
            }
        }
    }
}

# Check optional variables
if ($ShowReport) {
    Write-Host ""
    Write-Host ""
    Write-Host "Optional Variables:" -ForegroundColor $Colors.Info
}

foreach ($service in $OptionalVars.Keys) {
    if ($ShowReport) {
        Write-Host ""
        Write-Host "  [$service]" -ForegroundColor $Colors.Info
    }
    
    foreach ($varInfo in $OptionalVars[$service]) {
        $var = $varInfo.Name
        $default = $varInfo.Default
        $value = [Environment]::GetEnvironmentVariable($var)
        
        if ($null -eq $value) {
            $status = "Default"
            $valueDisplay = "not set (default: $default)"
        } elseif (Test-Placeholder -Value $value) {
            $status = "Placeholder"
            $valueDisplay = "PLACEHOLDER"
            $ValidationErrors += "Variable $var has placeholder value"
        } else {
            $formatError = Test-VariableFormat -Name $var -Value $value
            if ($formatError) {
                $status = "Invalid"
                $valueDisplay = "INVALID: $formatError"
                $ValidationErrors += "$var format error: $formatError"
            } else {
                $status = "OK"
                $valueDisplay = Get-ValueDisplay -Name $var -Value $value -Status $status
            }
        }
        
        if ($ShowReport) {
            $icon = Get-StatusIcon -Status $status
            $color = switch ($status) {
                "OK" { $Colors.Success }
                "Default" { $Colors.Warning }
                default { $Colors.Error }
            }
            
            $message = "    $icon $var"
            if ($valueDisplay) {
                $message += ": $valueDisplay"
            }
            Write-Host $message -ForegroundColor $color
        }
    }
}

# Check .env file
if ($CheckEnvFile) {
    if ($ShowReport) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor $Colors.Header
    }
    
    $envExists = Test-Path ".env"
    if ($ShowReport) {
        if ($envExists) {
            Write-Host "✅ .env file exists" -ForegroundColor $Colors.Success
        } else {
            Write-Host "⚠️  .env file not found" -ForegroundColor $Colors.Warning
            Write-Host "   Run: cp .env.example .env" -ForegroundColor $Colors.Warning
        }
    }
}

# Check .gitignore
if ($CheckGitignore) {
    $gitignoreExists = Test-Path ".gitignore"
    $envIgnored = $false
    
    if ($gitignoreExists) {
        $gitignoreContent = Get-Content ".gitignore" -Raw
        $envIgnored = $gitignoreContent -match "\.env" -or $gitignoreContent -match "\*\.env"
    }
    
    if ($ShowReport) {
        if ($envIgnored) {
            Write-Host "✅ .env is in .gitignore" -ForegroundColor $Colors.Success
        } else {
            Write-Host "❌ .env is NOT in .gitignore!" -ForegroundColor $Colors.Error
            Write-Host "   Add '*.env' or '.env' to .gitignore to prevent secret leaks!" -ForegroundColor $Colors.Error
            $ValidationErrors += ".env is not in .gitignore"
        }
    }
}

# Summary
if ($ShowReport) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $Colors.Header
    Write-Host " Summary" -ForegroundColor $Colors.Header
    Write-Host "========================================" -ForegroundColor $Colors.Header
}

if ($ValidationErrors.Count -eq 0) {
    if ($ShowReport) {
        Write-Host "✅ All validations passed!" -ForegroundColor $Colors.Success
    }
    exit 0
} else {
    if ($ShowReport) {
        Write-Host "❌ Validation failed with $($ValidationErrors.Count) error(s):" -ForegroundColor $Colors.Error
        foreach ($error in $ValidationErrors) {
            Write-Host "   - $error" -ForegroundColor $Colors.Error
        }
        Write-Host ""
        Write-Host "Fix the errors above and run this script again." -ForegroundColor $Colors.Warning
    }
    
    if ($Strict) {
        exit 1
    }
    exit 0
}
