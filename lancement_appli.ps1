$python = Get-Command python -ErrorAction SilentlyContinue
$pythonInstallPath = "https://www.python.org/ftp/python/3.10.4/python-3.10.4-amd64.exe"
$pythonInstallerPath = "C:\temp\python-installer.exe"

$mysqlConnectorInstallerPath = "C:\Users\kilia\Desktop\stage\test-stage\mysql-connector-net-8.3.0.msi"


# Vérifier si Python est installé
if (-not $python) {
    $installPython = Read-Host "Python n'est pas installé sur votre machine. Voulez-vous l'installer? (O/N)"
    if ($installPython -eq "O") {
        # Télécharger l'installateur de Python
        Invoke-WebRequest -Uri $pythonInstallPath -OutFile $pythonInstallerPath
        # Installer Python
        Start-Process -FilePath $pythonInstallerPath -Wait
    }
    else {
        Write-Host "L'application ne peut pas être lancée sans Python."
        Exit
    }
}

# Vérifier si le connecteur MySQL est installé
if (-not (Test-Path -Path "C:\Program Files (x86)\MySQL\MySQL Connector Net 8.0.29\MySql.Data.dll" -PathType Leaf)) {
    $installMySQLConnector = Read-Host "Le connecteur MySQL n'est pas installé sur votre machine. Voulez-vous l'installer? (O/N)"
    if ($installMySQLConnector -eq "O") {
        # Installer le connecteur MySQL
        Start-Process -FilePath $mysqlConnectorInstallerPath -Wait


        Pause
    }
    else {
        Write-Host "L'application peut ne pas fonctionner correctement sans le connecteur MySQL."
    }
}

# Lancer l'application
python .\app.py
