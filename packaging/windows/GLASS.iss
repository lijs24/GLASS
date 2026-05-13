#define MyAppName "GLASS"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "GLASS contributors"
#define MyAppExeName "glass.cmd"

[Setup]
AppId={{A6E26844-8789-4C67-A46E-1B08E8B2F2E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\GLASS
DefaultGroupName=GLASS
DisableProgramGroupPage=yes
OutputDir=..\..\.release\windows
OutputBaseFilename=GLASS-Setup-win64
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "..\..\.release\windows\GLASS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GLASS Doctor"; Filename: "{app}\glass-doctor.cmd"
Name: "{group}\GLASS Command Prompt"; Filename: "{cmd}"; Parameters: "/K cd /d ""{app}"" && glass.cmd --help"

[Run]
Filename: "{app}\glass-doctor.cmd"; Description: "Run GLASS Doctor"; Flags: postinstall nowait skipifsilent
