#!/usr/bin/python3
from zipfile import ZipFile as zipFile
import os, random, json, time, shutil, sys
from enum import IntEnum, auto # Needs python 3.4+

'''TODO:
    - Add option for verbose instead of spamming a log (-v)
    - Add option for only checking the JSON files (--check-only)
    - Add support for putting replacement key and variable in as a command-line variable
'''

# Setup necessary classes
class SettingArgTypes(IntEnum):
        '''Argument types used for remembering what input arguments is what.
        '''
        INVAL = 0 # Giberish
        CALLED_FILE_PATH = auto() # First argument (executed file)
        COMPACT = auto() # -v or -vbr
        LONG = auto() # --help
        LONG_COMPLEX = auto() # --set_mode x
        LONG_COMPLEX_CHILD = auto() # the x from the LONG_COMPLEX comment


class ArgumentSettings(object):
    '''
        Class for helping with CLI argument support setup
        and info showing
    '''

    class VarOrder(IntEnum):
        # VarOrder used for remembering order of data in varAvailable to allow easy change
        trigger = 0
        settingName = auto()
        desc = auto()
        isComplex = auto()
        allowedEntry = auto()

    LOCATION_HELP = 1 # Location of help entry in varAvailable
    # Entry as: [trigger, settingName, description, is complex bool (0 if unset), list of allowed entries (TODO) (only with complex bool. 0 if unset)]
    varAvailable = [
        ["CALLED_FILE_PATH", "calledFilePath", 1, []], # Special case for standard given argument
        ["-help", "help", "Shows this help list", 0, []],
    ]

    activeSettings = {}

    def __init__(self, toAddVarSettings, programName:str):
        '''Initiates ArgumentSettings class
        '''
        # Add wanted variables to varAvailable list
        for indexSet in toAddVarSettings:
            self.varAvailable.append(indexSet)
        
        self.NAME = programName

    def isUsed(self, trigger:str, argTrigType:SettingArgTypes = None) -> bool:
        '''Checks if trigger value is set in varAvailable, then returns bool
        '''

        # Remove '-' from begin if there
        if trigger[0] == '-': trigger = trigger[1:]

        # Filtering and processing for COMPACT type
        if argTrigType == SettingArgTypes.COMPACT:
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

    def getInfo(self, trigger:str, infoType:VarOrder) -> str or int:
        '''
            This function searches for trigger and gets his value to return
            at the infoType place
        '''
        for i in self.varAvailable:
            if i[self.VarOrder.trigger] == trigger:
                # Found trigger, now return value if able too
                try:
                    return i[infoType]
                except IndexError:
                    return None
        return None

    def setVal(self, settingName: VarOrder.settingName, value = None) -> None:
        '''Function sets the settingName in activeSettings to Value for later use
        '''
        # TODO: Add complex variable "allowed input check" (Only a thing 
        #   when value != None)
        self.activeSettings[settingName] = 1 if value == None else value

    def getVal(self, settingName: VarOrder.settingName):
        '''This function retrieves a value of a var from activeSettings and returns it
        '''
        return self.activeSettings[settingName]
    
    def showHelp(self) -> None:
        '''This function generates and shows the help info menu
        '''
        # TODO: May be great to sort the output alphabaticly and in type (long/ short)

        # Show help list info
        print("\nHelp information menu of {}\n".format(self.NAME))

        # Go threw used variables and show them in niceish format
        # Ignore the first entry (CALLED_FILE_PATH)
        for var in self.varAvailable[1:]:
            infoString = "\t" # Base string

            if (var[self.VarOrder.trigger][0] == "-"):
                # Add formating for long triggers
                infoString += "\b-" + var[self.VarOrder.trigger]
                infoString += "" if (len(var[self.VarOrder.trigger]) > 8) else "\t"
            else:
                # Add formating for short triggers
                infoString += "-{}\t".format(var[self.VarOrder.trigger])
            
            # Print formatted string
            print("{}\t{}".format(infoString, var[self.VarOrder.desc]))

            # Print extra info about LONG's child posibilities (TODO)
            # TODO: add print("\t └ Supports arguments")
            # TODO: print("\t └ Supports following arguments;")
        
        print("\n") # New lines just to make it nice


