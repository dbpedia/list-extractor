# coding: utf-8
import urllib2
import json
import re
import rdflib
import utilities
import time
from mapping_rules import *

'''
#Used to select a mapping function for the given resource class,
# Values must correspond to mapping methods in the form of 'map_bibliography()'
MAPPING = {'Writer' : 'BIBLIOGRAPHY'}

#Contains the substrings to be searched in section names in order to relate the inner list to the topic
#Title describes the topic and is a value from MAPPING
#Keys correspond to language prefix, Values to section titles
BIBLIOGRAPHY = {
    'en': ['bibliography', 'works', 'fiction'],
    'it': ['opere', 'romanzi', 'saggi']
}

#Used to reconcile section names with literary genres of inner list elements (for bibliography-kind lists)
BIBLIO_GENRE = {
    'en' : {'Novels' : 'Novel', 'Short stories' : 'Short_story', 'Short Fiction' : 'Short_story',
            'Comics' : 'Comic', 'Articles': 'Article', 'Essays':'Essay', 'Plays' : 'Play_(theatre)'},
    'it' : {'Romanzi' : 'Romanzo', 'Racconti' : 'Racconto', 'Antologie': 'Antologia',
            'Audiolibri' : 'Audiolibro', 'Saggistica' : 'Saggio', 'Poesie' : 'Poesia',
            'Drammi': 'Dramma'}
}
'''

dbo = rdflib.Namespace("http://dbpedia.org/ontology/")
dbr = rdflib.Namespace("http://dbpedia.org/resource/")


def select_mapping(resDict, res, lang, res_class, g):
    """
    Select the mapping rules to apply
    :param resDict: dictionary representing current resource
    :param res: current resource name
    :param res_class: resource class/type (e.g. Writer)
    :param lang: resource language
    :param g: RDF graph to be created
    """
    try:
        domain = MAPPING[res_class]  # BIBLIOGRAPHY
        domain_keys = eval(domain)[lang]  # [opere, ecc]
    except KeyError:
        print("Could not find a mapping for the extraction")
        return

    if lang != 'en':  # correct dbpedia resource domain for non-english language
        global dbr
        dbr = rdflib.Namespace("http://" + lang + ".dbpedia.org/resource/")

    db_res = rdflib.URIRef(dbr + res.decode('utf-8'))
    res_triples = 0
    for res_key in resDict.keys():  # iterate on resource dictionary keys
        for dk in domain_keys:  # search for resource keys related to the selected domain
            if re.search(dk, res_key, re.IGNORECASE):  # if they match, apply bibliography mapping
                mapper = "map_" + domain.lower() + "(resDict[res_key], res_key, db_res, lang, g)"
                res_triples += eval(mapper)  # calls the proper mapping for that domain
    print("Nodes extracted from " + res + ": " + str(res_triples))
    return res_triples


def map_bibliography(elem_list, sect_name, res, lang, g):
    '''
    Handles lists related to bibliography contained in a section
    adding RDF triples containing the resource, its author and its publication year
    :param elem_list: list of elements to be mapped
    :param sect_name: section name, used to reconcile literary genre
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    '''
    lit_genre = litgenre_mapper(sect_name, lang)
    triples = 0
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            map_bibliography(elem, sect_name, res, lang, g)
        else:
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            ref = reference_mapper(elem)  # look for resource references
            if ref != None:  # current element contains a reference
                uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                if (uri != None):
                    dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                    if dbpedia_uri != None:  #if you can find a DBpedia res, use it as subject
                        uri = dbpedia_uri
                else:  # Take the reference name anyway if you can't reconcile it
                    ref = list_elem_clean(ref)
                    elem = elem.replace(ref,
                                        "")  # subtract reference part from list element, to facilitate further parsing
                    uri_name = ref.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name) ###
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')
                #print (rdflib.URIRef(uri) + " " + dbo.author + " " + res)
                g.add((rdflib.URIRef(uri), dbo.author, res))
                triples+=1
            else:  # no reference found
                uri_name = general_mapper(elem)
                if (uri_name != None and uri_name != "" and uri_name != res):
                    uri_name = uri_name.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name) ###
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')
                    #print (rdflib.URIRef(uri) + " " + dbo.author + " " + res)
                    g.add((rdflib.URIRef(uri), dbo.author, res))
                    triples += 1
            if uri != None and uri != "":
                year = year_mapper(elem)
                if year != None:
                    # print (rdflib.URIRef(uri) + " " + dbo.releaseYear + " " + year)
                    g.add((rdflib.URIRef(uri), dbo.releaseYear, rdflib.Literal(year, datatype=rdflib.XSD.gYear)))

                if lit_genre != None:
                    # print (rdflib.URIRef(uri) + " " + dbo.literaryGenre + " " + dbr + lit_genre)
                    g.add((rdflib.URIRef(uri), dbo.literaryGenre, dbr + rdflib.URIRef(lit_genre)))

    return triples



