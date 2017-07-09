#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
List-extractor - Extract Data from Wikipedia Lists
--------------------------------------------------

This program is used to create RDF triples from wikipedia lists so that they can be inserted into the
DBpedia dataset.

The program accepts three parameters: collect_mode, source and language. 
The first one is used to discriminate between the extraction of a single page or from all the pages 
related to a given class; the second one is the name of a single resource in the first case or a 
class in the latter. The last one is a two-letter language prefix used by DBpedia (currently only 
'it' and 'en' are accepted because the are mappings for italian and english.)
Depending on the collection mode chosen, it either passes the source as it is to wikiParser or 
collects first the list of resources from the given class to be passed from the endpoint.
wikiParser returns a dictionary representing the list information inside each resource, and optionally
you can save the dictionary inside a subdirectory named 'resources'. The dictionary is then passed to 
mapper module, which selects a mapping function depending on resource type and starts building the RDF 
graph, keeping trace of the number of list elements extracted. Finally, if the graph is not empty, it 
is serialized in a .ttl file inside a subdirectory named 'extracted'.


## How to run the tool

`python listExtractor.py collect_mode source language`

* `collect_mode` : `s` or `a`

    * use `s` to specify a single resource or `a` for a class of resources in the next parameter.

* `source`: a string representing a class of resources from DBpedia ontology 
    (right now it works for `Writer` and `Actor`), or a single Wikipedia page of an actor/writer.

* `language`: `en` or `it`

    * a two-letter prefix corresponding to the desired language of Wikipedia pages and SPARQL endpoint
     to be queried.

## Examples: 

* `python listExtractor.py a Writer it` 
* `python listExtractor.py s William_Gibson en`

"""

import sys
import argparse
import rdflib
import wikiParser
import utilities
import mapper


def main():
    """
    Entry point for list-extractor.
    Parses parameters and calls other modules in order to serialize a RDF graph.
    """
    
    # initialize argparse parameters
    parser = argparse.ArgumentParser(description='Extract data from lists in Wikipedia pages and serialize it in RDF.'
                                                 '\nExample: `python listExtractor.py a Writer en.`',
                                    formatter_class = argparse.RawTextHelpFormatter,
                                    usage="listExtractor.py [--help] collection_mode resource language "
                                    "\nUse listExtractor.py -h for more details.\n ")
    parser.add_argument('collect_mode',
                        help="'s' to specify a single Wikipedia page;\n'a' for all resources from a DBpedia class.\n ",
                        choices=['s', 'a'])
    parser.add_argument('source', type=lambda s: unicode(s, sys.getfilesystemencoding()),
                        help="Select resource to extract lists from. Options are:"
                            "\nSingle Wikipedia page (example: William_Gibson) "
                            "\nDBpedia ontology class (example: Writer)\n ")
    parser.add_argument('language', type=str, choices=['en', 'it', 'de', 'es'], default='en',
                        help="Language prefix of Wikipedia pages to analyze."
                            "\nen: English (Default)\nit: Italian\nde: German\nes: Spanish\n")
    parser.add_argument("-c", "--classname", type=str, help="Provide a classname from settings.json and use its"
                            "\nmapper functions")

    args = parser.parse_args()

    # initialize RDF graph which will contain the triples
    g = rdflib.Graph()
    g.bind("dbo", "http://dbpedia.org/ontology/")
    g.bind("dbr", "http://dbpedia.org/resource/")

    # start extracting lists from resources
    if args.collect_mode == 's':  # extract list information from a single resource
        try:
            resource = args.source.encode('utf-8')  # apply utf-8 encoding
            resDict = wikiParser.main_parser(args.language, resource)  # create a dict representing the resource
            
            for key in resDict:
                print key, ":", resDict[key]
                print ''
            
            ''' Decomment the line below to create a file inside a resources folder containing the dictionary'''
            utilities.createResFile(resDict, args.language, resource)
            
            # Asks the endpoint for a list of types/classes associated to the resource
            if args.classname == None:
                rdf_type = utilities.get_resource_type(args.language, resource)
            else:
                rdf_type = [classes.strip() for classes in args.classname.split(',')]
            #print rdf_type
        
        except:
            print("Could not find specified resource: " + args.source)
            sys.exit(0)

        list_elems = 0  # Used to keep trace of the number of list elements extracted
        for t in rdf_type:  # for each type found, look for a suitable mapping and apply it
            list_elems += mapper.select_mapping(resDict, resource, args.language, t,
                                                g)  # get number of elements extracted
            #print '>>>>>', t, list_elems
        tot_list_elems = utilities.count_listelem_dict(resDict)  # count all list elements of the resource
        print("Total elements extracted: " + str(list_elems) + "/" + str(tot_list_elems))

    elif args.collect_mode == 'a':  # extract lists from a class of resources from DBpedia ontology (e.g. 'Writer')
        if utilities.check_existing_class(args.source) == True:
            try:
                resources = utilities.get_resources(args.language, args.source)
                res_num = len(resources)  # total number of resources
                curr_num = 1  # current resource to be analyzed
            except:
                print("Could not find specified class of resources: " + args.source)
                sys.exit(0)
        else: 
            print '\nThis domain has not been mapped yet!'
            print 'You can add a mapping for this domain using rulesGenerator.py and try again...'
            sys.exit(0)
        
        tot_extracted_elems = 0  # Used to keep track of the number of list elements extracted
        tot_elems = 0 # Used to keep track of total number of list elements
        total_res_failed = 0
        for res in resources:
            try:
                print(res + " (" + str(curr_num) + " of " + str(res_num) + ")")
                resDict = wikiParser.main_parser(args.language, res)  # create a dict representing each resource
                tot_elems += utilities.count_listelem_dict(resDict)
                
                '''Decomment the line below to create a file inside a resources folder containing the dictionary'''
                # utilities.createResFile(resDict, args.language, res)
            
            except:
                print("Could not parse " + args.language + ":" + res)
                total_res_failed +=1
                curr_num+=1
            
            else:
                curr_num += 1
                print(">>> " + args.language + ":" + res + " has been successfully parsed <<<")
                extr_elems = mapper.select_mapping(resDict, res, args.language, args.source, g)
                mapper.mapped_domains = []  # reset domains already mapped for next resource
                tot_extracted_elems += extr_elems
                print(">>> Mapped " + args.language + ":" + res + ", extracted elements: " + str(extr_elems) + "  <<<\n")
        
        utilities.evaluate(args.language, args.source, res_num, res_num - total_res_failed,
                             tot_extracted_elems, tot_elems, len(g))

    # If the graph contains at least one statement, create a .ttl file with the RDF triples created
    g_length = len(g)
    if g_length > 0:
        file_name = "ListExtractor_" + args.source + "_" + args.language + "_" + utilities.getDate() + ".ttl"
        file_path = utilities.get_subdirectory('extracted', file_name)
        g.serialize(file_path, format="turtle")
        print(str(g_length) + " statements created. Triples serialized in: " + file_path)
    else:
        print("Could not serialize any RDF statement! :(")


if __name__ == "__main__":
    main()