def searchDirFor(directory, startsW, endsW) -> list:
    ''' 
        Searches recursively in the specified directory for files that start with 
        "startW" and end with "endsW".
        Returns list of specefied files
    '''
    foundTarget = []

    for file in os.listdir(directory):
        if (file.endswith(endsW) and file.startswith(startsW)):
            foundTarget.append(os.path.join(directory, file))

        elif (os.path.isdir(os.path.join(directory, file))):
            foundTarget += searchDirFor(os.path.join(directory, file), startsW, endsW)
    return foundTarget


def displayArray(array, description) -> None:
    ''' Does as the name says with formatting
    '''
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
    ''' Gets the name of the specified file without extension and dictionary
    '''
    splitUpDirectory = directory.split('/')
    fileName = splitUpDirectory[len(splitUpDirectory)-1].rsplit('.', 1)[0]
    return fileName


def jsonChangeValue(file, key, value) -> int:
    '''
        Reads specified json file, changes it and saves that change
        Returns hasDataChanged bool (1 if changed 0 if has not)
    '''
    print(f'{timeStamp(timeStart)} Changing "{key}" to '+str(value).replace("'",'"')+f' in "{file}"', end=END_DOTS)

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


def timeStamp(timeStart) -> str:
    '''
        This function calculates the time from the start of execution and returns a
        string with this data formated into bracets.
    '''
    return "[{}s]".format(round(time.time() - timeStart, 3))


def isValidJSON(data) -> bool:
    ''' This funciton checks if data is valid json. Returns true if true otherwise false
    '''
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


def getConformation(q) -> bool:
    '''
        Asks for user conformation via CLI.
        If no conformation is given it will re-ask it recursively
    '''
    a = input(str(q)+" (y or n) ")
    if "y" == a.lower() or "yes" == a.lower():
        return True
    elif "n" == a.lower() or "no" == a.lower():
        return False
    else:
        print("That doesn't look like a conformation. Please put one in")
        return getConformation(q)


def hasSubStr(targetStr:str, thisStr:str, mode:int=0) -> bool:
    '''
        Looks for str inside of str and returns 1 if found, 0 if not
        Modes:
        0 - (default) searches whole str
        1 - Only search front with length of targetStr
        2 - Only search back with length of targetStr
    '''

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
    '''
        Function checks if thisStr ONLY has allowedChars in it.
        Returns true if it does, false if not
    '''
    for char in thisStr:
        if char not in allowedChars:
            return 0
    return 1


def getSettingArgType(arg:str, prevArgType:int) -> SettingArgTypes:
    '''Function looks at Argument to determin the type, then returns the type
    '''
    allowedCharsCompact = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVXYZ"

    if hasSubStr('-', arg, 1) != 1:
        # Is invalid but may be LONG_COMPLEX_CHILD
        if prevArgType == SettingArgTypes.LONG:
            return SettingArgTypes.LONG_COMPLEX_CHILD
        return SettingArgTypes.INVAL

    # Is argument, check if longer
    if hasSubStr('--', arg, 1) != 1:
        # Is probably of type compact, testing for invalid characters
        if hasAllowedChars(arg[1:], allowedCharsCompact) == 1:
            return SettingArgTypes.COMPACT # Is a valid compact type

        return SettingArgTypes.INVAL # Invalid

    # Is longer
    return SettingArgTypes.LONG


