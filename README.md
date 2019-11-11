# JSONs in ZIPs editor
Like the description of this repository says is the purpose of this program to change JSON files inside ZIP files way faster than Humans can by hand. This with the hope of saving hours of manually editing ZIPs, like when a game updates and you only have to change the version numbers of mod ZIPs, which for example is being done with [BeatSaber mods](https://github.com/RedBrumbler/BMBFCustomSabers) when the changes to the game allow for this.

## Limitations
At this moment the software is still limitation in functionality. The program doesn't have any kind of user interface yet. This makes the operation of the program a bit harder than necessary. The only way to change the search key or the replacement value is to change it manually in the code. There is a comment there that will help a bit with letting this program do what you want it to but please keep in mind that it usually runs even when there is a mistake in that variable input. So **please make a backup before running this script** in the folder where you have put it in. The script can always be run again to check if the JSON syntax is still correct

## Windows issue
The windows bash some how doesn't delete directorys with `shutil.rmtree()` on Any of the base windows shells (CMD & PowerShell). This script does work on the Windows Debian shell but on the default command lines on Windows you will get a OSError `The directory is not empty` error when it tries to delete the remaining temporary directory windows. This directory can be deleted manually after the script has finished.
