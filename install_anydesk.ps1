Param(
    [string]$mode,
    [string]$pcId,
    [string]$password
)

# Vérifier si les paramètres requis ont été fournis

if (-not $password) {   
    Write-Host "utilisation: install_anydesk.ps1 <mode> <pcId> <password>" -ForegroundColor Red
    exit
}

if (-not $pcId) {   
    Write-Host "utilisation: install_anydesk.ps1 <mode> <pcId> <password>" -ForegroundColor Red
    exit
}

if (-not $mode) {   
    Write-Host "utilisation: install_anydesk.ps1 <mode> <pcId> <password>" -ForegroundColor Red
    exit
}


# Vérifier si l'utilisateur a des droits d'administration
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Vous devez executer ce script en tant qu'administrateur." -ForegroundColor Red
    exit
}


# Set the URLs for the AnyDesk installer and destination paths
$anyDeskUrl = "https://download.anydesk.com/AnyDesk.exe"

# Create the temp directory if it doesn't exist
if (-not (Test-Path -Path "C:\temp" -PathType Container)) {
    New-Item -ItemType Directory -Path "C:\temp" | Out-Null
    New-Item -ItemType File -Path "C:\temp\anydeskMDP.txt" | Out-Null
}
# Create the AnyDesk directory if it doesn't exist
if (-not (Test-Path -Path "C:\Program Files\AnyDesk" -PathType Container)) {
    New-Item -ItemType Directory -Path "C:\Program Files\AnyDesk" | Out-Null
}

# Create the mdpAnydesk.txt file if it doesn't exist
if (-not (Test-Path -Path "C:\temp\anydeskMDP.txt" -PathType Leaf)) {
    New-Item -ItemType File -Path "C:\temp\anydeskMDP.txt" | Out-Null   
}

# Download AnyDesk installer to the temp directory
Invoke-WebRequest -Uri $anyDeskUrl -OutFile "C:\temp\anydesk.exe"

# Run AnyDesk.exe with the specified arguments for installation
C:\temp\anydesk.exe --install "C:\Program Files\AnyDesk" --start-with-win --create-desktop-icon

Write-Host "Veuillez attendre que AnyDesk soit online" -ForegroundColor Yellow


# tant que anydesk n'est pas connecté a internet, on redemande le statut
do {
    Start-Process -FilePath "C:\temp\anydesk.exe" -ArgumentList "--get-status" -RedirectStandardOutput "C:\temp\AnyDeskStatus.txt" -Wait
    $anydeskStatus = Get-Content -Path "C:\temp\AnyDeskStatus.txt"
    Write-Host "AnyDesk est $anydeskStatus" -ForegroundColor Yellow   
    Start-Sleep -Seconds 3

    } while ($anydeskStatus -ne "online")

# Exécute la commande AnyDesk pour obtenir l'ID
Set-Location -Path "C:\temp"

Start-Process -FilePath "C:\temp\anydesk.exe" -ArgumentList "--get-id" -RedirectStandardOutput "C:\temp\AnyDeskID.txt" -Wait
$idanydesk = Get-Content -Path "C:\temp\AnyDeskID.txt"

# Définition du mot de passe AnyDesk
Write-Output $password | C:\temp\anydesk.exe --set-password
Write-Host "Le mot de passe anydesk est mis a jour" -ForegroundColor Green 


Write-Host "Ajout des donnees dans la base de donnees" -ForegroundColor Green

# Importez le module MySQL Connector/NET  ---------------  ca doit être installé quand on appuie pour ajouter le pc dans la bdd !!!!!!!!!!!!!!!!!!!!!!!!!!!
Import-Module "C:\Program Files (x86)\MySQL\MySQL Connector NET 8.3.0\MySql.Data.dll"

# Paramètres de connexion à la base de données MySQL
$server = "127.0.0.1"
$database = "base_test_stage"
$username = "root"
$passwordBDD = ""
$port = "3308"

# Créez la chaîne de connexion
$connectionString = "Server=$server;Port=$port;Database=$database;User ID=$username;Password=$passwordBDD;"

# Créez un objet de connexion MySQL
$connection = New-Object MySql.Data.MySqlClient.MySqlConnection
$connection.ConnectionString = $connectionString

try {
        # Ouvrez la connexion à la base de données
    $connection.Open()


    if ($mode -eq "tout") {
        #  Mettez à jour la colonne 'data' avec le nouveau JSON
        $queryUpdateData = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.idAnydesk', '$idanydesk') WHERE idPC = $pcId"
        $commandUpdateData = $connection.CreateCommand()
        $commandUpdateData.CommandText = $queryUpdateData
        $commandUpdateData.ExecuteNonQuery() > $null
    }


    
    $queryUpdateData1 = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.mdpAnydesk', '$password') WHERE idPC = $pcId"
    $commandUpdateData = $connection.CreateCommand()
    $commandUpdateData.CommandText = $queryUpdateData1
    $commandUpdateData.ExecuteNonQuery() > $null
    Write-Host "Mise a jour reussie pour le PC avec idPC : $pcId" -ForegroundColor Green
        

} finally {
    # Fermez la connexion à la base de données, même en cas d'erreur
    $connection.Close()
}

# Supprimez les fichiers temporaires
Start-Sleep -Seconds 5
Remove-Item -Path "C:\temp\anydeskMDP.txt"
Remove-Item -Path "C:\temp\AnyDeskStatus.txt"
Remove-Item -Path "C:\temp\AnyDeskID.txt"

Write-Host "Installation et configuration d'AnyDesk terminees" -ForegroundColor Green

