#!/usr/bin/python3
from zipfile import ZipFile as zipFile
import os, random, json, time, shutil


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
    for i in range(len(array)):
        if len(temp) == 0:
            temp += '"'+array[i]+'"'
        elif i+1 == len(array):
            temp += ' and "'+array[i]+'"'
        else:
            temp += ', "'+array[i]+'"'
    print(timeStamp(timeStart),description+':', temp)


def getFileName(directory):
    ''' Gets the name of the specified file without extension and dictionary '''
    splitUpDirectory = directory.split('/')
    fileName = splitUpDirectory[len(splitUpDirectory)-1].rsplit('.', 1)[0]
    return fileName


def jsonChangeValue(file, key, value):
    ''' Reads specified json file, changes it and saves that change '''
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
    data = searchAndReplace(data, key, value)

    # Rewrite data
    # (truncates/removes existing data in file)
    if useEncoding != None:
        with open(file, 'w', encoding=useEncoding) as f:
            try:
                json.dump(data, f, indent=4)
            finally:
                f.close()
    else:
        with open(file, 'w') as f:
            try:
                json.dump(data, f, indent=4)
            finally:
                f.close()

    print('done!')


def searchAndReplace(var, searchKey, newValue):
    ''' Searches and replaces values in a dictionary and lists with the specified key '''
    if type(var) == dict:
        for key in var.keys():
            if key == searchKey:
                var[key] = newValue
            elif type(var[key]) == dict or type(var[key]) == list:
                var[key] = searchAndReplace(var[key], searchKey, newValue)
        return var
    elif type(var) == list:
        for item in var:
            i = var.index(item)
            if type(var[i]) == dict or type(var[i]) == list:
                var[i] = searchAndReplace(var[i], searchKey, newValue)
        return var
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
    inputKey = input('Input JSON key: ').replace("'",'"')
    inputValue = input('Input new JSON value: ').replace("'",'"')
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
    displayArray(allZips, f'Found {len(allZips)} zips')


    # Gets temporary directory
    tempDir = './temp'
    while os.path.isdir(tempDir) == 1:
        print(f'{timeStamp(timeStart)} Diractory "{tempDir}/" already exists, looking for new temp directory')
        tempDir += str(random.randint(0,9))

    print(f'{timeStamp(timeStart)} Using temporary directory: "{tempDir}/"')


    # Processes all the zip files
    failed = [['Operation', 'File', 'Error type', 'Error value']]
    for i in range(len(allZips)):
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
        displayArray(allJsons, f'Found {len(allJsons)} jsons')

        # Look threw all JSONs and replace specefied thing
        for j in range(len(allJsons)):
            try:
                jsonChangeValue(allJsons[j], inputKey, inputValue)
            except Exception as e:
                print("failed!")
                failed.append(["changing json", allJsons[j], type(e).__name__, str(e)])

        # Rezip extracted zip
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

    if len(failed) > 1:
        temp = 'S' if len(failed)==1 else ''
        print(f'WITH ERROR{temp}'+'=-'*4)
        for i in range(len(failed)-1):
            print(f'\tGot {failed[i+1][2]} error "{failed[i+1][3]}" while {failed[i+1][0]} file "{failed[i+1][1]}"\n')

    print(f'\nExecution of script took: {round(time.time()-timeStart, 6)} seconds\n')


# Run main() if file wasn't imported
if __name__ == '__main__':
    timeStart = None # Will be set in main() but is a global definition for other functions
    main()
