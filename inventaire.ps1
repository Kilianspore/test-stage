Param(
    [string]$modeLancement,
    [string]$groupname,
    [string]$locPC,
    [string]$compteMicrosoft
)

# Vérifier si les paramètres requis ont été fournis
if (-not $groupname) {
    Write-Host "utilisation: inventaire.ps1 <modeLancement> <groupname> <locPC> <compteMicrosft>" -ForegroundColor Red
    exit
}
if (-not $modeLancement) {
    Write-Host "utilisation: inventaire.ps1 <modeLancement> <groupname> <locPC>" -ForegroundColor Red
    exit
}
if (-not $locPC) {
    Write-Host "utilisation: inventaire.ps1 <modeLancement> <groupname> <locPC>" -ForegroundColor Red
    exit
}
if (-not $compteMicrosoft) {
    Write-Host "utilisation: inventaire.ps1 <modeLancement> <groupname> <locPC> <compteMicrosft>" -ForegroundColor Red
    exit
}


# Vérifier si l'utilisateur a des droits d'administration
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Vous devez executer ce script en tant qu'administrateur." -ForegroundColor Red
    exit
}


# Obtenir le nom du PC
$nomPC = $env:COMPUTERNAME
Write-Host "Le nom du PC est " $nomPC -ForegroundColor Green

# Obtenir la marque et le modèle du PC
$computerSystem = Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model
$manufacturer = $computerSystem.Manufacturer
$model = $computerSystem.Model
Write-Host "Le PC est un " $manufacturer " " $model -ForegroundColor Green

# Obtenir la version de Windows
$osVersion = (Get-CimInstance Win32_OperatingSystem).Version
Write-Host "La version de Windows est " $osVersion -ForegroundColor Green

# Obtenir des informations sur le processeur
$processor = Get-CimInstance Win32_Processor | Select-Object Name
$processor = $processor.Name
Write-Host "Le processeur est un " $processor -ForegroundColor Green

# Obtenir la quantité de RAM
$ram = Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum | Select-Object @{Name='TotalRAM';Expression={($_.Sum / 1GB) -as [int]}}
$ram = $ram.TotalRAM
Write-Host "La quantite de RAM est de " $ram "Go" -ForegroundColor Green

# Obtenir la capacité de stockage
$storage = Get-CimInstance Win32_LogicalDisk | Where-Object {$_.DriveType -eq 3} | Measure-Object Size -Sum | Select-Object @{Name='TotalStorage';Expression={($_.Sum / 1GB) -as [int]}}
$storage = $storage.TotalStorage
Write-Host "La capacite de stockage est de " $storage "Go" -ForegroundColor Green

# Obtenir la version d'Office
$OfficeVersionX32        = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' -ErrorAction SilentlyContinue -WarningAction SilentlyContinue) | Select-Object -ExpandProperty VersionToReport
$OfficeVersionX64        = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Office\ClickToRun\Configuration' -ErrorAction SilentlyContinue -WarningAction SilentlyContinue)
if ( $null -ne $OfficeVersionX32 -and $null -ne $OfficeVersionX64) {
  $OfficeVersion = "Both x32 version ($OfficeVersionX32) and x64 version ($OfficeVersionX64) installed!"
} elseif ($null -eq $OfficeVersionX32 -or $null -eq $OfficeVersionX64) {
  $OfficeVersion = $OfficeVersionX32 + $OfficeVersionX64
}
else {
    $OfficeVersion = ""
}
Write-Host "Office version: $OfficeVersion" -ForegroundColor Green

# Obtenir la clé de produit Windows
$productKey = Get-CimInstance -ClassName SoftwareLicensingService
$cleWindows = $productKey | Select-Object -ExpandProperty OA3xOriginalProductKey
Write-Host "La cle de produit Windows est " $cleWindows -ForegroundColor Green

# Obtenir l'utilisateur actuel
$userPC = $env:USERNAME
Write-Host "L'utilisateur actuel est " $userPC -ForegroundColor Green

