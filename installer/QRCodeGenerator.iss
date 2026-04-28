#define MyAppName "QR Code Generator"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Ahmer Kavas"
#define MyAppExeName "QRCodeGenerator.exe"
#define MyAppIcon "..\assets\app.ico"

[Setup]
AppId={{4DFA048B-A4EE-44A7-B7F1-8C583964D10D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=QRCodeGeneratorSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
#if FileExists(MyAppIcon)
SetupIconFile={#MyAppIcon}
#endif

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
