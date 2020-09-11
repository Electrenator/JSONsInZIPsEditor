#!/usr/bin/python3
from zipfile import ZipFile as zipFile
import os, random, json, time, shutil, sys
from enum import IntEnum, auto # Needs python 3.4+

'''TODO:
    - Add support for command-line options (And add --help of course)
    - Add option for verbose instead of spamming a log (-v)
    - Add option for only checking the JSON files (--check-only)
    - Add support for putting replacement key and variable in as a command-line variable
'''

# Setup necessary classes
class settingArgTypes(IntEnum):
        # Argument types used for remembering what input arguments is what.
        INVAL = 0 # Giberish
        EXECUTION_FILE = auto() # First argument (executed file)
        COMPACT = auto() # -v or -vbr
        LONG = auto() # --help
        LONG_COMPLEX = auto() # --set_mode x (TODO: make work)
        LONG_COMPLEX_CHILD = auto() # the x from the LONG_COMPLEX comment


class argumentSettings(object):
    # Creates class for helping argument setting setup
    # and info showing

    class varOrder(IntEnum):
        # varOrder used for remembering order of data in varAvailable
        trigger = 0
        desc = auto()
        isComplex = auto()
        allowedEntry = auto()

    # Entry as: [trigger, description, is complex bool (0 if unset), list of allowed entries (TODO) (only with complex bool. 0 if unset)]
    varAvailable = [
        ["-help", "Shows this help list", 0, []],
    ]

    def __init__(self, toAddVarSettings):
        # Add wanted variables to varAvailable list
        for indexSet in toAddVarSettings:
            self.varAvailable.append(indexSet)

    def isUsed(self, trigger:str, argTrigType:settingArgTypes = None) -> bool:
        # Check if trigger value is set in varAvailable, returnes bool

        # Remove '-' from begin if there
        if trigger[0] == '-': trigger = trigger[1:]

        # Filtering and processing for COMPACT type
        if argTrigType == settingArgTypes.COMPACT:
            triggerLen = len(trigger)
            if triggerLen > 1:
                # Has more than one character, make character
                for triggerChar in trigger:
                    triggerCharUsed = self.isUsed(triggerChar, argTrigType)
                    if triggerCharUsed == 0:
                        # One of variables isn't used
                        return 0
                return 1

        # Great for LONG types but COMPACT needs above filtering
        for entry in self.varAvailable:
            if entry[0] == trigger:
                return 1
        return 0

    def getInfo(self, trigger:str, infoType:varOrder) -> str or int:
        # This function searches for trigger and gets his value to return
        #   at the infoType place
        for i in self.varAvailable:
            if i[self.varOrder.trigger] == trigger:
                # Found trigger, now return value if able too
                try:
                    return i[infoType]
                except IndexError:
                    return None
        return None

    def setVal(self, trigger, value):
        # TODO: Add setting setup
        pass

    def getVal(self, trigger):
        # TODO: Make setting retrival work
        pass


def searchDirFor(directory, startsW, endsW):
    ''' Searches recursively in the specified directory for files that start with "startW" and end with "endsW" '''
    foundTarget = []

    for file in os.listdir(directory):
        if (file.endswith(endsW) and file.startswith(startsW)):
            foundTarget.append(os.path.join(directory, file))

        elif (os.path.isdir(os.path.join(directory, file))):
            foundTarget += searchDirFor(os.path.join(directory, file), startsW, endsW)
    return foundTarget


def displayArray(array, description):
    ''' Does as the name says with a nice & readable format '''
    temp = ''
    lenArray = len(array)
    for i in range(lenArray):
        if len(temp) == 0:
            temp += '"'+array[i]+'"'
        elif i+1 == lenArray:
            temp += ' and "'+array[i]+'"'
        else:
            temp += ', "'+array[i]+'"'
    print(timeStamp(timeStart), description+(':' if lenArray != 0 else ''), temp)


def getFileName(directory):
    ''' Gets the name of the specified file without extension and dictionary '''
    splitUpDirectory = directory.split('/')
    fileName = splitUpDirectory[len(splitUpDirectory)-1].rsplit('.', 1)[0]
    return fileName


