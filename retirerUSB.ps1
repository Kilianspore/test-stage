$premierelettre = $PSScriptRoot.Substring(0,1)
$Eject = New-Object -comObject Shell.Application    
$Eject.NameSpace(17).ParseName($premierelettre+":").InvokeVerb("Eject")