# Obetenir la date de préparation au format sql datetime
$datePrepaPC = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "La date de preparation est " $datePrepaPC -ForegroundColor Green

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

    # 1. Récupérez l'id du groupe correspondant à $groupename
    $queryGetGroupeId = "SELECT idGroupe FROM groupe WHERE nomGroupe='$groupname'"
    $commandGetGroupeId = $connection.CreateCommand()
    $commandGetGroupeId.CommandText = $queryGetGroupeId
    $groupeId = $commandGetGroupeId.ExecuteScalar()

    # Création du pc dans la base de données
    $queryCreatePC = "INSERT INTO pc (idPC, nomPC, datePrepaPC, dataPC, idGroupe) VALUES (NULL, '$nomPC', '', '{""locPC"": """", ""ramPC"": """", ""userPC"": """", ""marquePC"": """", ""modelePC"": """", ""idAnydesk"": """", ""mdpAnydesk"": """", ""stockagePC"": """", ""processeurPC"": """", ""licenceOffice"": """", ""versionOffice"": """", ""licenceWindows"": """", ""versionWindows"": """", ""compteMicrosoft"": """"}', '$groupeId')"
    $commandCreatePC = $connection.CreateCommand()
    $commandCreatePC.CommandText = $queryCreatePC
    $commandCreatePC.ExecuteNonQuery() > $null

    # 2. Récupérez l'id du PC correspondant à $nomPC dans $groupname
    $queryGetPCId = "SELECT pc.idPC FROM pc,groupe WHERE pc.idgroupe=groupe.idgroupe and groupe.nomGroupe='$groupname' and pc.nomPC = '$nomPC'"
    $commandGetPCId = $connection.CreateCommand()
    $commandGetPCId.CommandText = $queryGetPCId
    $pcId = $commandGetPCId.ExecuteScalar()

    if ($null -ne $pcId) {

        # 3. Mettez à jour la colonne 'data' avec le nouveau JSON
        $queryUpdateRAM = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.ramPC', '$ram') WHERE idPC = $pcId"
        $commandUpdateRAM = $connection.CreateCommand()
        $commandUpdateRAM.CommandText = $queryUpdateRAM
        $commandUpdateRAM.ExecuteNonQuery() > $null

        $queryUpdateUserPC = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.userPC', '$userPC') WHERE idPC = $pcId"
        $commandUpdateUserPC = $connection.CreateCommand()
        $commandUpdateUserPC.CommandText = $queryUpdateUserPC
        $commandUpdateUserPC.ExecuteNonQuery() > $null

        $queryUpdateLicenceWindows = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.licenceWindows', '$cleWindows') WHERE idPC = $pcId"
        $commandUpdateLicenceWindows = $connection.CreateCommand()
        $commandUpdateLicenceWindows.CommandText = $queryUpdateLicenceWindows
        $commandUpdateLicenceWindows.ExecuteNonQuery() > $null

        $queryUpdateLocPC = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.locPC', '$locPC') WHERE idPC = $pcId"
        $commandUpdateLocPC = $connection.CreateCommand()
        $commandUpdateLocPC.CommandText = $queryUpdateLocPC
        $commandUpdateLocPC.ExecuteNonQuery() > $null

        $queryUpdateVersionOffice = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.versionOffice', '$OfficeVersion') WHERE idPC = $pcId"
        $commandUpdateVersionOffice = $connection.CreateCommand()
        $commandUpdateVersionOffice.CommandText = $queryUpdateVersionOffice
        $commandUpdateVersionOffice.ExecuteNonQuery() > $null

        $queryUpdateCompteMicrosoft = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.compteMicrosoft', '$compteMicrosoft') WHERE idPC = $pcId"
        $commandUpdateCompteMicrosoft = $connection.CreateCommand()
        $commandUpdateCompteMicrosoft.CommandText = $queryUpdateCompteMicrosoft
        $commandUpdateCompteMicrosoft.ExecuteNonQuery() > $null

        $queryUpdateStorage = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.stockagePC', '$storage') WHERE idPC = $pcId"
        $commandUpdateStorage = $connection.CreateCommand()
        $commandUpdateStorage.CommandText = $queryUpdateStorage
        $commandUpdateStorage.ExecuteNonQuery() > $null
        
        $queryUpdateProcessor = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.processeurPC', '$processor') WHERE idPC = $pcId"
        $commandUpdateProcessor = $connection.CreateCommand()
        $commandUpdateProcessor.CommandText = $queryUpdateProcessor
        $commandUpdateProcessor.ExecuteNonQuery() > $null
        
        $queryUpdateOSVersion = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.versionWindows', '$osVersion') WHERE idPC = $pcId"
        $commandUpdateOSVersion = $connection.CreateCommand()
        $commandUpdateOSVersion.CommandText = $queryUpdateOSVersion
        $commandUpdateOSVersion.ExecuteNonQuery() > $null

        $queryUpdateManufacturer = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.marquePC', '$manufacturer') WHERE idPC = $pcId"
        $commandUpdateManufacturer = $connection.CreateCommand()
        $commandUpdateManufacturer.CommandText = $queryUpdateManufacturer
        $commandUpdateManufacturer.ExecuteNonQuery() > $null

        $queryUpdateModel = "UPDATE pc SET dataPC = JSON_SET(dataPC, '$.modelePC', '$model') WHERE idPC = $pcId"
        $commandUpdateModel = $connection.CreateCommand()
        $commandUpdateModel.CommandText = $queryUpdateModel
        $commandUpdateModel.ExecuteNonQuery() > $null

        #faire ça uniquement $modeLancement = "neuf"
        if ($modeLancement -eq "neuf") {
            $queryUpdateDatePrepaPC = "UPDATE pc SET datePrepaPC = '$datePrepaPC' WHERE idPC = $pcId"
            $commandUpdateDatePrepaPC = $connection.CreateCommand()
            $commandUpdateDatePrepaPC.CommandText = $queryUpdateDatePrepaPC
            $commandUpdateDatePrepaPC.ExecuteNonQuery() > $null
        } else {
            $queryUpdateDatePrepaPC = "UPDATE pc SET datePrepaPC = Null WHERE idPC = $pcId"
            $commandUpdateDatePrepaPC = $connection.CreateCommand()
            $commandUpdateDatePrepaPC.CommandText = $queryUpdateDatePrepaPC
            $commandUpdateDatePrepaPC.ExecuteNonQuery() > $null
        }

        

        Write-Host "Mise a jour reussie pour le PC nomme : $nomPC" -ForegroundColor Green
        
    } else {
        Write-Host "Aucun PC trouve dans la base avec le nom '$nomPC' et le groupe nomme '$groupname'" -ForegroundColor Red
    }
} finally {
    # Fermez la connexion à la base de données, même en cas d'erreur
    $connection.Close()
}

