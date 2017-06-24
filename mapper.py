# -*- coding: utf-8 -*-

'''
#################
### mapper.py ###
#################

* This module contains all the methods/functions that use dictionaries from `mapping_rules.py`
  and produce respective triplets.

* This module contains all the mapping functions that are used by the extractor based on rules present
  in mapping_rules.py


'''

import urllib2
import json
import re
import rdflib
import utilities
import time
from mapping_rules import *

dbo = rdflib.Namespace("http://dbpedia.org/ontology/")
dbr = rdflib.Namespace("http://dbpedia.org/resource/")
rdf = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

mapped_domains = []  # used to prevent duplicate mappings
resource_class = ""

def select_mapping(resDict, res, lang, res_class, g):
    ''' Calls mapping functions for each matching section of the resource, thus constructing the associated RDF graph.

    Firstly selects the mapping type(s) to apply from MAPPING (in mapping_rules.py) based on resource class (domain).
    If a match is found, it tries to find another match between section names and key-words related to that domain.
    Finally, it applies related mapping functions for the list elements contained in that section.
    :param resDict: dictionary representing current resource
    :param res: current resource name
    :param res_class: resource class/type (e.g. Writer)
    :param lang: resource language
    :param g: RDF graph to be created
    :return number of list elements actually mapped in th graph
    '''
    global mapped_domains
    global resource_class
    res_elems = 0

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
            if lang in eval(domain):
                domain_keys = eval(domain)[lang]  # e.g. ['bibliography', 'works', ..]
            else:
                print("The language provided is not available yet for this mapping")
                #return 0

            mapped_domains.append(domain)  #this domain won't be used again for mapping
    
            for res_key in resDict.keys():  # iterate on resource dictionary keys
                mapped = False
        
                for dk in domain_keys:  # search for resource keys related to the selected domain
                    # if the section hasn't been mapped yet and the title match, apply domain related mapping
                    dk = dk.decode('utf-8') #make sure utf-8 mismatches don't skip sections 
                    if not mapped and re.search(dk, res_key, re.IGNORECASE):
                        mapper = "map_" + domain.lower() + "(resDict[res_key], res_key, db_res, lang, g, 0)"
                        res_elems += eval(mapper)  # calls the proper mapping for that domain and counts extracted elements
                        mapped = True  # prevents the same section to be mapped again

    else:
        return 0

    return res_elems


def map_discography(elem_list, sect_name, res, lang, g, elems):
    ''' Handles albums list present inside a section containing a match with DISCOGRAPHY.

    Adds RDF statement about the album, its artist (the current resource) and the year launched.
    
    :param elem_list: list of elements to be mapped
    :param sect_name: section name
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
   
    :return number of list elements extracted
    '''

    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_discography(elem, sect_name, res, lang, g, elems)   # handle recursive lists
        
        else:
            year = month_year_mapper(elem)
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
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), rdf.type, dbo.Album))
                g.add((rdflib.URIRef(uri), dbo.musicalArtist, res))
                elems += 1
                if year:
                    add_years_to_graph(g, uri, year)

    return elems


def map_concert_tours(elem_list, sect_name, res, lang, g, elems):
    ''' Handles albums list present inside a section containing a match with CONCERT_TOURS.

    Adds RDF statement about the tour, its artist (the current resource) and the year launched.
    
    :param elem_list: list of elements to be mapped
    :param sect_name: section name
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
   
    :return number of list elements extracted
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
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), rdf.type, dbo.concertTour))
                g.add((rdflib.URIRef(uri), dbo.musicalArtist, res))
                elems += 1
                if year:
                    add_years_to_graph(g, uri, year)

    return elems


def map_alumni(elem_list, sect_name, res, lang, g, elems):
    ''' Handles albums list present inside a section containing a match with ALUMNI.

    Adds RDF statement about the person and its assosiation with the resource(organisation).
    
    :param elem_list: list of elements to be mapped
    :param sect_name: section name
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
   
    :return number of list elements extracted
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
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.alumni, res))
                elems += 1
                work = alumni_profession_mapper(elem)
                if work:
                    g.add((rdflib.URIRef(uri), dbo.notableWork, rdflib.Literal(work, datatype=rdflib.XSD.string)))
    return elems