def jsonChangeValue(file, key, value) -> int:
    '''
        Reads specified json file, changes it and saves that change
        Returns hasDataChanged bool (1 if changed 0 if has not)
    '''
    print(f'{timeStamp(timeStart)} Changing "{key}" to '+str(value).replace("'",'"')+f' in "{file}"', end=printEnd())

    # Read data
    useEncoding = None
    try:
        with open(file, 'r') as f:
            try:
                data = json.loads(f.read())
            finally:
                f.close()
    except ValueError:
        with open(file, 'r', encoding='utf-8-sig') as f:
            try:
                data = json.loads(f.read())
                useEncoding = 'utf-8-sig'
            finally:
                f.close()

    # Change data
    dataAltered, totalChanges = searchAndReplace(data, key, value)
    hasDataChanged = 1 if totalChanges > 0 else 0

    # Rewrite data if changed
    # (truncates/removes existing data in file)
    if hasDataChanged != 0:
        if useEncoding != None:
            with open(file, 'w', encoding=useEncoding) as f:
                try:
                    json.dump(dataAltered, f, indent=4)
                finally:
                    f.close()
        else:
            with open(file, 'w') as f:
                try:
                    json.dump(dataAltered, f, indent=4)
                finally:
                    f.close()

    print('done!', '(changed {} keys)'.format(totalChanges) if hasDataChanged == 1 else '(no change)')
    return hasDataChanged


def searchAndReplace(var, searchKey, newValue, changes:int = 0):
    '''
        Searches and replaces values in a dictionary and lists with the specified key
        Returns new var and amount of changes (int)
    '''
    if type(var) == dict:
        for key in var.keys():
            if key == searchKey:
                var[key] = newValue
                changes += 1
            elif type(var[key]) == dict or type(var[key]) == list:
                var[key], newChanges = searchAndReplace(var[key], searchKey, newValue)
                changes += newChanges
        return var, changes
    elif type(var) == list:
        for item in var:
            i = var.index(item)
            if type(var[i]) == dict or type(var[i]) == list:
                var[i], newChanges = searchAndReplace(var[i], searchKey, newValue)
                changes += newChanges
        return var, changes
    else:
        raise TypeError('Input not a dict or list (the only dicts and lists are suported)')


def timeStamp(timeStart):
    return f'[{round(time.time()-timeStart, 3)}s]'


def printEnd():
    return '...    '


def isValidJSON(data):
    try:
        json.loads(data)
        return True
    except:
        return False


def getInputJSON():
    syntaxExceptions = ("true", "false", "null") # For allowing these as inputs even if capitalised

    inputKey = input('Input JSON key: ').replace("'",'"')
    inputValue = input('Input new JSON value: ').replace("'",'"')

    # Check for exceptions
    for entry in syntaxExceptions:
        if inputValue.lower() == entry:
            inputValue = entry

    inputData = '{'+f'{inputKey}:{inputValue}'+'}'

    if isValidJSON(inputData) == True:
        return inputKey.replace('"',"").replace("'",""), inputData
    else:
        print('\nThis input will give you the following invalid JSON data:', '\n{'+inputKey+':'+inputValue+'}\n'+'Please give a valid JSON value and JSON key\n')
        return getInputJSON()


def getConformation(q):
    a = input(str(q)+" (y or n) ")
    if "y" == a.lower() or "yes" == a.lower():
        return True
    elif "n" == a.lower() or "no" == a.lower():
        return False
    else:
        print("That doesn't look like a conformation. Please put one in")
        return getConformation(q)


def hasSubStr(targetStr:str, thisStr:str, mode:int=0) -> bool:
    # Looks for str inside of str and returns 1 if found, 0 if not
    # Modes:
    #   0 - (default) searches whole str
    #   1 - Only search front with length of targetStr
    #   2 - Only search back with length of targetStr

    targetStrLen = len(targetStr)
    if mode == 0:
        if targetStr in thisStr:
            return 1
    elif mode == 1:
        if targetStr in thisStr[:targetStrLen]:
            return 1
    elif mode == 2:
        if targetStr in thisStr[:-targetStrLen - 1:-1][::-1]:
            return 1
    return 0


