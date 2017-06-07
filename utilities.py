# -*- coding: utf-8 -*-

'''
####################
### utilities.py ###
####################

* This module contains all the utility methods/functions that are commonly used by all mapping functions.

'''

import time
import datetime
import os
import urllib
import csv
import json
import sys
from mapping_rules import EXCLUDED_SECTIONS


def readResFile(resName):
    ''' Reads the file called resName in resources directory and returns it as a dictionary

    :param resName: file name to be read
    :return: the dictionary contained in resources/resName
    '''
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dirname = os.path.join(current_dir, 'resources')
    path = os.path.join(dirname, resName)
    try:
        out_file = open(path, "r")
        text = out_file.read()
        out_file.close()
    
    except:
        print("Oops! Something went wrong with file reading (" + resName + ")")
        raise
    
    return eval(text)

def getDate():
    """ Returns current date in format YYYY_MM_DD, used for naming dataset."""
    timestmp = time.time()
    date = datetime.datetime.fromtimestamp(timestmp).strftime('%Y_%m_%d')
    return date

def createResFile(file_content, lang, resName):
    '''Creates a new file named 'resName - date'.txt containing extracted info

    :param file_content: parsed data to be stored
    :param resName: name_of_resource
    '''
    title = resName + " [" + lang.upper() + "] - " + getDate() + ".txt"
    path = get_subdirectory('resources', title)
    str_content = makeReadable(file_content)
    
    try:
        out_file = open(path, "w")
        out_file.write(str(str_content))
        out_file.close()
    
    except IOError:
        print("Ops! Something went wrong with file creation")
        raise


def get_subdirectory(dirname, filename):
    '''Get the absolute path of new file called 'filename' inside subdirectory 'dirname', abstracting from OS

    :param dirname: subdirectory name
    :param filename: new file name
    :return: final path
    '''
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dirpath = os.path.join(current_dir, dirname)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    file_path = os.path.join(dirname, filename)
    
    return file_path

def makeReadable (res_dict) :
    ''' Used to make more decipherable the dictionaries stored in 'resources' directory

    Converts the dictionary in a string, sorts by key, and makes it more readable to be stored in a file
    :param res_dict: dictionary obtained fro resource
    :return: readable string
    '''
    finalString = ""
    keys_list = list(res_dict)
    for key in sorted(keys_list) :
        finalString += key + " : " + str(res_dict[key]) + "\n"
    encoded = finalString.encode('utf-8')
    
    return encoded


def clean_dictionary(listDict) :
    ''' Deletes all entries with an empty values, thus 'cleaning' the dictionary

    :param listDict: dictionary obtained from parsing
    :return: a dictionary without empty values
    '''
    for key in listDict.keys() :
        if listDict[key] == '' :
            listDict.pop(key)
        if key in EXCLUDED_SECTIONS:
            listDict.pop(key)
        else:
            listDict[key] = remove_symbols(listDict[key])

    return listDict


def remove_symbols(listDict_key):
    ''' removes other sybols are garbage characters that pollute the values to be inserted 

    :param listDict_key: dictionary entries(values) obtained from parsing
    :return: a dictionary without empty values
    '''
    for i in range(len(listDict_key)):
        value = listDict_key[i]
        if type(value)==list:
            value=remove_symbols(value)
        else:
            listDict_key[i] = value.replace('&nbsp;','')

    return listDict_key


def sparql_query(query, lang):
    ''' Returns a json representation of data from a query to a given SPARQL endpoint

    :param query: string containing the query
    :param lang: prefix representing the local endpoint to query (e.g. 'en', 'it'..)
    :return: json result obtained from the endpoint
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


def get_resources(lang, page_type):
    ''' Constructs a list containing all resources from specified type/class

    Firstly computes the number of resources from given type, then performs (tot_res modulo 1000) calls
    to the endpoint and construct the final list containing all of them.
    :param lang: prefix representing the local endpoint to query (e.g. 'en', 'it'..)
    :param page_type: a string containing the ontology class to query
    :return: resource list
    '''
    tot_res = int(count_query(lang, page_type))
    offset = 0
    fin_list = []
    while (offset < tot_res):
        base_query = "SELECT distinct ?s as ?res WHERE{ ?s a <http://dbpedia.org/ontology/" + page_type \
                        + "> .?s <http://dbpedia.org/ontology/wikiPageID> ?f} LIMIT 1000 OFFSET "
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
        print("Could not retrieve any resource")
        raise
    
    return fin_list


def count_query(lang, page_type):
    '''Gets the number of resources of the given type using a count query on the specified endpoint

    :param lang: endpoint
    :param page_type: for example "<http://dbpedia.org/ontology/Writer>"
    :return: endpoint answer as a number
    '''
    where_clause = "?s a <http://dbpedia.org/ontology/" + page_type + \
                    "> .?s <http://dbpedia.org/ontology/wikiPageID> ?f"
    query = "select (count(distinct ?s) as ?res_num) where{" + where_clause + "}"
    json_res = sparql_query(query, lang)
    try:
        res_num = json_res['results']['bindings'][0]['res_num']['value']
        return res_num
    except:
        print("Could not retrieve any resource")
        raise


def json_req(req):
    ''' Performs a request to an online service and returns the answer in JSON

    :param req: URL representing the request
    :return: a JSON representation of data obtained from a call to an online service
    '''
    try:
        call = urllib.urlopen(req)
        answer = call.read()
        json_ans = json.loads(answer)
        return json_ans
    except:
        err = str(sys.exc_info()[0])
        print("Error: " + err + " - on request " + req)
        raise


def get_resource_type(lang, resource):
    ''' Asks all rdf:type of current resource to the local SPARQL endpoint

    :param resource: current resource with unknown type
    :param lang: language/endpoint
    :return: a list containing all types associated to the resource in the local endpoint
    '''
    if lang == 'en':
        local = ""
    else:
        local = lang + "."
    type_query = "SELECT distinct ?t WHERE {<http://" + local + "dbpedia.org/resource/" + resource + "> a ?t}"
    answer = sparql_query(type_query, lang)
    results = answer['results']['bindings']
    types = []
    for res in results:
        full_uri = res['t']['value']  # e.g. http://dbpedia.org/ontology/Person
        class_type = full_uri.split("/")[-1]  # e.g Person
        types.append(class_type)
    return types


def count_listelem_dict(res_dict):
    ''' Counts the total number of list elements from the dictionary representing the Wikipedia page.

    It's used to know how many list elements in a page are actually extracted.
    :param res_dict: dictionary representing the resource (Wikipedia page)
    :return: total list elements
    '''
    list_el_num = 0
    for k in res_dict.keys():
        for el in res_dict[k]:
            list_el_num += 1
    return list_el_num

def evaluate(lang, source, tot_extracted_elems, tot_elems):
    ''' Evaluates the extaction process and stores it in a csv file.

    :param source: resource type(dbpedia ontology type)
    :param tot_extracted_elems: number of list elements extracted in the resources.
    :param tot_elems: total number of list elements present in the resources.
    '''
    print "\nEvaluation:\n===========\n"
    print "Resource Type:", lang + ":" + source
    print "Total list elements found:", tot_elems
    print "Total elements extracted:", tot_extracted_elems
    accuracy = (1.0*tot_extracted_elems)/tot_elems
    print "Accuracy:", accuracy

    with open('evaluation.csv', 'a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow([lang, source, tot_extracted_elems, tot_elems, accuracy])
