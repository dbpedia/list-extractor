import urllib2
import json
import re
import rdflib
import utilities

dbo = rdflib.Namespace("http://dbpedia.org/ontology/")
dbr = rdflib.Namespace("http://dbpedia.org/resource/")


def select_mapping(resDict, res, lang, graph):
    if lang == 'en':
        select_mapping_en(resDict, res, graph)
    elif lang == 'it':
        select_mapping_it(resDict, res, graph)
    else:
        print('Sorry! Language ' + lang + ' is not available yet for list extraction')


def select_mapping_en(resDict, res, g):
    res = rdflib.URIRef(dbr + res)
    for key in resDict.keys():
        if re.search('bibliography', key, re.IGNORECASE):
            map_bibliography(resDict[key], res, 'en', g)


def select_mapping_it(resDict, res, g):
    res = rdflib.URIRef(dbr + res.decode("utf-8"))
    for key in resDict.keys():
        if re.search('opere', key, re.IGNORECASE):  # or re.search('bibliografia',key, re.IGNORECASE) :
            map_bibliography(resDict[key], res, 'it', g)
            for s, p, o in g:
                print(" New Triple: "),
                print(s, p, o)


def map_bibliography(elem_list, res, lang, g):
    '''
    Handles lists referring to bibliography
    :param elem_list: list of elements to be mapped
    :param res: current resource
    :param lang: resource language
    :return:
    '''
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            map_bibliography(elem, res, lang, g)
        else:
            ref = reference_mapper(elem)
            if ref != None:  # elem contains a reference res
                uri = wikidataAPI_call(ref, lang)
                if (uri != None):
                    dbpedia_uri = find_DBpedia_uri(uri, lang)
                    if dbpedia_uri != None:
                        uri = dbpedia_uri
                    g.add((rdflib.URIRef(uri), dbo.author, res))
            else:  # no reference found
                uri_name = general_mapper(elem)
                if (uri_name != None):
                    uri_name = uri_name.replace(' ', '_')
                    uri = dbr + uri_name
                    g.add((rdflib.URIRef(uri), dbo.author, res))
            year = year_mapper(elem)
            if year != None and uri != None:
                g.add((rdflib.URIRef(uri), dbo.releaseYear, rdflib.Literal(year, datatype=rdflib.XSD.gYear)))


def reference_mapper(list_elem):
    '''
    Looks for a reference inside the element, which has been marked by {{ }}
    :param list_elem: current list element
    :return: a match if found
    '''
    match_ref = re.search(r'\{\{(.*?)\}\}', list_elem)
    if match_ref != None:
        match_ref = match_ref.group(1)
        print("reference match " + list_elem + " -> "),
        print(match_ref)
    return match_ref


def general_mapper(list_elem):
    '''
    Called when no reference is found, applies a regex to find the main concept and cuts off punctuation marks
    :param list_elem: current list element
    :return: a match if found
    '''
    match_str = re.search(r'([^0-9][^,.*|:.*])+', list_elem, re.IGNORECASE)
    if match_str != None:
        match_str = match_str.group()
        match_str = match_str.replace("\'\'", "")
        match_str = match_str.replace("\"", "")
        match_str = match_str.replace(";", "")
        match_str = match_str.replace(".", "")
    print("general mapper: "),
    print(match_str)
    return match_str


def year_mapper(list_elem):
    '''
    Looks for a set of 4 digits which would likely represent the year of publication
    :param list_elem: current list element
    :return: a numeric match if found
    '''
    match_num = re.search(r'[0-9]{4}', list_elem)
    if match_num != None:
        match_num = match_num.group()
    print("year: "),
    print(match_num)
    return match_num


def lookup_call(keyword):
    '''
    Calls dbpedia lookup service to retrieve a corresponding URI from a keyword
    :param keyword: keys in the resource dictionary
    :return: service answer in JSON format
    '''
    base_req = 'http://lookup.dbpedia.org/api/search/PrefixSearch?MaxHits=1&QueryString='
    req = base_req + str(keyword)
    try:
        call = urllib2.Request(req)
        call.add_header('Accept', 'application/json')
        resp = urllib2.urlopen(call)
        answer = resp.read()
        parsed_ans = json.loads(answer)
    except:
        print ("Dbpedia Lookup error")
        raise
    return parsed_ans


def wikidataAPI_call(res, lang):
    '''
    Calls Wikidata API service to retrieve a corresponding URI from a string
    :param res: string related to the URI we want to find
    :param lang: language or endpoint in which we perform the search
    :return: answer in json format
    '''
    utf8_res = res.encode('utf8')  # first encode the string in utf8 format to keep safe from special characters
    enc_res = urllib2.quote(utf8_res)  # then encode the string to be used in a URL

    req = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&search=' + enc_res + '&language=' + lang
    try:
        call = urllib2.Request(req)
        resp = urllib2.urlopen(call)
        answer = resp.read()
        parsed_ans = json.loads(answer)
        result = parsed_ans['search']
    except:
        print ("Wikidata API error")
        raise
    if result == []:
        return None
    else:
        uri = result[0]['concepturi']
        print(uri)
        return uri


# Not using this for now since it works only for english and Wikidata API has shown to provide better results
def find_DBpedia_uri(wk_uri, lang):
    '''
    Used to find equivalent URI in DBpedia from a Wikidata one
    :param wk_uri: URI found using the WikiData API
    :param lang: resource/endpoint language
    :return:
    '''
    query = "select distinct ?s where {?s <http://www.w3.org/2002/07/owl#sameAs> <" + wk_uri + "> }"
    json = utilities.sparql_query(query, lang)
    try:
        result = json['results']['bindings'][0]['s']['value']
    except:
        result = None
    print (">>>> Dbpedia res: "),
    print(result)
    return result
