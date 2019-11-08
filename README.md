# JSONs in ZIPs editor

## Limitations
At this moment the software is still limitation in functionality. The program doesn't have any kind of user interface yet. Furthermore keys with more keys as it's value, like `"key":{"Key1":"Value1","Key2":"Value2"}`, can't be changed correctly at ones at this moment.

## Windows issue
The windows bash some how doesn't delete directorys with `shutil.rmtree()` on Any of the base windows shells (CMD & PowerShell). This script does work on the Debian shell that can be downloaded on windows.
