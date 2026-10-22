param([Parameter(Mandatory = $true)][string]$Subnet)
$ErrorActionPreference = 'Stop'
if ($Subnet -notmatch '^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$') {
    throw 'Indique el CIDR IPv4 real del router, por ejemplo 192.168.1.0/24.'
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Esta regla requiere PowerShell como administrador.'
}
$backend = 'C:\Program Files\Docker\Docker\resources\com.docker.backend.exe'
if (-not (Test-Path -LiteralPath $backend)) { throw 'No se encontro el backend de Docker.' }
$display = 'Proyecto2 MPI Docker LAN privada'
if (Get-NetFirewallRule -DisplayName $display -ErrorAction SilentlyContinue) {
    throw 'La regla ya existe. Revise su subred antes de reemplazarla.'
}
New-NetFirewallRule -DisplayName $display -Direction Inbound -Action Allow `
    -Profile Private -Program $backend -RemoteAddress $Subnet -Protocol TCP
