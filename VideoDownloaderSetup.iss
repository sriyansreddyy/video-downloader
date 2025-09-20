; Video Downloader Installer Script
; Save this as VideoDownloaderSetup.iss

[Setup]
; Application Information
AppName=Video Downloader
AppVersion=1.0.0
AppVerName=Video Downloader 1.0.0
AppPublisher=Video Downloader
AppCopyright=Copyright (C) 2025

; Installation Settings
DefaultDirName={autopf}\Video Downloader
DefaultGroupName=Video Downloader
AllowNoIcons=yes

; Output Configuration
OutputDir=InstallerOutput
OutputBaseFilename=VideoDownloaderSetup
Compression=lzma
SolidCompression=yes

; Installer Appearance
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; 

[Files]
Source: "D:\Desktop\Sriyans\py\youtube-downloader1\dist\"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{autoprograms}\Video Downloader"; Filename: "{app}\VideoDownloader.exe"; WorkingDir: "{app}"

; Desktop shortcut (only if task selected)
Name: "{autodesktop}\Video Downloader"; Filename: "{app}\VideoDownloader.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Launch the app after installation
Filename: "{app}\VideoDownloader.exe"; Description: "Launch Video Downloader now"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"