def map_programs_offered(elem_list, sect_name, res, lang, g, elems):
    ''' Handles list present inside a section containing a match with PROGRAMS_OFFERED.

    Adds RDF statement about the program offered by the resource(organisation).
    
    :param elem_list: list of elements to be mapped
    :param sect_name: section name
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
   
    :return number of list elements extracted
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
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.academicDiscipline, res))
                elems+=1
            
    return elems


def map_honors(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to awards and honors given to people inside a section containing a match with HONORS.

    Adds RDF statements about the awards, and its details(if present) and the recipient.
    :param elem_list: list of elements to be mapped
    :param sect_name: section name, used to reconcile literary genre
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
    :return number of list elements extracted
    '''
    
    award_status = award_status_mapper(sect_name, lang)  # if award status is found in the section name.
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_honors(elem, sect_name, res, lang, g, elems)
        
        else:
            uri = None
            if award_status == None: award_status = award_status_mapper(elem, lang)
            if award_status == None: award_status = "Winner" #if no information is found, assume winner.

            elem = elem.encode('utf-8')  # apply utf-8 encoding
            elem = elem.replace("Winner","").replace("Won","").replace("Nominated","").replace("Nominee","")
            for_entity = sentence_splitter(elem,"for",lang)
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
                    uri_name = urllib2.quote(uri_name)  ###
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')
            else:
                uri_name = quote_mapper(elem)  #try finding awards in quotes
                if uri_name == None: uri_name = general_mapper(elem)  # no reference found, try general mapping (less accurate
                if (uri_name and uri_name != "" and uri_name != res):
                    uri_name = uri_name.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name)  ###
                    uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
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
    ''' Handles list present inside a section containing a match with STAFF.

    Adds RDF statement about the staff member and the institution.
    
    :param elem_list: list of elements to be mapped
    :param sect_name: section name
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
   
    :return number of list elements extracted
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
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
            if uri and uri != "":
                if len(list(g.triples((rdflib.URIRef(uri), dbo.alumni, res)))) == 0 and \
                    len(list(g.triples((rdflib.URIRef(uri), dbo.academicDiscipline, res)))) ==0: # if already mapped
                    g.add((rdflib.URIRef(uri), dbo.staff, res))
    
    return elems


def map_other_person_details(elem_list, sect_name, res, lang, g, elems):
    ''' Handles list present inside a section containing a match with OTHER.

    Adds RDF statement about the unclassified sections in Person domain.
    
    :param elem_list: list of elements to be mapped
    :param sect_name: section name
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
   
    :return number of list elements extracted
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
                res_name = urllib2.quote(res_name)  ###
                uri = dbr + res_name.decode('utf-8', errors='ignore')
            
            else:
                uri_name = quote_mapper(elem)
                if (uri_name and uri_name != "" and uri_name != res):
                    uri_name = uri_name.replace(' ', '_')
                    uri_name = urllib2.quote(uri_name)  ###
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

            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo[p], res))
                elems+=1

    return elems


def map_career(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to awards and honors given to people inside a section containing a match with HONORS.

    Adds RDF statements about the awards, and its details(if present) and the recipient.
    :param elem_list: list of elements to be mapped
    :param sect_name: section name, used to reconcile literary genre
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
    :return number of list elements extracted
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
            
            p = PERSON_DETAILS[lang][other_details]
            
            uri_name = quote_mapper(elem)
            if uri_name == None or uri_name == res: uri_name = general_mapper(elem)
            if (uri_name and uri_name != "" and uri_name != res):
                uri_name = uri_name.replace(' ', '_')
                uri_name = urllib2.quote(uri_name)  ###
                uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo[p], res))
                elems += 1
                if year:
                    add_years_to_graph(g,uri, year)                
    return elems