def hasAllowedChars(thisStr:str, allowedChars:str) -> bool:
    # Function checks if thisStr ONLY has allowedChars in it.
    # Returns true if it does, false if not
    for char in thisStr:
        if char not in allowedChars:
            return 0
    return 1


def getSettingArgType(arg:str, prevArgType:int) -> settingArgTypes:
    # Function looks at Argument to determin the type, then returns the type
    allowedCharsCompact = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVXYZ"

    if hasSubStr('-', arg, 1) != 1:
        # Is invalid but may be LONG_COMPLEX_CHILD
        if prevArgType == settingArgTypes.LONG:
            return settingArgTypes.LONG_COMPLEX_CHILD
        return settingArgTypes.INVAL

    # Is argument, check if longer
    if hasSubStr('--', arg, 1) != 1:
        # Is probably of type compact, testing for invalid characters
        if hasAllowedChars(arg[1:], allowedCharsCompact) == 1:
            return settingArgTypes.COMPACT # Is a valid compact type

        return settingArgTypes.INVAL # Invalid

    # Is longer
    return settingArgTypes.LONG


def getSettings(argsEnv:list, argsSettingsUsed:list == None) -> argumentSettings:
    # This function gets the enviroment arguments and processes them.
    # It should (TODO) return the settings themself

    settings = argumentSettings(argsSettingsUsed)

    # Look for argument type
    argHasType = [settingArgTypes.EXECUTION_FILE]
    counter = 1
    for arg in argsEnv[1:]:
        argHasType.append(getSettingArgType(arg, argHasType[-1]))

        # Check for LONG_COMPLEX_CHIELD, if found set previous as LONG_COMPLEX
        if argHasType[-1] == settingArgTypes.LONG_COMPLEX_CHILD:
            # Check if argsEnv[counter - 1] can get LONG_COMPLEX
            if settings.getInfo(argsEnv[counter - 1][1:], settings.varOrder.isComplex) != 1:
                argHasType[-1] = settingArgTypes.INVAL
            else: 
                argHasType[-2] = settingArgTypes.LONG_COMPLEX

        # Check if trigger is used
        if argHasType[-1] == settingArgTypes.LONG or argHasType[-1] == settingArgTypes.LONG_COMPLEX or argHasType[-1] == settingArgTypes.COMPACT:
            isArgTrigUsed = settings.isUsed(argsEnv[counter], argHasType[counter])
            print(argsEnv[counter], "[isUsed]", isArgTrigUsed)

            if isArgTrigUsed == 0:
                # TODO: Add custom error
                raise Exception # Unused/ Unknown cli input setting found
        counter += 1

        if argHasType[-1] == settingArgTypes.INVAL:
            # TODO: Add custom error
            raise Exception # Invalid cli input setting format detected
    print(argHasType)

    # Set settings to return (TODO)

    return settings


