<#
    YAML normalization helper (idempotent best-effort):
        * Removes CP1252 0x9D bytes
        * Normalizes line endings to LF
        * Trims trailing spaces
        * Ensures minimum two spaces before inline '#'
        * (Optional) can quote top-level 'on' key (disabled by default)
        * Ensures final newline
        * Reports lines > max length (default 120) for manual wrapping

    Limitations / heuristics:
        * Does not parse YAML AST; uses regex/string heuristics.
        * Will skip spacing adjustments for lines containing '://.*#' (likely URLs) to avoid breaking fragments.
        * Root key quoting only applied to an unquoted leading 'on:' exactly at start-of-line.

        Usage examples: 
        Dry run: pwsh yaml_ducttape.ps1 -DryRun 
        Apply with defaults: pwsh yaml_ducttape.ps1 
        Custom max length: pwsh yaml_ducttape.ps1 -MaxLength 100 
        Quote root on keys (rarely needed): pwsh yaml_ducttape.ps1 -QuoteOnKey

    NOTE: Always review diffs before committing.
#>

param(
  [int]$MaxLength = 120,
  [switch]$QuoteOnKey,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-YamlTrackedPaths {
  git ls-files -- '*.yml' '*.yaml' 'mkdocs.yml' 'bandit.yaml'
}

$yaml = Get-YamlTrackedPaths | Where-Object { $_ }
if (-not $yaml) {
  Write-Host 'No YAML files matched.'
  return
}

$modified = @()
$issues = @()

foreach ($p in $yaml) {
  if (-not (Test-Path -LiteralPath $p)) { continue }
  $raw = [IO.File]::ReadAllBytes($p)

  # Remove CP1252 0x9D bytes (rare smart quote control)
  if ($raw -contains 0x9d) { $raw = $raw | Where-Object { $_ -ne 0x9d } }

  $text = [Text.Encoding]::UTF8.GetString($raw)
  # Normalize newlines
  $text = $text -replace "`r`n|`r", "`n"

  $lines = $text -split "`n"

  $changed = $false

  for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]

    # Trim trailing whitespace
    $trimmed = $line -replace '\s+$', ''
    if ($trimmed -ne $line) { $line = $trimmed; $changed = $true }

    # Normalize flow-style spacing in a conservative way (outside quotes)
    # 1) Inside { } and [ ]: collapse inner excess spaces but keep one space.
    $line = $line -replace '(\{)\s+', '$1 '           # after {
    $line = $line -replace '\s+(\})', ' $1'           # before }
    $line = $line -replace '(\[)\s+', '$1 '           # after [
    $line = $line -replace '\s+(\])', ' $1'           # before ]

    # 2) No extra spaces just inside delimiters: "{  a: b  }" -> "{ a: b }"
    $line = $line -replace '(\{\s)\s+', '$1'
    $line = $line -replace '\s+(\s\})', ' $1'
    $line = $line -replace '(\[\s)\s+', '$1'
    $line = $line -replace '\s+(\s\])', ' $1'

    # 3) After colon in flow context: collapse 2+ spaces to one, but avoid URLs "://"
    if ($line -notmatch '://') {
      $line = $line -replace ':\s{2,}', ': '
    }

    # 4) Collapse spaces inside single-element braces/brackets: "{  x }" -> "{ x }"
    $line = $line -replace '\{\s+([^}\s][^}]*)\s+\}', '{ $1 }'
    $line = $line -replace '\[\s+([^\]\s][^\]]*)\s+\]', '[ $1 ]'

    # Inline comment spacing heuristic:
    #   * Skip if full-line comment
    #   * Skip if no '#'
    #   * Skip if looks like a URL containing '#': protocol://.*#
    if ($line -notmatch '^\s*#' -and $line -match '#' -and $line -notmatch '://[^\s#]*#') {
      $hashIndex = $line.IndexOf('#')
      if ($hashIndex -gt 0) {
        $before = $line.Substring(0, $hashIndex)
        $after = $line.Substring($hashIndex)
        # Only enforce if there's at least one space before '#', but not already two, to avoid smashing scalars
        if ($before -match '\s$' -and $before -notmatch '\s{2}$') {
          $before = ($before -replace '\s+$', '') + '  '
          $line = $before + $after
          $changed = $true
        }
      }
    }
# --- Safe flow-style spacing normalization (single-line only) ---
$before = $line

# Skip block scalars entirely
if ($line -match '^\s*[|>]-?\s*$') {
    # do nothing
}
else {
    # Only operate when the open and close delimiter are on the SAME line.
    $hasBracePair   = $line -match '\{.*\}'
    $hasBracketPair = $line -match '\[.*\]'

    if ($hasBracePair -or $hasBracketPair) {
        # 1) Strip padding just inside {} and [] on single-line flows
        #    "{  a: 1  }" -> "{a: 1}", "[  a,  b  ]" -> "[a, b]"
        $line = $line -replace '(\{|\[)\s+', '$1'
        $line = $line -replace '\s+(\}|\])', '$1'

        # 2) Normalize commas: no space before, single space after
        $line = $line -replace '\s+,', ','
        $line = $line -replace ',\s{2,}', ', '

        # 3) Normalize colon spacing inside flow (avoid URLs)
        if ($line -notmatch '://') {
            $line = $line -replace ':\s{2,}', ': '
        }
    }
    else {
        # Multi-line flow or non-flow: DO NOT touch indentation or closers.
        # Intentionally left blank.
    }
}

if ($line -ne $before) { $changed = $true }
# --- end safe normalization ---

    $lines[$i] = $line
  }

  # Rejoin early for root key transform
  $joined = [string]::Join("`n", $lines)
  if ($QuoteOnKey) {
    # Quote ONLY an unquoted root-level 'on:' key at start-of-line; ensure space after colon for yamllint.
    $newLines = @()
    $localChanged = $false
    foreach ($l in ($joined -split "`n")) {
      if ($l -match '^(on):(\s*.*)$' -and $l -notmatch '^"on":') {
        $l = $l -replace '^on:', '"on":'
        # Ensure a space after colon if immediately followed by non-space
        if ($l -match '^"on":\S') { $l = $l -replace '^"on":', '"on": ' }
        $localChanged = $true
      }
      $newLines += $l
    }
    if ($localChanged) { $joined = [string]::Join("`n", $newLines); $changed = $true }
  }

  if (-not $joined.EndsWith("`n")) { $joined += "`n"; $changed = $true }

  if ($changed) {
    if ($DryRun) {
      Write-Host "[DRY] Would normalize: $p"
    }
    else {
      [IO.File]::WriteAllText($p, $joined, (New-Object Text.UTF8Encoding($false)))
      $modified += $p
    }
  }
  Write-Host "Scanning $p"


  # Length report (use current state: joined)
  $currentLines = $joined -split "`n"
  for ($i = 0; $i -lt $currentLines.Count; $i++) {
    $ln = $currentLines[$i]
    if ($ln.Length -gt $MaxLength) {
      $issues += [PSCustomObject]@{ File = $p; Line = $i + 1; Length = $ln.Length; Snippet = $ln.Substring(0, [Math]::Min(160, $ln.Length)) }
    }
  }
}

Write-Host "`n==== YAML Normalization Summary ===="
Write-Host ("Modified files: {0}" -f ($modified.Count))
if ($modified) { $modified | ForEach-Object { Write-Host "  - $_" } }

Write-Host "`n==== Lines > $MaxLength chars (manual wrap suggested) ===="
if (-not $issues) { Write-Host 'None' } else { $issues | ForEach-Object { Write-Host ("{0}:{1} ({2}) {3}" -f $_.File, $_.Line, $_.Length, $_.Snippet) } }

Write-Host "`nDone." 