def map_filmography(elem_list, sect_name, res, lang, g, elems):
    '''Handles lists related to filmography inside a section containing a match with FILMOGRAPHY.

    It constructs RDF statements about the movie title, it release year and type (Film, TV show, Cartoon..)
    and which part the current resource took in it (director, actor, ...)
    :param elem_list: list of elements to be mapped
    :param sect_name: section name, used to reconcile literary genre
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
    :return number of list elements extracted
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
            
            if uri and uri != "":
                g.add((rdflib.URIRef(uri), rdf.type, dbo + rdflib.URIRef(filmography_type)))
                if year:
                    add_years_to_graph(g, uri, year)
                if film_particip:
                    g.add((rdflib.URIRef(uri), dbo + rdflib.URIRef(film_particip), res))
                elems += 1
    
    return elems


def map_bibliography(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to bibliography inside a section containing a match with BIBLIOGRAPHY.

    Adds RDF statement about the work title, its author (the current resource), publication year and isbn code.
    :param elem_list: list of elements to be mapped
    :param sect_name: section name, used to reconcile literary genre
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
    :return number of list elements extracted
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
                        elem = elem.replace(ref,"")  #subtract reference part from list element, to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:
                    uri_name = quote_mapper(elem)  #try finding awards in quotes
                    if uri_name == None or uri_name == res: uri_name = general_mapper(elem)  # no reference found, try general mapping (less accurate
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
            
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
    ''' Handles lists related to members inside a section containing a match with BAND_MEMBERS.

    Adds RDF statement about the band, its members
    :param elem_list: list of elements to be mapped
    :param sect_name: section name 
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
    :return number of list elements extracted
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
                        elem = elem.replace(ref,"")  #subtract reference part from list element to facilitate further parsing
                        uri_name = ref.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                
                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            if uri and uri != "":
                g.add((rdflib.URIRef(uri), dbo.bandMember, res))
                elems += 1
                
    return elems


def map_contributors(elem_list, sect_name, res, lang, g, elems):
    ''' Handles lists related to contributions made by person inside a section containing a 
        match with CONTRIBUTORS.

    Adds RDF statement about the band, its members
    :param elem_list: list of elements to be mapped
    :param sect_name: section name 
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
    :return number of list elements extracted
    '''
    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_contributors(elem, sect_name, res, lang, g, elems)

        else:
            contrib_type, subsection = None, None
            search_str = sect_name
            try: subsection = sect_name.split('-')[1].strip()
            except: pass
            
            for t in CONTRIBUTION_TYPE[lang].keys():
                if subsection: search_str = subsection
                if re.search(t, search_str, flags=re.IGNORECASE):
                    contrib_type = CONTRIBUTION_TYPE[lang][t]
                    break

            if contrib_type == None:
                feature = bracket_feature_mapper(elem)
                for t in CONTRIBUTION_TYPE[lang]:
                    try:
                        if re.search(t, feature, re.IGNORECASE):
                            contrib_type = CONTRIBUTION_TYPE[lang][t]
                            break
                    except: continue

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
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

                else:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

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
    ''' Handles lists related to literature details inside a section containing a 
        match with OTHER_LITERATURE_DETAILS.

    Adds RDF statement about the band, its members
    :param elem_list: list of elements to be mapped
    :param sect_name: section name 
    :param res: current resource
    :param lang: resource language
    :param g: RDF graph to be constructed
    :param elems: a counter to keep track of the number of list elements extracted
    :return number of list elements extracted
    '''
    for c in CONTRIBUTORS[lang]:
        if re.search(c, sect_name, re.I):   #Already mapped
            return 0

    for elem in elem_list:
        if type(elem) == list:  # for nested lists (recursively call this function)
            elems += 1
            map_other_literature_details(elem, sect_name, res, lang, g, elems)

        else:
            detail_type = None
            for t in OTHER_LITERATURE_DETAILS[lang].keys():
                if re.search(t, sect_name, flags=re.IGNORECASE):
                    detail_type = OTHER_LITERATURE_DETAILS[lang][t]
                    break

            if detail_type == None:
                feature = bracket_feature_mapper(elem)
                for t in OTHER_LITERATURE_DETAILS[lang]:
                    if re.search(t, feature, re.IGNORECASE):
                        detail_type = OTHER_LITERATURE_DETAILS[lang][t]
                        break

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
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

                elif (ref is not None):  # no reference found, try general mapping (less accurate)
                    uri_name = quote_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')
                        map_failed = False

                if map_failed:  # no reference found, try general mapping (less accurate)
                    uri_name = general_mapper(elem)
                    if (uri_name and uri_name != "" and uri_name != res):
                        uri_name = uri_name.replace(' ', '_')
                        uri_name = urllib2.quote(uri_name)  ###
                        uri = dbr + uri_name.decode('utf-8', errors='ignore')

            if uri and uri != "":
                if detail_type:
                    g.add((rdflib.URIRef(uri), dbo[detail_type], res))
                else:
                    g.add((rdflib.URIRef(uri), dbo.other, res))
                if year:
                    add_years_to_graph(g, uri, year)

                elems += 1
                
    return elems