def getArgSettings(argsEnv:list, programName:str, argsSettingsUsed:list == None) -> ArgumentSettings:
    '''
        This function gets the enviroment arguments and processes them to a more friendly form.
        It should return the settings themself
    '''
    '''
        -=-= Little note =-=-
        Yes, I know that this whole function with the argument parsing I do here
        can be done with getopt.getopt() or argparse, and so is unconventional. The
        reason why I, an inexperienced programmer and first-year college student, took
        the time to write this code is mostly as a challenge.
        Secondly, I hope to learn to write code that parses arguments like
        these, so that I can use this in future projects even if they are in another,
        more complex, programming language. This way I may be able to save time in the
        future by basing argument parsing on what I did here.

        TLDR; Basically wrote this function to learn how I could do this in the future
        using other programming languages. Even though I could have used an already
        build sys function

        - Electrenator 
    '''

    settings = ArgumentSettings(argsSettingsUsed, programName)

    # Look for argument types
    argHasType = [SettingArgTypes.CALLED_FILE_PATH]
    counter = 1
    for arg in argsEnv[1:]:
        argHasType.append(getSettingArgType(arg, argHasType[-1]))

        # Check for LONG_COMPLEX_CHIELD, if found set previous as LONG_COMPLEX
        if argHasType[-1] == SettingArgTypes.LONG_COMPLEX_CHILD:
            # Check if argsEnv[counter - 1] can get LONG_COMPLEX
            if settings.getInfo(argsEnv[counter - 1][1:], settings.VarOrder.isComplex) != 1:
                argHasType[-1] = SettingArgTypes.INVAL
            else: 
                argHasType[-2] = SettingArgTypes.LONG_COMPLEX

        # Check if trigger is used
        if (argHasType[-1] == SettingArgTypes.LONG or 
          argHasType[-1] == SettingArgTypes.LONG_COMPLEX or 
          argHasType[-1] == SettingArgTypes.COMPACT):
            isArgTrigUsed = settings.isUsed(argsEnv[counter], argHasType[counter])

            if isArgTrigUsed == 0:
                # TODO: Add custom error
                raise Exception # Unused/ Unknown cli input setting found
        counter += 1

        if argHasType[-1] == SettingArgTypes.INVAL:
            # TODO: Add custom error
            raise Exception # Invalid cli input setting format detected

    # Set settings in settings class to return
    genSettingList(settings, argsEnv, argHasType)

    return settings

def genSettingList(settings:ArgumentSettings, args:list, argTypes:list) -> None:
    for argNumber in range(len(args)):
        thisArgType = argTypes[argNumber]

        if not thisArgType == SettingArgTypes.LONG_COMPLEX:
            if thisArgType == SettingArgTypes.CALLED_FILE_PATH:
                # CALLED_FILE_PATH argument; Special treatment
                thisArgName = settings.getInfo("CALLED_FILE_PATH",
                  settings.VarOrder.settingName) # Get settingName

            elif thisArgType == SettingArgTypes.LONG_COMPLEX_CHILD:
                # Complex argument; get complex(er) treatment
                thisArgName = settings.getInfo(args[argNumber - 1][1:],
                  settings.VarOrder.settingName) # Get settingName of parent arg
                
            else:
                # Simple argument
                thisArgName = settings.getInfo(args[argNumber][1:],
                  settings.VarOrder.settingName) # Get settingName
                

            # Store arg setting data
            if thisArgName != None:
                if (thisArgName ==
                  settings.varAvailable[settings.LOCATION_HELP][settings.VarOrder.settingName]):
                    settings.showHelp()
                    exit(0) # Help message exit

                if thisArgType == SettingArgTypes.LONG_COMPLEX_CHILD:
                    # Set complex value
                    settings.setVal(thisArgName, args[argNumber])
                elif thisArgType == SettingArgTypes.CALLED_FILE_PATH:
                    # Set CALLED_FILE_PATH value
                    settings.setVal(thisArgName, args[argNumber])
                else:
                    # Set other values
                    settings.setVal(thisArgName)
            else:
                raise Exception # All Args should have name at this point


def exctractZip(dirOfZip, targetDir) -> None:
    with zipFile(dirOfZip, 'r') as zip:
        try:
            zip.extractall(targetDir)
        except Exception as e:
            failed.append(["extracting", dirOfZip, type(e).__name__, str(e)])
        finally:
            zip.close()
    print('done!')


def writeZip(dirOfZip, targetDir) -> None:
    with zipFile(dirOfZip, 'w') as zip:
        try:
            for j in os.listdir(targetDir):
                zip.write(os.path.join(
                    targetDir, j), arcname=j)
        except Exception as e:
            failed.append(["zipping", os.path.join(
                targetDir, j), type(e).__name__, str(e)])
        finally:
            zip.close()
    print('done!')


