# -*- coding: utf-8 -*-

'''
#########
 Mapper
#########

* This module contains all the core methods/functions that are used for RDF-triple generation.


* This module mainly consists of the mapping functions that are used by the extractors based on \
rules present in ``setting.json``, ``mapping_rules.py`` and ``custom_mappers.json``.


* This module also contains the extractors and some other helper functions that are used by the mapping \
functions to generate triples.


'''

import urllib2
import json
import re
import rdflib
import utilities
import time
from mapping_rules import *


#defining namespaces to be used in the extracted triples
dbo = rdflib.Namespace("http://dbpedia.org/ontology/")
dbr = rdflib.Namespace("http://dbpedia.org/resource/")
rdf = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

mapped_domains = []  # used to prevent duplicate mappings
resource_class = ""

# These would contain the mapping rules and the custom defined mapping functions that would be used by the
# mapper functions. These are initially empty and loaded when mapper functions are selected for each resource.
MAPPING = dict()
CUSTOM_MAPPERS = dict()


def select_mapping(resDict, res, lang, res_class, g):
    ''' Calls mapping functions for each matching section of the resource, thus constructing the associated RDF graph.

    Firstly selects the mapping type(s) to apply from ``MAPPING`` (loaded from ``settings.json``) based on resource class (domain).
    If a match is found, it tries to find another match between section names and key-words related to that domain.
    Finally, it applies related mapping functions for the list elements contained in that section.

    :param resDict: dictionary representing current resource.
    :param res: current resource name.
    :param res_class: resource class/type (e.g. ``Writer``).
    :param lang: resource language.
    :param g: RDF graph to be created.

    :return: number of list elements actually mapped in the graph.
    '''

    #use globally defined dicts
    global mapped_domains
    global resource_class
    global MAPPING
    global CUSTOM_MAPPERS
    
    if len(MAPPING) == 0: #load initial configuration
        MAPPING = utilities.load_settings()
        CUSTOM_MAPPERS = utilities.load_custom_mappers()
    
    # initialize the number of triples extracted
    res_elems = 0

    #if required class is a valid and existing class in the mapping, run suitable mapper functions
    if res_class in MAPPING and MAPPING[res_class] not in mapped_domains:
        if lang != 'en':  # correct dbpedia resource domain for non-english language
            global dbr
            dbr = rdflib.Namespace("http://" + lang + ".dbpedia.org/resource/")
        db_res = rdflib.URIRef(dbr + res.decode('utf-8'))
        
        domains = MAPPING[res_class]  # e.g. ['BIBLIOGRAPHY', 'FILMOGRAPHY']
        domain_keys = []
        resource_class = res_class

        for domain in domains:
            if domain in mapped_domains:
                continue
            
            is_custom_map_fn = False
            try:
                if lang in eval(domain):
                    domain_keys = eval(domain)[lang]  # e.g. ['bibliography', 'works', ..]
                else:
                    print("The language provided is not available yet for this mapping")
                    return 0
            except NameError:  #key not found(predefined mappers)
                if domain not in CUSTOM_MAPPERS.keys():
                    print "Cannot find the domain's mapper function!!"
                    print 'You can add a mapper function for this mapping using rulesGenerator.py and try again...\n'
                    return 0
                else:
                    is_custom_map_fn = True
                    domain_keys = CUSTOM_MAPPERS[domain]["headers"][lang]

            mapped_domains.append(domain)  #this domain won't be used again for mapping
    
            for res_key in resDict.keys():  # iterate on resource dictionary keys
                mapped = False
        
                for dk in domain_keys:  # search for resource keys related to the selected domain
                    # if the section hasn't been mapped yet and the title match, apply domain related mapping
                    dk = dk.decode('utf-8') #make sure utf-8 mismatches don't skip sections 
                    if not mapped and re.search(dk, res_key, re.IGNORECASE):
                        try:
                            if is_custom_map_fn == False:
                                #use the pre-defined mapper functions
                                mapper = "map_" + domain.lower() + "(resDict[res_key], res_key, db_res, lang, g, 0)"
                                res_elems += eval(mapper)  # calls the proper mapping for that domain and counts extracted elements
                                mapped = True  # prevents the same section to be mapped again
                            else:
                                mapper = map_user_defined_mappings(domain, resDict[res_key], res_key, db_res, lang, g, 0)
                                res_elems += mapper  # calls the proper mapping for that domain and counts extracted elements
                                mapped = True  # prevents the same section to be mapped again
                        except:
                            print 'exception occured in resDict, skipping....'

    else:
        # print 'This domain has not been mapped yet!'
        # print 'You can add a mapping for this domain using rulesGenerator.py and try again...\n'
        return 0

    return res_elems


