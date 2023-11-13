[Setup]
AppName=YourApp
AppVersion=1.0
DefaultDirName={pf}\YourApp
DefaultGroupName=YourApp
OutputDir=Output
OutputBaseFilename=YourAppSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "path\to\your\app\*"; DestDir: "{app}"