def processZips(tempDir:str, allZips:list, inputKey:str, inputValue) -> None:
    for i in range(len(allZips)):
        # Get temporary current directory
        tempCurrentDir = os.path.join(tempDir, getFileName(allZips[i]))

        # Extract currently processing zip file
        print(f'\n{timeStamp(timeStart)} Extracting zip {i+1}: "{allZips[i]}" -> "{tempCurrentDir}/"', end=END_DOTS)
        exctractZip(allZips[i], tempCurrentDir)

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
                print(f'{timeStamp(timeStart)} Writing: "{tempCurrentDir}/*" -> "{allZips[i]}"', end=END_DOTS)
                writeZip(allZips[i], tempCurrentDir)

        # Remove temp dir for zip
        print(f'{timeStamp(timeStart)} Removing: "{tempCurrentDir}"', end=END_DOTS)
        delDir(tempCurrentDir)
        print('done!')


def delDir(dirPath:str) -> None:
    try:
        os.rmdir(dirPath)
        print('done!')
    except OSError as e:
        if e.errno == 41:
            # Direcory not empty. Removing it with remaining tree
            shutil.rmtree(dirPath)
            print('done!')
        else:
            print('failed!')
            failed.append(["removing", dirPath, type(e).__name__, str(e)])


def genUniqueDirName(dirBaseName:str) -> str:
    dirName = dirBaseName

    while os.path.isdir(dirName) == 1:
        print(f'{timeStamp(timeStart)} Diractory "{dirName}/" already exists, looking for new temp directory')
        dirName += str(random.randint(0,9))

    return dirName


def printFailedEndMessage(errorList):
    totalErrors = len(errorList)

    if totalErrors > 1:
        print('WITH ERROR{}{}'.format('S' if totalErrors == 1 else '', '=-'*4))
        for i in range(totalErrors-1):
            print(f'\tGot {errorList[i+1][2]} error "{errorList[i+1][3]}" while {errorList[i+1][0]} file "{errorList[i+1][1]}"\n')


def main(argVariables:SettingArgTypes):
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

    # Input conformation
    conf = getConformation(f'\nThe key "{inputKey}" will be set to '+str(inputValue).replace("'",'"')+'. This will result in:\n'+str(inputData).replace("'",'"')+'\n\nAre you sure this is what you want?')

    if conf == False:
        print('Exiting...')
        exit(0)
    print("\n")

    # Set variables used for processing
    timeStart = time.time() # Starts timer
    allZips = searchDirFor('./', '', '.zip')
    lenAllZips = len(allZips)
    tempDir = genUniqueDirName('./temp')

    displayArray(allZips, f'Found {lenAllZips} zip'+ ('s' if lenAllZips != 1 else ''))

    # Processes all the zip files if found
    if len(allZips) > 0:
        print(f'{timeStamp(timeStart)} Using temporary directory: "{tempDir}/"')
        processZips(tempDir, allZips, inputKey, inputValue)

        # Remove temp dir fully
        print(f'\n{timeStamp(timeStart)} Removing the temp directory: "{tempDir}"', end=END_DOTS)
        delDir(tempDir)

    print('\n'*2+'-='*5, 'SCRIPT FINISHED', '=-'*5+'\n')
    printFailedEndMessage(failed)
    print(f'\nExecution of script took: {round(time.time()-timeStart, 6)} seconds\n')


# Run main() if file wasn't imported
if __name__ == '__main__':
    print("Variables ({}): {}".format(len(sys.argv), str(sys.argv)))

    argSettings = getArgSettings(sys.argv, "JSONsInZIPsEditor", [
        # Entry as: [trigger, settingName, description, is complex bool (0 if unset), list of allowed entries (only with complex bool. 0 if unset)]
        ["-check-only", "check-only", "Only validate json files and make no changes", 1],
        ["v", "verbose", "Verbose/ tell what is going on"],
    ])

    print(argSettings.activeSettings)

    exit(0)
    timeStart = None # Will be set in main() but is a global definition for other functions
    END_DOTS = "...    "
    failed = [['Operation', 'File', 'Error type', 'Error value']]

    main(argSettings)