def map_user_defined_mappings(mapper_fn_name, elem_list, sect_name, res, lang, g, elems):
    ''' **This is the made module that runs all user-defined mapper functions.**

    * It uses the ``CUSTOM_MAPPERS`` dict to find the settings assotiated with the domain, and then runs \
    the mapping functions according to the settings and adds the associated triples in the RDF graph.

    * Firstly selects the settings to apply from ``custom_mappers.json`` based on resource class (domain).
    * If a match is found, it tries to find another match between section names and key-words related to that domain.
    * Finally, it applies related mapping functions for the list elements contained in that section.

    :param mapper_fn_name: Name of the custom mapper function from which settings(eg. section headers,
                           ontology classes, extractors to be used etc.) are loaded.
    :param resDict: dictionary representing current resource.
    :param res: current resource name.
    :param res_class: resource class/type (e.g. ``Writer``).
    :param lang: resource language.
    :param g: RDF graph to be created.
    
    :return: number of list elements actually mapped in the graph.
    '''
    global CUSTOM_MAPPERS
    
    #determine if the custom mapper function exists; if yes, load it.
    mapper_settings = dict()
    try:
        mapper_settings = CUSTOM_MAPPERS[mapper_fn_name]
    except: #not found, skip the rest of the process
        print 'Did not find', mapper_fn_name, 'in CUSTOM_MAPPERS!'
        return 0

    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_user_defined_mappings(mapper_fn_name, elem, sect_name, res, lang, g, elems)   # handle recursive lists

        else:
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            years = []
            if mapper_settings["years"] == "Yes": #extract years related to the resource.
                years = month_year_mapper(elem)
            
            #load the ontologies to be used in the triple generation
            ontology_class = None
            for class_type in mapper_settings["ontology"][lang]:
                try:
                    #find a matching sub-section from the ontology class
                    if class_type.decode('utf-8').lower() in sect_name.decode('utf-8').lower():
                        ontology_class = class_type
                except UnicodeEncodeError:
                    break

            if ontology_class == None:   #No possible mapping found; try default mapping
                if mapper_settings["ontology"][lang]["default"] == "None": 
                    return 0 #default wasn't allowed
                else: 
                    ontology_class = "default"
                    # print 'Matching Header not found, using default ontology relation:', str(ontology_class)
            
            #final ontology class/property for the current element
            p = mapper_settings["ontology"][lang][ontology_class]
            
            #selection of the extractors to be used in the triple generation
            extractor_choices = mapper_settings["extractors"]

            #initital uri and resource names of the triple (triple form: <uri dbo:p res_name>)
            uri = None
            res_name = None

            if res_name == None and 1 in extractor_choices: #italics mapper was chosen
                res_name = italic_mapper(elem)
                if res_name:
                    elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                    res_name = res_name.replace(' ', '_')
                    res_name = urllib2.quote(res_name)  #quoting res_name in proper format
                    uri = dbr + res_name.decode('utf-8', errors='ignore')

            if res_name == None and 2 in extractor_choices: #reference mapper was chosen
                res_name = reference_mapper(elem)
                if res_name:  # current element contains a reference
                    uri = wikidataAPI_call(res_name, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    else:  # Take the reference name anyway if you can't reconcile it
                        res_name = list_elem_clean(res_name)
                        elem = elem.replace(res_name, "")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = res_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  #quoting res_name in proper format
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            if res_name == None and 3 in extractor_choices: #quote mapper was chosen
                res_name = quote_mapper(elem)
                if res_name:
                    elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                    res_name = res_name.replace(' ', '_')
                    res_name = urllib2.quote(res_name)  #quoting res_name in proper format
                    uri = dbr + res_name.decode('utf-8', errors='ignore')


            if res_name == None and 4 in extractor_choices: #general mapper was chosen
                res_name = general_mapper(elem)
                if (res_name and res_name != "" and res_name != res):
                        res_name = res_name.replace(' ', '_')
                        res_name = urllib2.quote(res_name)  #quoting res_name in proper format
                        uri = dbr + res_name.decode('utf-8', errors='ignore')

            #if successfully found a triple, add that to the existing graph
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo[p], res))
                elems += 1
                if years:
                    add_years_to_graph(g, uri, years)

    if elems == 0: print 'Could not extract any elements. Try adding more extractors....'
    return elems


def map_discography(elem_list, sect_name, res, lang, g, elems):
    ''' Handles albums list present inside a section containing a match with ``DISCOGRAPHY``.

    Adds RDF statement about the album, its artist (the current resource) and the year it was launched.
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
   
    :return: number of list elements extracted.
    '''

    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_discography(elem, sect_name, res, lang, g, elems)   # handle recursive lists
        
        else:
            year = month_year_mapper(elem) #map years present in the list
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            if res_name == None: res_name = quote_mapper(elem)
            
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)  ###
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
            #add successfuly extracted triples into the graph
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), rdf.type, dbo.Album))
                g.add((rdflib.URIRef(uri), dbo.musicalArtist, res))
                elems += 1
                if year:
                    add_years_to_graph(g, uri, year, {'activeYear':'releaseYear'})

    return elems


def map_concert_tours(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists of concerts present inside a section containing a match with ``CONCERT_TOURS``.

    Adds RDF statement about the tour, its artist (the current resource) and the year it was launched.
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
   
    :return: number of list elements extracted.
    '''
    
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_concert_tours(elem, sect_name, res, lang, g, elems)   # handle recursive lists
        
        else:
            year = month_year_mapper(elem)
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            if res_name == None: res_name = quote_mapper(elem)
           
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
            #add successfuly extracted triples into the graph
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), rdf.type, dbo.concertTour))
                g.add((rdflib.URIRef(uri), dbo.musicalArtist, res))
                elems += 1
                if year:
                    add_years_to_graph(g, uri, year)

    return elems


def map_alumni(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists of alumni members present inside a section containing a match with ``ALUMNI``.

    Adds RDF statement about the person and its assosiation with the resource(organisation).
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
   
    :return: number of list elements extracted.
    '''
    
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_alumni(elem, sect_name, res, lang, g, elems)   # handle recursive lists
        
        else:
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name) 
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.alumni, res))
                elems += 1
                work = alumni_profession_mapper(elem)
                if work:
                    g.add((rdflib.URIRef(uri), dbo.notableWork, rdflib.Literal(work, datatype=rdflib.XSD.string)))
    return elems