def add_years_to_graph(g, uri, year):
    '''Adds all the years related to the uri to the graph g. Does not return anything; appends existing graph

    :param g: current graph
    :param uri: resource related to the years list.
    :param year: contains a list of years that need to be mapped.
    '''
    for y in year:
        if type(y) != list:
            if "^" in y:
                d = y.replace("^","-")
                g.add((rdflib.URIRef(uri), dbo.activeYear, rdflib.Literal(d, datatype=rdflib.XSD.gYearMonth)))

            else:    
                g.add((rdflib.URIRef(uri), dbo.activeYear, rdflib.Literal(y, datatype=rdflib.XSD.gYear)))
        else:
            start_period, end_period = y[0], y[1]
            if "^" in y[0]:
                d = y[0].replace("^","-")
                g.add((rdflib.URIRef(uri), dbo.activeYearsStartDate, rdflib.Literal(d, datatype=rdflib.XSD.gYearMonth)))
            else:    
                g.add((rdflib.URIRef(uri), dbo.activeYearsStartDate, rdflib.Literal(y[0], datatype=rdflib.XSD.gYear)))

            if "^" in y[1]:
                d = y[1].replace("^","-")
                g.add((rdflib.URIRef(uri), dbo.activeYearsEndDate, rdflib.Literal(d, datatype=rdflib.XSD.gYearMonth)))

            else:    
                g.add((rdflib.URIRef(uri), dbo.activeYearsEndDate, rdflib.Literal(y[1], datatype=rdflib.XSD.gYear)))

    return

def alumni_profession_mapper(list_elem):
    '''Applies a regex to look for a profession, returns a match if found

    Profession is expected to present after the resource name, seperated by either a hyphen or comma
    :param list_elem: current list element
    :return: a match for profession, if present
    '''
    profession = re.search(r'[^-|,]+$', list_elem)
    if profession != None:
        profession = profession.group()
        profession = profession.replace("{{", "").replace("}}","")
        if profession[0] == " ": profession = profession[1:]
    
    return profession

def isbn_mapper(list_elem):
    '''Applies a regex to look for a isbn number, returns a match if found

    ISBN or International Standard Book Number consists of 4 parts and 10 digits (if assigned before 2007)
    where the last character may equal to the letter "X", or 5 parts and 13 digits , possibly separated by hyphens
    :param list_elem: current list element
    :return: a match for a isbn code, if present
    '''
    match_isbn = re.search(r'ISBN ([0-9]|-)*X?', list_elem)
    if match_isbn != None:
        match_isbn = match_isbn.group()
        match_isbn = match_isbn.replace('ISBN ', "")
    
    return match_isbn

def year_mapper(list_elem):
    '''Looks for a set of exactly 4 digits which would likely represent the year of publication of a work

    :param list_elem: current list element
    :return: a numeric match if found
    '''
    # select an occurance of a 4 digit number as the (publication) year
    # match_num = re.search(r'[0-9]{4}', list_elem)
    # if match_num != None:
    #     match_num = match_num.group()

    match_num = re.findall(r'[0-9]{4}', list_elem)
    if len(match_num) == 0: return None
    return match_num

