# -*- coding: utf-8 -*-
import time
import datetime
import os
import urllib
import json
import sys

def readResFile(resName):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dirname = os.path.join(current_dir, 'resources')

    path = os.path.join(dirname, resName)
    try:
        out_file = open(path, "r")
        text = out_file.read()
        out_file.close()
    except:
        print("Ops! Something went wrong with file reading (" + resName + ")")
        raise
    return eval(text)


def read_mappingrules(mapdict):
    map_file = open('mapping_rules.py', "r")
    cont = map_file.read()
    map_file.close()


def getDate():
    """
    Simply returns current date in format YYYY_MM_DD, used for naming dataset
    """
    timestmp = time.time()
    date = datetime.datetime.fromtimestamp(timestmp).strftime('%Y_%m_%d')
    return date

def createResFile (file_content, lang, resName) :
    """
    Creates a new file named 'resource-name - date'.txt containing extracted info
    :param file_content: parsed data
    :param resName: name_of_resource
    """
    title = resName + " [" + lang.upper() + "] - " + getDate() + ".txt"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    dirname = os.path.join(current_dir, 'resources')

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    path = os.path.join(dirname, title)
    str_content = makeReadable(file_content)
    try:
        out_file = open(path, "w")
        out_file.write(str(str_content))
        out_file.close()
    except:
        print("Ops! Something went wrong with file creation")
        raise


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

    encoded = finalString.encode('utf-8')
    return encoded


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


def sparql_query(query, lang):
    '''
    Returns a json representation of data from a query to a given SPARQL endpoint
    :param query: string containing the query
    :param lang: local endpoint to query (e.g. 'en', 'it'..)
    :return: json result from the endpoint
    '''
    if lang == 'en':
        local = ""
    else:
        local = lang + "."
    enc_query = urllib.quote_plus(query)
    endpoint_url = "http://" + local + "dbpedia.org/sparql?default-graph-uri=&query=" + enc_query + \
                   "&format=application%2Fsparql-results%2Bjson&debug=on"
    json_result = json_req(endpoint_url)
    return json_result


def get_resources(lang, page_type="Writer"):
    '''
    constructs a list containing all resources from specified type (default: writers)
    :param lang: endpoint language
    :param page_type: should be a string as <http://dbpedia.org/ontology/Writer>
    :return: resource list
    '''
    tot_res = int(count_query(lang, page_type))
    offset = 0
    fin_list = []

    while (offset < tot_res):
        base_query = "SELECT distinct ?s as ?res WHERE{ ?s a <http://dbpedia.org/ontology/" + page_type + "> .?s <http://dbpedia.org/ontology/wikiPageID> ?f} LIMIT 1000 OFFSET "
        query = base_query + str(offset)
        json_res = sparql_query(query, lang)
        res_list = json_res['results']['bindings']
        for json_res in res_list:
            resource = json_res['res']['value']
            resource_name = resource.split("/")[-1]
            fin_res = resource_name.encode('utf-8')
            fin_list.append(fin_res)
        offset += 1000

    if fin_list == []:  # No resource found
        raise
    return fin_list


def count_query(lang, page_type="Writer"):
    '''
    Gets the number of resources of the given type which have also a Wikipedia related page found on a specified enpoint
    :param lang: endpoint
    :param page_type: for example "<http://dbpedia.org/ontology/Writer>"
    :return: endpoint answer as a number
    '''
    where_clause = "?s a <http://dbpedia.org/ontology/" + page_type + "> .?s <http://dbpedia.org/ontology/wikiPageID> ?f"
    query = "select (count(distinct ?s) as ?res_num) where{" + where_clause + "}"
    json_res = sparql_query(query, lang)
    try:
        res_num = json_res['results']['bindings'][0]['res_num']['value']
        return res_num
    except:
        print("Could not retrieve number of resources")
        raise


def json_req(req):
    """
    Performs a request to an online service and returns the answer in JSON
    :param req: URL representing the request
    :return: a json representation of data obtained from a call to an online service
    """
    try:
        call = urllib.urlopen(req)
        answer = call.read()
        json_ans = json.loads(answer)
        return json_ans
    except:
        err = str(sys.exc_info()[0])
        print("Error: " + err + " - on request " + req)
        raise