def map_programs_offered(elem_list, sect_name, res, lang, g, elems):
    ''' Handles list present inside a section containing a match with ``PROGRAMS_OFFERED``.

    Adds RDF statement about the programs offered by the resource(organisation).
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
   
    :return: number of list elements extracted.
    '''
    
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_programs_offered(elem, sect_name, res, lang, g, elems)   # handle recursive lists
        
        else:
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)  
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.academicDiscipline, res))
                elems+=1
            
    return elems


def map_honors(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to awards and honors given to people inside a section containing \
    a match with ``HONORS``.

    Adds RDF statements about the awards, and its details(if present) and the recipient.

    :param elem_list: list of elements to be mapped.
    :param sect_name: section name, used to reconcile literary genre.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.

    :return: number of list elements extracted.
    '''
    
    award_status = award_status_mapper(sect_name, lang)  # if award status is found in the section name.
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_honors(elem, sect_name, res, lang, g, elems)
        
        else:
            uri = None

            #find out the status of the award; i.e winner or nominated
            if award_status == None: award_status = award_status_mapper(elem, lang)
            if award_status == None: award_status = "Winner" #if no information is found, assume winner.

            elem = elem.encode('utf-8')  # apply utf-8 encoding

            #remove status from the element
            elem = elem.replace("Winner","").replace("Won","").replace("Nominated","").replace("Nominee","")
            
            #find out the resource for which the award was given
            for_entity = sentence_splitter(elem,"for",lang)

            #the entity providing the award
            from_entity = sentence_splitter(elem,"from",lang)
            year = month_year_mapper(elem)

            ref = reference_mapper(elem)  # look for resource references
            if ref:  # current element contains a reference
                uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    
                if uri:
                    dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                    if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                        uri = dbpedia_uri
                    
                else:  # Take the reference name anyway if you can't reconcile it
                    ref = list_elem_clean(ref)
                    elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                    uri_name = ref.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name)  
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')
            else:
                uri_name = quote_mapper(elem)  #try finding awards in quotes
                if uri_name == None: uri_name = general_mapper(elem)  # no reference found, try general mapping (less accurate
                if (uri_name and uri_name != "" and uri_name != res):
                    uri_name = uri_name.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name)  
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.awardedTo, res))
                g.add((rdflib.URIRef(uri), dbo.awardStatus, dbo + rdflib.URIRef(award_status)))
                if year:
                    add_years_to_graph(g, uri, year)
                if for_entity:
                    g.add((rdflib.URIRef(uri), dbo.AwardedFor, dbr + rdflib.URIRef(for_entity)))
                if from_entity:
                    g.add((dbo + rdflib.URIRef(award_status), dbo.AwardedBy, dbr + rdflib.URIRef(from_entity)))

                elems += 1
    
    return elems


def map_staff(elem_list, sect_name, res, lang, g, elems):
    ''' Handles list present inside a section containing a match with ``STAFF``.

    Adds RDF statement about the staff members and the institution.
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
   
    :return: number of list elements extracted.
    '''
    
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_staff(elem, sect_name, res, lang, g, elems)   # handle recursive lists
        
        else:
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)  ###
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph                
            if uri and uri != "":
                if len(list(g.triples((rdflib.URIRef(uri), dbo.alumni, res)))) == 0 and \
                    len(list(g.triples((rdflib.URIRef(uri), dbo.academicDiscipline, res)))) ==0: # if already mapped
                    g.add((rdflib.URIRef(uri), dbo.staff, res))
    
    return elems


def map_other_person_details(elem_list, sect_name, res, lang, g, elems):
    ''' Handles list present inside a section containing a match with ``OTHER``.

    Adds RDF statement about the unclassified sections in ``Person`` domain.
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
   
    :return: number of list elements extracted.
    '''
    
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_other_person_details(elem, sect_name, res, lang, g, elems)   # handle recursive lists
        
        else:
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            
            other_details = None
            for other_type in OTHER_PERSON_DETAILS[lang]:
                if other_type.decode('utf-8').lower() in sect_name.decode('utf-8').lower():
                    other_details = other_type

            if other_details == None:   #No possible mapping found; leave the element
                return 0
            
            p = PERSON_DETAILS[lang][other_details]
            
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)  
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                uri_name = quote_mapper(elem)
                if (uri_name and uri_name != "" and uri_name != res):
                    uri_name = uri_name.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name)  
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')

                ref = None
                if uri == None: ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo[p], res))
                elems+=1

    return elems


def map_career(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to awards and honors given to people inside a section containing a \
    match with ``CAREER``.

    Adds RDF statements about the career (academic/professional), and its details(if present) \
    and the recipient.
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name, used to reconcile literary genre.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
    
    :return: number of list elements extracted.
    '''
    
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_career(elem, sect_name, res, lang, g, elems)
        
        else:
            year = month_year_mapper(elem)            
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding

            other_details = None
            for other_type in CAREER[lang]:
                #print other_type
                if other_type.encode('utf-8').lower() in sect_name.encode('utf-8').lower():
                    other_details = other_type

            if other_details == None:   #No possible mapping found; leave the element
                return 0
            
            #ontology property/class to be used for this resource
            p = PERSON_DETAILS[lang][other_details]
            
            uri_name = quote_mapper(elem)
            if uri_name == None or uri_name == res: uri_name = general_mapper(elem)
            if (uri_name and uri_name != "" and uri_name != res):
                uri_name = uri_name.replace(' ', '_')
                uri_name = urllib2.quote(uri_name)  ###
                uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo[p], res))
                elems += 1
                if year:
                    add_years_to_graph(g,uri, year)                
    return elems


