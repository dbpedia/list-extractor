import time
import datetime

def createResFile (file_content, lang, resName) :
    """
    Creates a new file named 'resource-name - date'.txt containing extracted info
    :param file_content: parsed data
    :param resName: name_of_resource
    """
    timestmp = time.time()
    date = datetime.datetime.fromtimestamp(timestmp).strftime('%Y_%m_%d')
    title = resName + " [" + lang.upper() + "] - " + date + ".txt"

    str_content = makeReadable(file_content)
    try:
        out_file = open(title,"w")
        out_file.write(str(str_content))
        out_file.close()
    except:
        print("Ops! Something went wrong with file creation")


def makeReadable (res_dict) :
    """
    converts the dictionary in a string, sorts by key, and makes it more readable to be stored in a file
    :param resddict: dictionary obtained fro resource
    :return: readable string
    """
    finalString = ""
    keys_list = list(res_dict)
    for key in sorted(keys_list) :
        finalString += key + " : " + str(res_dict[key]) + "\n"
    return finalString


def clean_dictionary(listDict) :
    """
    Deletes all entries with an empty values and cleanses the dictionary
    :param listDict: dictionary obtained from parsing
    :return: a dictionary without empty values
    """
    for key in listDict.keys() :
        if listDict[key] == '' :
            listDict.pop(key)
    return listDict