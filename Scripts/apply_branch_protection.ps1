param(
    [Parameter(Mandatory = $true)]
    [string]$Repository,

    [string]$Branch = "modularize-v1.34"
)

$ErrorActionPreference = "Stop"

gh api `
    --method PUT `
    -H "Accept: application/vnd.github+json" `
    "/repos/$Repository/branches/$Branch/protection" `
    -f required_status_checks.strict=true `
    -f enforce_admins=true `
    -f required_pull_request_reviews.required_approving_review_count=1 `
    -f restrictions=

Write-Output "Requested branch protection update for $Repository branch $Branch."