def map_filmography(elem_list, sect_name, res, lang, g, elems):
    '''Handles lists related to filmography inside a section containing a match with ``FILMOGRAPHY``.

    It constructs RDF statements about the movie title, it release year and type (``Film``, ``TV show``, ``Cartoon``..)
    and which part the current resource took in it (``director``, ``actor``, ...)
    
    :param elem_list: list of elements to be mapped.
    :param sect_name: section name, used to reconcile literary genre.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
    
    :return: number of list elements extracted.
    '''
    film_particip = filmpart_mapper(sect_name, lang)  # applied to every list element of the section, default:starring
    filmography_type = filmtype_mapper(sect_name, lang)  #same as above
    for elem in elem_list:
        if type(elem) == list:  #for nested lists (recursively call this function)
            elems += 1
            map_filmography(elem, sect_name, res, lang, g, elems)
        
        else:
            year = month_year_mapper(elem)
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)  # Try to extract italic formatted text (more precise)
            
            if res_name:
                elem = elem.replace(res_name, "")  #delete occurence of matched text for further extraction
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:  #if unsuccessful, apply general mapping (lower accuracy)
                uri_name = quote_mapper(elem)  #try finding names in quotes
                if uri_name == None: uri_name = general_mapper(elem)  # no reference found, try general mapping (less accurate
                if (uri_name and uri_name != "" and uri_name != res):
                    uri_name = uri_name.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name)
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), rdf.type, dbo + rdflib.URIRef(filmography_type)))
                if year:
                    add_years_to_graph(g, uri, year, {'activeYear':'releaseYear'})
                if film_particip:
                    g.add((rdflib.URIRef(uri), dbo + rdflib.URIRef(film_particip), res))
                elems += 1
    
    return elems


def map_bibliography(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to bibliography inside a section containing a match with ``BIBLIOGRAPHY``.

    Adds RDF statement about the work title, its author (the current resource), publication year and ISBN code.

    :param elem_list: list of elements to be mapped.
    :param sect_name: section name, used to reconcile literary genre.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.

    :return: number of list elements extracted.
    '''

    # literary genre depends on the name of the section, so it is the same for every element of the list
    lit_genre = litgenre_mapper(sect_name, lang)  #literary genre is the same for every element of the list
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_bibliography(elem, sect_name, res, lang, g, elems)
        
        else:
            uri = None
            year = month_year_mapper(elem)
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)  
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref,"")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:
                    uri_name = quote_mapper(elem)  #try finding awards in quotes
                    if uri_name == None or uri_name == res: uri_name = general_mapper(elem)  # no reference found, try general mapping (less accurate
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.author, res))
                elems += 1
                isbn = isbn_mapper(elem)
                if isbn:
                    g.add((rdflib.URIRef(uri), dbo.isbn, rdflib.Literal(isbn, datatype=rdflib.XSD.string)))
                    elem = elem.replace(isbn, "")  
                if year:
                    add_years_to_graph(g, uri, year)
                if lit_genre:
                    g.add((rdflib.URIRef(uri), dbo.literaryGenre, dbo + rdflib.URIRef(lit_genre)))
    
    return elems


def map_band_members(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to members inside a section containing a match with ``BAND_MEMBERS``.

    Adds RDF statement about the band and its members.

    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.
    
    :return: number of list elements extracted.
    '''
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_members(elem, sect_name, res, lang, g, elems)

        else:
            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            res_name = italic_mapper(elem)
            if res_name:
                elem = elem.replace(res_name, "")  #delete resource name found from element for further mapping
                res_name = res_name.replace(' ', '_')
                res_name = urllib2.quote(res_name)  
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref,"")  #subtract reference part from list element to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.bandMember, res))
                elems += 1
                
    return elems


