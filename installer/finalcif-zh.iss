; Inno Setup script for the Chinese FinalCif edition.
; Build with installer\build_installer.ps1 (it stages build\FinalCif-zh first).

#define MyAppName "FinalCif 中文版"
#define MyAppVersion "180"
#define MyAppPublisher "Honghao Cao"
#define MyAppURL "https://github.com/honghaocao838/FinalCif-zh"
#define MyAppExeName "finalcif.exe"

[Setup]
AppId={{8D4C0F52-6B3E-4F1A-9C2D-7A5E1B3C9D41}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\FinalCif-zh
DisableProgramGroupPage=yes
DisableDirPage=no
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
AppMutex=FinalCifSetupMutex
ShowLanguageDialog=no
OutputDir=..\dist
OutputBaseFilename=FinalCif-zh-v180-setup-x64
SetupIconFile=..\finalcif\icon\finalcif2.ico
VersionInfoVersion=180.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=180

[Languages]
Name: "chinesesimp"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: checkedonce

[Files]
Source: "..\build\FinalCif-zh\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\FinalCif 中文版"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\FinalCif 中文版"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 FinalCif 中文版"; Flags: nowait postinstall skipifsilent
