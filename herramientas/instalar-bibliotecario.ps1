param([string]$Proyecto = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$base = (Resolve-Path -LiteralPath $Proyecto).Path
$programa = Join-Path $base 'biblioteca.py'
if (!(Test-Path -LiteralPath $programa -PathType Leaf)) { throw 'No se encontró biblioteca.py en el proyecto.' }
$python = (Get-Command pythonw.exe -ErrorAction Stop).Source
$cli = (Get-Command codex.exe -ErrorAction Stop).Source
$inicio = [Environment]::GetFolderPath('Startup')
if (!$inicio) { throw 'La cuenta actual no tiene carpeta de inicio.' }
$shell = New-Object -ComObject WScript.Shell
$enlace = $shell.CreateShortcut((Join-Path $inicio 'MarketingIA - Biblioteca audiovisual.lnk'))
$enlace.TargetPath = $python
$enlace.Arguments = ('"{0}" --codex "{1}" vigilar' -f $programa, $cli)
$enlace.WorkingDirectory = $base
$enlace.Description = 'Clasificar videos nuevos de las campañas de MarketingIA'
$enlace.WindowStyle = 7
$enlace.Save()
$proceso = Start-Process -FilePath $python -ArgumentList $enlace.Arguments -WorkingDirectory $base -WindowStyle Hidden -PassThru
Write-Output ('Inicio automático guardado. Proceso solicitado: ' + $proceso.Id)