def reference_mapper(list_elem):
    '''
    Looks for a reference inside the element, which has been marked by {{ }} by wikiParser
    :param list_elem: current list element
    :return: a match if found, excluding number references
    '''
    match_ref = re.search(r'\{\{.*?\}\}', list_elem)
    if match_ref != None:
        match_ref = match_ref.group()
        match_num = re.search(r'[0-9]{4}', match_ref)  # check if this reference is a date
        if match_num != None:  # date references must be ignored for this mapping
            num = match_num.group()
            new_ref = re.sub(r'\{\{.*\}\}', "", num, count=1)  # delete the number part
            match_ref = reference_mapper(new_ref)  #call again reference_mapper passing the new reference
    return match_ref



def general_mapper(list_elem):
    '''
    Called when no reference is found, applies a regex to find the main concept and cuts off punctuation marks
    :param list_elem: current list element
    :return: a match if found
    '''
    list_elem = list_elem_clean(list_elem)
    # look for strings and cut everything which follows punctuation
    match_str = re.search(r"[^0-9][^,|:|\-|–|(*|\[*]+", list_elem, re.IGNORECASE)
    if match_str != None:
        match_str = match_str.group()
        match_str = match_str.lstrip()
        match_str = match_str.lstrip('\'')
        match_str = match_str.lstrip('\'')
        match_str = match_str.rstrip('\'')
        match_str = match_str.lstrip(':')
        match_str = match_str.lstrip('-')
        match_str = match_str.lstrip('–')
        match_str = match_str.lstrip('(')
        match_str = match_str.lstrip(',')
        match_str = match_str.lstrip()
        match_str = match_str.rstrip()
    '''
    print("general mapper: "),
    print(match_str)
    '''
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
    '''
    print("year: "),
    print(match_num)
    '''
    return match_num


def litgenre_mapper(sect_name, lang):
    """
    Tries to match the section name with a literary genre provided in BIBLIO_GENRE dictionary,
    if a genre is found, it checks also for multiple matches and ignores them
    (some sections can be called 'Novels and short stories', so it's impossible to know if each list element is actually novels or short stories.
    :param sect_name: wikipedia section name, to reconcile
    :param language: resource/endpoint language
    :return: a literary genre if there is a match, None otherwise
    """
    b_genres = BIBLIO_GENRE[lang]
    for bg in b_genres.keys():  # iterate on literary genres provided for the given language
        if re.search(bg, sect_name, re.IGNORECASE):  # try to match section name with a genre
            for other_bg in b_genres.keys():
                if bg != other_bg and re.search(other_bg, sect_name,
                                                re.IGNORECASE):  # if another genre also matches the current section
                    return None
            return b_genres[bg]


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
    # utf8_res = res.encode('utf-8')  # first encode the string in utf8 format to keep safe from special characters
    enc_res = urllib2.quote(res)  # then encode the string to be used in a URL

    req = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&search=' + enc_res + '&language=' + lang
    try:
        call = urllib2.Request(req)
        resp = urllib2.urlopen(call)
        answer = resp.read()
        parsed_ans = json.loads(answer)
        result = parsed_ans['search']
        if result == []:  # no URis found
            return None
        uri = result[0]['concepturi']
    except urllib2.URLError:  # sometimes the host can refuse too many connections and returns a socket error
        time.sleep(5)
        print("retrying Wikidata API call...")
        wikidataAPI_call(res, lang)
        # raise
    except:
        print ("Wikidata API error on request " + req)
    else:
        return uri


# Not using this for now since it works only for english and Wikidata API has shown to provide better results
def find_DBpedia_uri(wk_uri, lang):
    '''
    Used to find equivalent URI in DBpedia from a Wikidata one
    :param wk_uri: URI found using the WikiData API
    :param lang: resource/endpoint language
    :return: DBpedia equivalent URI if found
    '''
    query = "select distinct ?s where {?s <http://www.w3.org/2002/07/owl#sameAs> <" + wk_uri + "> }"
    try:
        json = utilities.sparql_query(query, lang)
    except IOError:
        time.sleep(5)
        print("retrying DBpedia API call...")
        find_DBpedia_uri(wk_uri, lang)
    try:
        result = json['results']['bindings'][0]['s']['value']
    except:
        result = None
    '''
    print ("Dbpedia res: "),
    print(result)
    '''
    return result


def list_elem_clean(list_elem):
    list_elem = list_elem.lstrip()
    list_elem = list_elem.replace("{", "")
    list_elem = list_elem.replace("}", "")
    list_elem = list_elem.replace("«", "")
    list_elem = list_elem.replace("»", "")
    list_elem = list_elem.replace("\'\'", "")
    list_elem = list_elem.replace("\"", "")
    list_elem = list_elem.replace("#", "")
    return list_elem