def map_contributors(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to contributions made by a person inside a section containing a \
    match with ``CONTRIBUTORS``.

    Adds RDF statement about the person and his contributions.

    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.

    :return: number of list elements extracted.
    '''
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_contributors(elem, sect_name, res, lang, g, elems)

        else:
            contrib_type, subsection = None, None
            search_str = sect_name

            #Find if the contribution has a predefined type(editor, writer etc.)
            try: subsection = sect_name.split('-')[1].strip()
            except: pass
            
            for t in CONTRIBUTION_TYPE[lang].keys():
                if subsection: search_str = subsection
                #if subsection exists, select corresponding ontology class from CONTRIBUTION_TYPE
                if re.search(t, search_str, flags=re.IGNORECASE):
                    contrib_type = CONTRIBUTION_TYPE[lang][t]
                    break

            #if subsection name fails, try the individual list element for the contribution
            if contrib_type == None:
                feature = bracket_feature_mapper(elem)
                for t in CONTRIBUTION_TYPE[lang]:
                    try:
                        #if list element has contribution type, select corresponding ontology class from CONTRIBUTION_TYPE
                        if re.search(t, feature, re.IGNORECASE):
                            contrib_type = CONTRIBUTION_TYPE[lang][t]
                            break
                    except: continue

            #extract and remove the time period present in the list element
            year = month_year_mapper(elem)
            if year: 
                for y in year:
                    if type(y) == list:
                        for yy in y:
                            elem= elem.replace(re.split(r'\^',yy)[-1], "")
                    else:
                        elem= elem.replace(re.split(r'\^',y)[-1], "")
                    
                elem = elem.strip()

            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            
            if True:
                ref = reference_mapper(elem)  # look for resource references
                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref,"")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph 
            if uri and uri != "":
                if contrib_type:
                    g.add((rdflib.URIRef(uri), dbo[contrib_type], res))
                else:
                    g.add((rdflib.URIRef(uri), dbo.ContributedTo, res))
                if year:
                    add_years_to_graph(g, uri, year)

                elems += 1
                
    return elems


def map_other_literature_details(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to literature details inside a section containing a \
    match with ``OTHER_LITERATURE_DETAILS``.

    :param elem_list: list of elements to be mapped.
    :param sect_name: section name.
    :param res: current resource.
    :param lang: resource language.
    :param g: RDF graph to be constructed.
    :param elems: a counter to keep track of the number of list elements extracted.

    :return: number of list elements extracted.
    '''

    #check if the existing element has already been mapped; if yes, skip element
    for c in CONTRIBUTORS[lang]:
        if re.search(c, sect_name, re.I):   #Already mapped
            return 0

    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_other_literature_details(elem, sect_name, res, lang, g, elems)

        else:
            detail_type = None
            #if subsection exists, select corresponding ontology class from OTHER_LITERATURE_DETAILS
            for t in OTHER_LITERATURE_DETAILS[lang].keys():
                if re.search(t, sect_name, flags=re.IGNORECASE):
                    detail_type = OTHER_LITERATURE_DETAILS[lang][t]
                    break

            if detail_type == None:
                feature = bracket_feature_mapper(elem)
                for t in OTHER_LITERATURE_DETAILS[lang]:
                    #if list element has contribution type, select corresponding ontology class 
                    #from OTHER_LITERATURE_DETAILS
                    if re.search(t, feature, re.IGNORECASE):
                        detail_type = OTHER_LITERATURE_DETAILS[lang][t]
                        break

            #extract and remove the time period present in the list element
            year = month_year_mapper(elem)
            if year: 
                for y in year:
                    if type(y) == list:
                        for yy in y:
                            elem= elem.replace(re.split(r'\^',yy)[-1], "")

                    else:
                        elem= elem.replace(re.split(r'\^',y)[-1], "")
                    
                elem = elem.strip()


            uri = None
            elem = elem.encode('utf-8')  # apply utf-8 encoding
            
            if True:
                ref = reference_mapper(elem)  # look for resource references
                map_failed = True

                if ref:  # current element contains a reference
                    uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    
                    if uri:
                        dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                        if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                            uri = dbpedia_uri
                    
                    else:  # Take the reference name anyway if you can't reconcile it
                        ref = list_elem_clean(ref)
                        elem = elem.replace(ref,"")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

                elif (ref is not None):  # no reference found, try general mapping (less accurate)
                    uri_name = quote_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                        map_failed = False

                if map_failed:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            #add successfuly extracted triples into the graph
            if uri and uri != "":
                if detail_type:
                    g.add((rdflib.URIRef(uri), dbo[detail_type], res))
                else:
                    g.add((rdflib.URIRef(uri), dbo.WrittenWork, res))
                if year:
                    add_years_to_graph(g, uri, year)

                elems += 1
                
    return elems


def add_years_to_graph(g, uri, year, year_ontology = {}):
    '''Adds all the years related to the URI to the graph g. 
    Does not return anything; appends existing graph.

    :param g: current graph.
    :param uri: resource related to the years list.
    :param year: contains a list of years that need to be mapped.
    :param year_ontology: dict containing ontologies that can be used with time periods in a particular domain; 
    
    * Empty dict indicates default values should be taken from y_ontology.
    
        ``y_ontology = { 'activeYear':'activeYear', 'activeYearsStartDate': 'activeYearsStartDate', 'activeYearsEndDate' : 'activeYearsEndDate'}``
    :return: void
    '''

    #default ontologies
    y_ontology = { 'activeYear':'activeYear', 'activeYearsStartDate': 'activeYearsStartDate',
                       'activeYearsEndDate' : 'activeYearsEndDate'}
    
    #update if user provides a dictionary to override default ontologies
    for ontology in year_ontology.keys():
        if ontology in y_ontology:
            y_ontology[ontology] = year_ontology[ontology]

    try:
        #start creating triples from years
        for y in year:
            if type(y) != list:  #Single date (not a time-period)
                if "^" in y:  # '^' is a seperator used for month and year
                    d = y.replace("^","-")
                    g.add((rdflib.URIRef(uri), dbo[y_ontology['activeYear']], rdflib.Literal(d, datatype=rdflib.XSD.gYearMonth)))

                else:    
                    g.add((rdflib.URIRef(uri), dbo[y_ontology['activeYear']], rdflib.Literal(y, datatype=rdflib.XSD.gYear)))
            
            else:   #if the date is a time period (has a start-end date)
                start_period, end_period = y[0], y[1]
                if "^" in y[0]:   # '^' is a seperator used for month and year
                    d = y[0].replace("^","-")
                    g.add((rdflib.URIRef(uri), dbo[y_ontology['activeYearsStartDate']], rdflib.Literal(d, datatype=rdflib.XSD.gYearMonth)))
                else:    
                    g.add((rdflib.URIRef(uri), dbo[y_ontology['activeYearsStartDate']], rdflib.Literal(y[0], datatype=rdflib.XSD.gYear)))

                if "^" in y[1]:
                    d = y[1].replace("^","-")
                    g.add((rdflib.URIRef(uri), dbo[y_ontology['activeYearsEndDate']], rdflib.Literal(d, datatype=rdflib.XSD.gYearMonth)))

                else:    
                    g.add((rdflib.URIRef(uri), dbo[y_ontology['activeYearsEndDate']], rdflib.Literal(y[1], datatype=rdflib.XSD.gYear)))

    except:
        print 'Year exception! Skipping...'
        raise
    return

def alumni_profession_mapper(list_elem):
    '''Applies a regex to look for a profession, returns a match if found.
    Profession is expected to present after the resource name, seperated by either a hyphen or comma.
    
    :param list_elem: current list element.

    :return: a match for profession, if present.
    '''
    #regex for finding profession in the list element
    profession = re.search(r'[^-|,]+$', list_elem)

    #if found, return the profession
    if profession != None:
        profession = profession.group()
        profession = profession.replace("{{", "").replace("}}","")
        if profession[0] == " ": profession = profession[1:]
    
    return profession

def isbn_mapper(list_elem):
    '''Applies a regex to look for a ISBN number, returns a match if found.

    `ISBN or International Standard Book Number consists of 4 parts and 10 digits (if assigned before 2007)
    where the last character may equal to the letter "X", or 5 parts and 13 digits , possibly separated by hyphens`.
    
    :param list_elem: current list element.
    
    :return: a match for a isbn code, if present.
    '''

    #regex for finding ISBN in the list element
    match_isbn = re.search(r'ISBN ([0-9]|-)*X?', list_elem)

    #if found, return the ISBN
    if match_isbn != None:
        match_isbn = match_isbn.group()
        match_isbn = match_isbn.replace('ISBN ', "")
    
    return match_isbn

def year_mapper(list_elem):
    '''Looks for a set of exactly 4 digits which would likely represent the year.
    The most basic year extractor, used as a subroutine by ``month_year_mapper()``.

    :param list_elem: current list element.

    :return: a numeric match if found.
    '''
    match_num = re.findall(r'[0-9]{4}', list_elem)
    if len(match_num) == 0: return None
    return match_num

def month_year_mapper(list_elem):
    '''Looks for any kind of date formats; years, month+year or actual date and returns list of dates.

    :param list_elem: current list element.

    :return: a numeric match if found.
    '''
    
    # month_list a dictionaly that contain regex for different months as keys and a corresponding number
    # to that month with a '^' sign as value. This would be useful while mapping the years in the triples.
    month_list = { r'(january\s?)\d{4}':'1^', r'\W(jan\s?)\d{4}':'1^', r'(february\s?)\d{4}':'2^', r'\W(feb\s?)\d{4}':'2^',
                    r'(march\s?)\d{4}':'3^', r'\W(mar\s?)\d{4}':'3^',r'(april\s?)\d{4}':'4^',r'\W(apr\s?)\d{4}':'4^', 
                    r'(may\s?)\d{4}':'5^', r'\W(may\s?)\d{4}':'5^',r'(june\s?)\d{4}':'6^',r'\W(jun\s?)\d{4}':'6^',
                    r'(july\s?)\d{4}':'7^',r'\W(jul\s?)\d{4}':'7^', r'(august\s?)\d{4}':'8^', r'\W(aug\s?)\d{4}':'8^', 
                    r'(september\s?)\d{4}':'9^', r'\W(sep\s?)\d{4}':'9^',r'\W(sept\s?)\d{4}':'9^', r'(october\s?)\d{4}':'10^',
                    r'\W(oct\s?)\d{4}':'10^',r'(november\s?)\d{4}':'11^', r'\W(nov\s?)\d{4}':'11^' ,
                    r'(december\s?)\d{4}':'12^', r'\W(dec\s?)\d{4}':'12^'}
    
    month_present = False
    period_dates = False

    #check if the time period only contains year or if it also contain months
    for mon in month_list:
        if re.search(mon, list_elem, re.IGNORECASE):
            #find and replace the month name with corresponding month code from month_list
            rep = re.search(mon, list_elem, re.IGNORECASE).group(1)
            list_elem = re.sub(rep, month_list[mon], list_elem, flags=re.I)
            month_present = True

    #regex for finding out whether the date consists of a time period or a single year.
    period_regex = ur'(?:\(?\d{1,2}\^)?\s?\d{4}\s?(?:–|-)\s?(?:\d{1,2}\^)?\s?\d{4}(?:\))?'  

    if re.search(period_regex, list_elem, flags=re.IGNORECASE):
        period_dates = True

    #check for the 4 possible cases of months and time periods

    #if the year doesn't have months or time period, use less complicated year_mapper()
    if month_present == False and period_dates == False:
        return year_mapper(list_elem)
    
    years = []

    #if only yearly time period is present
    if month_present == False and period_dates == True:
        match_num =  re.findall(period_regex, list_elem, flags=re.IGNORECASE)
        if len(match_num) == 0: return year_mapper(list_elem)
        
        for y in match_num:   #split start and end year
            year = re.split(ur'\s?[–-]\s?', y)
            years.append([year[0], year[1]])
        
        for x in match_num:
            list_elem = list_elem.replace(x,"")

        #append the list of the years and return them
        single_years = year_mapper(list_elem)   
        if single_years != None: years.extend(single_years)
        return years
        
    #if only month is present, no time-periods
    if month_present == True and period_dates == False:
        match_num = re.findall(r'[0-9]{1,2}\^\s?[0-9]{4}', list_elem)
        for x in match_num:
            #replace and format the time period in appropriate form (month^year) and append it int the list
            list_elem = list_elem.replace(x,"")
            x = x.replace(" ","")
            z = "^".join(x.split('^')[::-1])
            years.append(z)

        single_years = year_mapper(list_elem)
        if single_years != None: years.extend(single_years)
        return years

    else: #if both months and periiods are present
        match_num = re.findall(period_regex, list_elem, flags=re.IGNORECASE)
        if len(match_num) == 0: return year_mapper(list_elem)

        for y in match_num:
            #replace and format the time period in appropriate form [(month^year), (month^year)] 
            #and append it int the list
            year = re.split(r'\s?(–|-)\s?', y)
            list_elem = list_elem.replace(y,"")
            years.append(["^".join(year[0].replace(" ","").split("^")[::-1]), "^".join(year[2].replace(" ","").split("^")[::-1])])

        single_years = year_mapper(list_elem)
        if single_years != None: years.extend(single_years)
        return years

def litgenre_mapper(sect_name, lang):
    '''Tries to match the section name with a literary genre provided in ``BIBLIO_GENRE`` dictionary.

    If a genre is found, it also checks for multiple matches and ignores them \
    (some sections may be called 'Novels and short stories', therefore it's impossible to know if each list element
    is actually a novel or a short story).

    :param sect_name: wikipedia section name, to reconcile.
    :param language: resource/endpoint language.
    
    :return: a literary genre if there is a match, ``None`` otherwise.
    '''
    b_genres = BIBLIO_GENRE[lang]
    for bg in b_genres.keys():  # iterate on literary genres provided for the given language
        if re.search(bg, sect_name, re.IGNORECASE):  # try to match section name with a genre
            for other_bg in b_genres.keys():
                # sect_name = sect_name.replace(bg, "")
                if other_bg != bg and re.search(other_bg, sect_name,
                                                re.IGNORECASE):  #if another genre also matches the current section
                    return None
            
            return b_genres[bg]

def filmpart_mapper(sect_name, lang):
    ''' Returns the part the person took in that movie as a property (e.g. ``starring``, ``director`` etc...)
    In order to do so, confronts section titles with ``FILMOGRAPHY_PARTICIPATION``. Default value is ``starring``.

    :param sect_name: section and sub-section name to compare with a regex.
    
    :return: a property if there is a match, ``None`` otherwise.
    '''
    film_particip = 'starring'  #default property for Actors is 'starring'
    f_parts = FILMOGRAPHY_PARTICIPATION[lang]
    for fp in f_parts.keys():
        if re.search(fp, sect_name, re.IGNORECASE):
            film_particip = f_parts[fp]
    
    return film_particip

def filmtype_mapper(sect_name, lang):
    ''' Returns the type of Filmography elements in current list as a class (``TelevisionShow``, ``Cartoon`` etc...)
    In order to do so, confronts section titles with ``FILMOGRAPHY_TYPE``. Default value is ``Movie``.

    :param sect_name: section and sub-section name to compare with a regex.
    :param lang: page language.
    
    :return: a class if there is a match, ``None`` otherwise.
    '''
    filmtype = 'Film'  # default type for Filmography elements is 'Film'
    f_types = FILMOGRAPHY_TYPE[lang]
    for ft in f_types.keys():
        if re.search(ft, sect_name, re.IGNORECASE):
            filmtype = f_types[ft]
    
    return filmtype

def award_status_mapper(sect_name, lang):
    ''' Returns the status of the award to the recipient; default is Winning, i.e. ``Awarded``.

    :param sect_name: section and sub-section name to compare with a regex.
    :param lang: page language.

    :return: a class if there is a match, ``None`` otherwise.
    '''
    status = None
    s_types = AWARD_STATUS_TYPE[lang]
    for st in s_types.keys():
        if re.search(st, sect_name, re.IGNORECASE):
            status = s_types[st]
    
    return status

def sentence_splitter(elem,word,lang):
    ''' Generic method that returns (if any) the second part (``URI``, if possible) of the sentence after \
    splitting the sentence using the supplied word.
    
    Can be use to extract more information from a single list element, which can contain complex compound \
    information.
    For eg. '``X`` won ``Y`` award **FOR** ``Z`` work **FROM** ``V`` organisation.'
    splitting at FOR and FROM can potentially create more triples with the work and organisation.

    :param elem: dictionary element entry.
    :param word: the word on which to split (must exist in ``TRANSLATIONS`` in ``mapping_rules.py``).
    :param lang: page language.

    :return: an entity if there is a match, None otherwise
    '''
    entity = None

    #finding the term for different languages
    term = TRANSLATIONS[word][lang]
    
    #take the ending from the sentence and try to find if it has a reference uri
    val = re.split(term,elem)
    if len(val)>1:
        entity = val[-1]

        ref = reference_mapper(entity)  # look for resource references
        if ref:  # current element contains a reference
            uri = wikidataAPI_call(ref, lang)  #try to reconcile resource with Wikidata API
                    
            if uri:
                dbpedia_uri = find_DBpedia_uri(uri, lang)  # try to find equivalent DBpedia resource
                if dbpedia_uri:  # if you can find a DBpedia res, use it as the statement subject
                    uri = dbpedia_uri
                    
            else:  # Take the reference name anyway if you can't reconcile it
                ref = list_elem_clean(ref)
                elem = elem.replace(ref, "")  #subtract reference part from list element, to facilitate further parsing
                uri_name = ref.replace(' ', '_')
                uri_name = urllib2.quote(uri_name).decode('utf-8', errors='ignore')
                entity = uri_name

        #no reference found; go ahead with the general mapping, which might be inaccurate
        #comment the below else case for more precise triples.
        else: 
            entity = entity.replace("{{","").replace("}}","").replace("\'\'","").strip().replace(" ","_")
            entity = urllib2.quote(entity).decode('utf-8', errors='ignore')

    return entity

def bracket_feature_mapper(elem):
    ''' Returns the entity (if any) which is found inside brackets in an element.

    :param elem: dictionary element entry.

    :return: an entity if there is a match, ``None`` otherwise.
    '''
    entity = None
    val = re.search('\(.*\)', elem, re.IGNORECASE)
    if val:
        val = val.group()
        entity = val.replace('(',"").replace(')',"").strip()
    return entity


##########################

'''

#########################
### UTILITY FUNCTIONS ###
#########################

Contains some of the helper modules that are required by the mapping functions.
'''


def lookup_call(keyword):
    ''' Calls DBpedia lookup service to get a corresponding URI from a keyword **[NOT USED ANYMORE]**

    :param keyword: the string to be reconciled with a URI.

    :return: service answer in JSON format.
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
        print ("Dbpedia Lookup error.")
        raise
    
    return parsed_ans


def wikidataAPI_call(res, lang):
    '''Calls Wikidata API service to get a corresponding URI from a string.

    :param res: string related to the URI we want to find.
    :param lang: language or endpoint in which we perform the search.

    :return: answer in json format.
    '''

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
        time.sleep(5)  #wait 5 seconds and then retry
        print("retrying Wikidata API call...")
        wikidataAPI_call(res, lang)
    
    except:
        print ("Wikidata API error on request " + req)
    
    else:
        return uri


def find_DBpedia_uri(wk_uri, lang):
    ''' Used to find an equivalent URI in DBpedia from a Wikidata one obtained by `Wikidata API`.

    :param wk_uri: URI found using the WikiData API.
    :param lang: resource/endpoint language.

    :return: DBpedia equivalent URI if found.
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
    
    return result


def list_elem_clean(list_elem):
    ''' Used to clean a list elements from forbidden or futile characters in a URI.

    :param list_elem: the list element to be cleaned.
    :return: cleaned element.
    '''
    list_elem = list_elem.lstrip()
    list_elem = list_elem.lstrip('\'')
    list_elem = list_elem.rstrip('\'')
    list_elem = list_elem.replace("{", "")
    list_elem = list_elem.replace("}", "")
    list_elem = list_elem.replace("[", "")
    list_elem = list_elem.replace("]", "")
    list_elem = list_elem.replace("“", "")
    list_elem = list_elem.replace("”", "")
    list_elem = list_elem.replace("«", "")
    list_elem = list_elem.replace("»", "")
    list_elem = list_elem.replace("《", "")
    list_elem = list_elem.replace("《", "")
    list_elem = list_elem.replace("\'\'", "")
    list_elem = list_elem.replace("\"", "")
    list_elem = list_elem.replace("#", "")
    list_elem = list_elem.lstrip()
    list_elem = list_elem.rstrip()
    
    return list_elem


'''
###########################
### Extractor Functions ###
###########################

### Below are the methods that extract list items from the JSON resource and form the resource dictionary
 
'''

def italic_mapper(list_elem):
    '''Extracts italic text inside the list element, mapped by ``''..''`` in Wikipedia.

    This is the first mapping to be applied since it's very precise. If this fails, more general mappings are applied.

    :param list_elem: current list element.
    
    :return: a match if found, ``None`` otherwise.
    '''
    
    # match_ref_italic = re.search(r'\'{2,}(.*?)\'{2,}', list_elem)
    match_italic = re.search(r'\'{2,}(.*?)\'{2,}', list_elem)
    if match_italic:
        match_italic = match_italic.group(0)
        match_italic = list_elem_clean(match_italic)
    
    return match_italic


def reference_mapper(list_elem):
    '''Looks for a reference inside the element, which has been marked with ``{{...}}`` by ``wikiParser``.
    It also ignores date references because they are non-relevant.
    
    :param list_elem: current list element.

    :return: a match if found, excluding number references.
    '''
    match_ref = re.search(r'\{\{.*?\}\}', list_elem)
    if match_ref:
        match_ref = match_ref.group()
        match_num = re.search(r'[0-9]{4}', match_ref)  # check if this reference is a date
        if match_num:  # date references must be ignored for this mapping
            num = match_num.group()
            new_ref = re.sub(r'\{\{.*\}\}', "", num, count=1)  # delete the number part
            match_ref = reference_mapper(new_ref)  #call again reference_mapper passing the new reference
    
    return match_ref


def general_mapper(list_elem):
    ''' Called when other text mappers fail, extract all text different from number until a \
    punctuation mark is found.

    Applies a regex to find the main concept and cuts off numbers and punctuation marks.
    
    :param list_elem: current list element.
    
    :return: a match if found.
    '''
    
    list_elem = list_elem_clean(list_elem)
    # look for strings cutting numbers and punctuation
    match_str = re.search(r"[^0-9][^,|:|：|–|(*|\[*|《*]+", list_elem, re.IGNORECASE)
    if match_str != None:
        match_str = match_str.group()
        match_str = list_elem_clean(match_str)
        match_str = match_str.lstrip('\'')
        match_str = match_str.lstrip('\'')
        match_str = match_str.rstrip('\'')
        match_str = match_str.lstrip(':')
        match_str = match_str.lstrip('-')
        match_str = match_str.lstrip('–')
        match_str = match_str.lstrip('(')
        match_str = match_str.lstrip(',')
    
    return match_str


def quote_mapper(list_elem):
    '''Looks for a quotation marks inside the element and returns the string inside quotes.
    It also ignores date references because they are non-relevant.

    :param list_elem: current list element.

    :return: a match if found, excluding number references.
    '''
    match_ref = re.search(r'\"(.*?)\"', list_elem)
    if match_ref:
        match_ref = match_ref.group(0)
        match_num = re.search(r'[0-9]{4}', match_ref)  # check if this reference is a date
        if match_num:  # date references must be ignored for this mapping
            num = match_num.group()
            new_ref = re.sub(r'\".*?\"', "", num, count=1)  # delete the number part
            match_ref = quote_mapper(new_ref)  #call again reference_mapper passing the new reference
    
    return match_ref
