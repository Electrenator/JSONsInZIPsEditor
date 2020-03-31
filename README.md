# JSONs in ZIPs editor
Like the description of this repository says is the purpose of this program to change JSON files inside ZIP files way faster than Humans can by hand. This with the hope of saving hours of manually editing ZIPs, like when a game updates and you only have to change the version numbers of mod ZIPs, which for example is being done with [BeatSaber mods](https://github.com/RedBrumbler/BMBFCustomSabers) when the changes to the game allow for this.


## Necessary things
Only python 3+ is necessary. This script will *not* work on Python 2 and has been tested on Python 3.8.


## Limitations
At this moment the software is still limitation in functionality. The JSON values to search for and to replace can only be input into the script when it's running at this moment. There isn't another way written yet.\
But please keep in mind that it can still make some mistakes in some rare unnoticed cases. So **please make a backup before running this script** in the folder where you have put it in. The script can always be run again with the same inputs to check if the JSON syntax is still correct inside of the zips.


## Input-able keys or values
Inputs need to be in correct JSON before the program can make use of the input so that it can also replace the key with the value in valid JSON.

### The input of keys
The only way to input keys is to use the JSON syntax for a string. This would be `"key"` but the program also accepts `'key'`, which will be translated to the JSON syntax version.

### The input of values
Values are a bit more free. These can use all the JSON data storing types as input, like objects, arrays, strings, numbers and binaries. You can input it in the same way as done in JSON files but `'string'` is also allowed as a string input. For more info look [here on json.org](https://www.json.org/)


## Windows issue
The windows bash some how doesn't delete directorys with `shutil.rmtree()` on Any of the base windows shells (CMD & PowerShell). This script does work on the Windows Debian shell but on the default command lines on Windows you will get a OSError `The directory is not empty` error when it tries to delete the remaining temporary directory windows. This directory can be deleted manually after the script has finished.
