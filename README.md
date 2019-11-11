# JSONs in ZIPs editor

## Limitations
At this moment the software is still limitation in functionality. The program doesn't have any kind of user interface yet. Furthermore keys with more keys as it's value, like `"key":{"Key1":"Value1","Key2":"Value2"}`, can't be changed correctly at ones at this moment.

## Windows issue
The windows bash some how doesn't delete directorys with `shutil.rmtree()` on Any of the base windows shells (CMD & PowerShell). This script does work on the Windows Debian shell but on the default command lines on Windows you will get a OSError `The directory is not empty` error when it tries to delete the remaining temporary directory windows. This directory can be deleted manually after the script is has finished.
