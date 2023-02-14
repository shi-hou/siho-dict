import os

upgrade_pyinstaller_cmd = 'pip install pyinstaller --upgrade'

'''
-i <FILE.ico or FILE.exe,ID or FILE.icns or Image or "NONE">, 
--icon <FILE.ico or FILE.exe,ID or FILE.icns or Image or "NONE">
    FILE.ico: apply the icon to a Windows executable. FILE.exe,ID: extract the icon with ID from an exe. 
    FILE.icns: apply the icon to the .app bundle on Mac OS. 
    If an image file is entered that isn’t in the platform format (ico on Windows, icns on Mac), 
    PyInstaller tries to use Pillow to translate the icon into the correct format (if Pillow is installed). 
    Use “NONE” to not apply any icon, thereby making the OS show some default (default: apply PyInstaller’s icon). 
    This option can be used multiple times.

-n NAME, --name NAME
    Name to assign to the bundled app and spec file (default: first script’s basename)

--add-data <SRC;DEST or SRC:DEST>
    Additional non-binary files or folders to be added to the executable. 
    The path separator is platform specific, os.pathsep (which is ; on Windows and : on most unix systems) is used. 
    This option can be used multiple times.

--clean
    Clean PyInstaller cache and remove temporary files before building.

-y
    Replace output directory (default: SPECPATH/dist/SPECNAME) without asking for confirmation

-c, --console, --nowindowed
    Open a console window for standard i/o (default). 
    On Windows this option has no effect if the first script is a ‘.pyw’ file.

-w, --windowed, --noconsole
    Windows and Mac OS X: 
        do not provide a console window for standard i/o. 
        On Mac OS this also triggers building a Mac OS .app bundle. 
        On Windows this option is automatically set if the first script is a ‘.pyw’ file. 
    This option is ignored on *NIX systems. 

-D, --onedir
    Create a one-folder bundle containing an executable (default)

-F, --onefile
    Create a one-file bundled executable.
'''
package_cmd = 'pyinstaller ' \
              '-i "assets\icon\logo-icon.ico" ' \
              '-n "siho-dict" ' \
              f'--add-data "assets{os.pathsep}assets" ' \
              '--clean -y -w -D "entry.py"'

if __name__ == '__main__':
    print(os.system(upgrade_pyinstaller_cmd))
    print(os.system(package_cmd))
