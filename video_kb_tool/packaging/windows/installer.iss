#define MyAppName "Video KB Desktop"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "OpenAI Generated"
#define MyAppExeName "VideoKBDesktop.exe"
#define MySourceDir "..\..\dist\VideoKBDesktop"

[Setup]
AppId={{C1E96795-53DA-4A42-9F93-8A9C97A90B2B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\VideoKBDesktop
DefaultGroupName=Video KB Desktop
AllowNoIcons=yes
OutputDir=output
OutputBaseFilename=VideoKBDesktop-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Video KB Desktop"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Video KB Desktop"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 Video KB Desktop"; Flags: nowait postinstall skipifsilent
