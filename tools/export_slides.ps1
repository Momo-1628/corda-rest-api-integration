# Exports every slide of a .pptx to PNG (1920x1080) with PowerPoint COM (LibreOffice is not installed).
param([string]$Pptx, [string]$OutDir)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $OutDir -Filter *.png -ErrorAction SilentlyContinue | Remove-Item
$app = New-Object -ComObject PowerPoint.Application
try {
    # Open(FileName, ReadOnly, Untitled, WithWindow)
    $pres = $app.Presentations.Open((Resolve-Path $Pptx).Path, -1, 0, 0)
    $i = 0
    foreach ($slide in $pres.Slides) {
        $i++
        $slide.Export((Join-Path (Resolve-Path $OutDir).Path ("slide_{0:D2}.png" -f $i)), "PNG", 1920, 1080)
    }
    $pres.Close()
    Write-Host "Exported $i slides to $OutDir"
} finally {
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