def month_year_mapper(list_elem):
    '''Looks for any kind of date formats; years, month+year or actual date and returns list of dates

    :param list_elem: current list element
    :return: a numeric match if found
    '''
    month_list = { r'(january\s?)\d{4}':'1^', r'\W(jan\s?)\d{4}':'1^', r'(february\s?)\d{4}':'2^', r'\W(feb\s?)\d{4}':'2^',
                    r'(march\s?)\d{4}':'3^', r'\W(mar\s?)\d{4}':'3^',r'(april\s?)\d{4}':'4^',r'\W(apr\s?)\d{4}':'4^', 
                    r'(may\s?)\d{4}':'5^', r'\W(may\s?)\d{4}':'5^',r'(june\s?)\d{4}':'6^',r'\W(jun\s?)\d{4}':'6^',
                    r'(july\s?)\d{4}':'7^',r'\W(jul\s?)\d{4}':'7^', r'(august\s?)\d{4}':'8^', r'\W(aug\s?)\d{4}':'8^', 
                    r'(september\s?)\d{4}':'9^', r'\W(sep\s?)\d{4}':'9^',r'\W(sept\s?)\d{4}':'9^', r'(october\s?)\d{4}':'10^',
                    r'\W(oct\s?)\d{4}':'10^',r'(november\s?)\d{4}':'11^', r'\W(nov\s?)\d{4}':'11^' ,
                    r'(december\s?)\d{4}':'12^', r'\W(dec\s?)\d{4}':'12^'}
    
    month_present = False
    period_dates = False

    for mon in month_list:
        if re.search(mon, list_elem, re.IGNORECASE):
            rep = re.search(mon, list_elem, re.IGNORECASE).group(1)
            list_elem = re.sub(rep, month_list[mon], list_elem, flags=re.I)
            month_present = True

    period_regex = ur'(?:\(?\d{1,2}\^)?\s?\d{4}\s?(?:–|-)\s?(?:\d{1,2}\^)?\s?\d{4}(?:\))?'  #regex for checking if its a single year or period

    if re.search(period_regex, list_elem, flags=re.IGNORECASE):
        period_dates = True

    if month_present == False and period_dates == False:
        return year_mapper(list_elem)
    
    years = []

    if month_present == False and period_dates == True:
        match_num =  re.findall(period_regex, list_elem, flags=re.IGNORECASE)
        if len(match_num) == 0: return year_mapper(list_elem)
        
        for y in match_num:
            year = re.split(ur'\s?[–-]\s?', y)
            years.append([year[0], year[1]])
        
        for x in match_num:
            list_elem = list_elem.replace(x,"")

        single_years = year_mapper(list_elem)   
        if single_years != None: years.extend(single_years)
        return years
        
    if month_present == True and period_dates == False:
        match_num = re.findall(r'[0-9]{1,2}\^\s?[0-9]{4}', list_elem)
        for x in match_num:
            list_elem = list_elem.replace(x,"")
            x = x.replace(" ","")
            z = "^".join(x.split('^')[::-1])
            years.append(z)

        single_years = year_mapper(list_elem)
        if single_years != None: years.extend(single_years)
        return years

    else:
        match_num = re.findall(period_regex, list_elem, flags=re.IGNORECASE)
        if len(match_num) == 0: return year_mapper(list_elem)

        for y in match_num:
            year = re.split(r'\s?(–|-)\s?', y)
            list_elem = list_elem.replace(y,"")
            years.append(["^".join(year[0].replace(" ","").split("^")[::-1]), "^".join(year[2].replace(" ","").split("^")[::-1])])

        single_years = year_mapper(list_elem)
        if single_years != None: years.extend(single_years)
        return years