def main():
    # Set variables that are global (mostly for writing not neded for reading)
    global timeStart

    # Get user input
    try:
        inputArray = getInputJSON()
        inputKey = inputArray[0]
        inputData = json.loads(inputArray[1])
        inputValue = inputData.get(inputKey)
    except KeyboardInterrupt:
        print("")
        exit(0)


    # Imput conformation
    conf = getConformation(f'\nThe key "{inputKey}" will be set to '+str(inputValue).replace("'",'"')+'. This will result in:\n'+str(inputData).replace("'",'"')+'\n\nAre you sure this is what you want?')

    if conf == False:
        print('Exiting...')
        exit(0)
    print("\n")

    # Start timer
    timeStart = time.time()


    # Get zips in current and lower dirs
    allZips = searchDirFor('./', '', '.zip')
    lenAllZips = len(allZips)
    displayArray(allZips, f'Found {lenAllZips} zip'+ ('s' if lenAllZips != 1 else ''))


    # Gets temporary directory
    tempDir = './temp'
    while os.path.isdir(tempDir) == 1:
        print(f'{timeStamp(timeStart)} Diractory "{tempDir}/" already exists, looking for new temp directory')
        tempDir += str(random.randint(0,9))


    # Processes all the zip files if found
    failed = [['Operation', 'File', 'Error type', 'Error value']]

    if lenAllZips > 0:
        print(f'{timeStamp(timeStart)} Using temporary directory: "{tempDir}/"')

        for i in range(lenAllZips):
            # Get temporary current directory
            tempCurrentDir = os.path.join(tempDir, getFileName(allZips[i]))

            # Extract currently processing zip file
            print(f'\n{timeStamp(timeStart)} Extracting zip {i+1}: "{allZips[i]}" -> "{tempCurrentDir}/"', end=printEnd())
            with zipFile(allZips[i], 'r') as zip:
                try:
                    zip.extractall(tempCurrentDir)
                except Exception as e:
                    failed.append(["extracting", allZips[i], type(e).__name__, str(e)])
                finally:
                    zip.close()
            print('done!')

            # Get JSON files of extracted zip
            allJsons = searchDirFor(tempCurrentDir, '', '.json')
            lenAllJsons = len(allJsons)
            displayArray(allJsons, f'Found {lenAllJsons} json'+ ('s' if lenAllJsons != 1 else ''))

            if lenAllJsons > 0:
                # Look threw all JSONs and replace specefied thing
                didJsonsChange = 0
                for j in range(lenAllJsons):
                    try:
                        hasJsonChanged = jsonChangeValue(allJsons[j], inputKey, inputValue)
                        if hasJsonChanged == 1:
                            didJsonsChange = 1
                    except Exception as e:
                        print("failed!")
                        failed.append(["changing json", allJsons[j], type(e).__name__, str(e)])

                # Rezip extracted zip if something changed
                if didJsonsChange == 1:
                    print(f'{timeStamp(timeStart)} Writing: "{tempCurrentDir}/*" -> "{allZips[i]}"', end=printEnd())
                    with zipFile(allZips[i], 'w') as zip:
                        try:
                            for j in os.listdir(tempCurrentDir):
                                zip.write(os.path.join(tempCurrentDir, j), arcname=j)
                        except Exception as e:
                            failed.append(["zipping", os.path.join(tempCurrentDir, j), type(e).__name__, str(e)])
                        finally:
                            zip.close()
                    print('done!')

            # Remove temp dir for zip
            print(f'{timeStamp(timeStart)} Removing: "{tempCurrentDir}"', end=printEnd())
            shutil.rmtree(tempCurrentDir)
            print('done!')


        # Remove temp dir fully
        print(f'\n{timeStamp(timeStart)} Removing the temp directory: "{tempDir}"', end=printEnd())
        try:
            os.rmdir(tempDir)
            print('done!')
        except OSError as e:
            if e.errno == 41:
                # Direcory not empty. Removing it with remaining tree
                shutil.rmtree(tempDir)
            else:
                print('failed!')
                failed.append(["removing", tempDir, type(e).__name__, str(e)])

    print('\n'*2+'-='*5, 'SCRIPT FINISHED', '=-'*5+'\n')
    lenFailed = len(failed)

    if lenFailed > 1:
        temp = 'S' if lenFailed == 1 else ''
        print(f'WITH ERROR{temp}'+'=-'*4)
        for i in range(lenFailed-1):
            print(f'\tGot {failed[i+1][2]} error "{failed[i+1][3]}" while {failed[i+1][0]} file "{failed[i+1][1]}"\n')

    print(f'\nExecution of script took: {round(time.time()-timeStart, 6)} seconds\n')


# Run main() if file wasn't imported
if __name__ == '__main__':
    print("Variables ({}): {}".format(len(sys.argv), str(sys.argv)))

    argsUsed = [
        # Entry as: [trigger, description, is complex bool (0 if unset), list of allowed entries (only with complex bool. 0 if unset)]
        ["-check-only", "Only validate json files and make no changes", 1],
        ["v", "Verbose/ tell what is going on"],
    ]
    setting = getSettings(sys.argv, argsUsed)

    exit(0)
    timeStart = None # Will be set in main() but is a global definition for other functions
    main(setting)
