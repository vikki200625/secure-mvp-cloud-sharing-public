#$zip_repo.ps1
#Zip the repository contents to the user's Downloads folder
$zipPath = "$env:USERPROFILE\\Downloads\\secure-mvp-cloud-sharing-public.zip"
$src = "C:\\secure_share"
if (Test-Path -Path $src) {
    $destDir = [IO.Path]::GetDirectoryName($zipPath)
    if (-not (Test-Path -Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Compress-Archive -Path "$src\\*" -DestinationPath $zipPath -Force
    Write-Output "Zipped to $zipPath"
} else {
    Write-Output "Source not found: $src"
}