def litgenre_mapper(sect_name, lang):
    '''Tries to match the section name with a literary genre provided in BIBLIO_GENRE dictionary.

    if a genre is found, it also checks for multiple matches and ignores them
    (some sections may be called 'Novels and short stories', therefore it's impossible to know if each list element
    is actually a novel or a short story).
    :param sect_name: wikipedia section name, to reconcile
    :param language: resource/endpoint language
    :return: a literary genre if there is a match, None otherwise
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
    ''' Returns the part the person took in that movie as a property (e.g. starring, director, etc...)

    In order to do so, confronts section titles with FILMOGRAPHY_PARTICIPATION. Default value is 'starring'
    :param sect_name: section and sub-section name to compare with a regex
    :return: a property if there is a match, None otherwise
    '''
    film_particip = 'starring'  #default property for Actors is 'starring'
    f_parts = FILMOGRAPHY_PARTICIPATION[lang]
    for fp in f_parts.keys():
        if re.search(fp, sect_name, re.IGNORECASE):
            film_particip = f_parts[fp]
    
    return film_particip

def filmtype_mapper(sect_name, lang):
    ''' Returns the type of Filmography elements in current list as a class (TelevisionShow, Cartoon, etc...)

    In order to do so, confronts section titles with FILMOGRAPHY_TYPE. Default value is Movie.
    :param sect_name: section and sub-section name to compare with a regex
    :param lang: page language
    :return: a class if there is a match, None otherwise
    '''
    filmtype = 'Film'  # default type for Filmography elements is 'Film'
    f_types = FILMOGRAPHY_TYPE[lang]
    for ft in f_types.keys():
        if re.search(ft, sect_name, re.IGNORECASE):
            filmtype = f_types[ft]
    
    return filmtype

def award_status_mapper(sect_name, lang):
    ''' Returns the status of the award to the recipient; default is Winnig, i.e. Awarded

    :param sect_name: section and sub-section name to compare with a regex
    :param lang: page language
    :return: a class if there is a match, None otherwise
    '''
    status = None
    s_types = AWARD_STATUS_TYPE[lang]
    for st in s_types.keys():
        if re.search(st, sect_name, re.IGNORECASE):
            status = s_types[st]
    
    return status

def sentence_splitter(elem,word,lang):
    ''' Returns the entity (if any) for which the award is awarded to the recipient

    :param elem: dictionary element entry
    :param lang: page language
    :return: an entity if there is a match, None otherwise
    '''
    entity = None
    term = TRANSLATIONS[word][lang]
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

        else:
            entity = entity.replace("{{","").replace("}}","").replace("\'\'","").strip().replace(" ","_")
            entity = urllib2.quote(entity).decode('utf-8', errors='ignore')


    return entity

def bracket_feature_mapper(elem):
    ''' Returns the entity (if any) which is found inside brackets in an element

    :param elem: dictionary element entry
    :param lang: page language
    :return: an entity if there is a match, None otherwise
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
    ''' Calls DBpedia lookup service to get a corresponding URI from a keyword [NOT USED ANYMORE]

    :param keyword: the string to be reconciled with a URI
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
        print ("Dbpedia Lookup error.")
        raise
    
    return parsed_ans


def wikidataAPI_call(res, lang):
    '''Calls Wikidata API service to get a corresponding URI from a string

    :param res: string related to the URI we want to find
    :param lang: language or endpoint in which we perform the search
    :return: answer in json format
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
    ''' Used to find an equivalent URI in DBpedia from a Wikidata one obtained by Wikidata API

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
    
    return result


def list_elem_clean(list_elem):
    ''' Used to clean a list elements from forbidden or futile characters in a URI

    :param list_elem: the list element to be cleaned
    :return: cleaned element
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


### Below are the methods that extract list items from the JSON resource and form the resource dictionary
 
def italic_mapper(list_elem):
    '''Extracts italic text inside the list element, mapped by ''..'' in Wikipedia.

    This is the first mapping to be applied since it's very precise.
    If this fails, more geneal mappings are applied.
    :param list_elem: current list element
    :return: a match if found, None object otherwise
    '''
    # match_ref_italic = re.search(r'\'{2,}(.*?)\'{2,}', list_elem)
    match_italic = re.search(r'\'{2,}(.*?)\'{2,}', list_elem)
    if match_italic:
        match_italic = match_italic.group(0)
        match_italic = list_elem_clean(match_italic)
    
    return match_italic


def reference_mapper(list_elem):
    '''Looks for a reference inside the element, which has been marked with {{...}} by wikiParser,

    It also ignores date references because they are non-relevant
    :param list_elem: current list element
    :return: a match if found, excluding number references
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
    ''' Called when other text mappers fail, extract all text different from number until a punctuation mark is found

    Applies a regex to find the main concept and cuts off numbers and punctuation marks
    :param list_elem: current list element
    :return: a match if found
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
    '''Looks for a quotation marks inside the element and returns

    It also ignores date references because they are non-relevant
    :param list_elem: current list element
    :return: a match if found, excluding number references
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



