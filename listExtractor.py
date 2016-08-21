# -*- coding: utf-8 -*-
__author__ = 'feddie - Federica Baiocchi - feddiebai@gmail.com'

import sys
import argparse
import rdflib
import wikiParser
import utilities
import mapper


def main():
    """Entry point for list-extractor, parses parameters and calls other modules in order to serialize a RDF graph.

    The program accepts three parameters: collect_mode, source and language. The first one is used to discriminate
    between the extraction of a single page or from all the pages related to a given class; the second one is the name
    of a single resource in the first case or a class in the latter. The last one is a two-letter language prefix used
    by DBpedia (currently only 'it' and 'en' are accepted because the are mappings for italian and english.)
    Depending on the collection mode chosen, it either passes the source as it is to wikiParser or collects first the
    list of resources from the given class to be passed from the endpoint.
    wikiParser returns a dictionary representing the list information inside each resource, and optionally you can save
    the dictionary inside a subdirectory named 'resources'.
    The dictionary is then passed to mapper module, which selects a mapping function depending on resource type and
    starts building the RDF graph, keeping trace of the number of list elements extracted.
    Finally, if the graph is not empty, it is serialized in a .ttl file inside a subdirectory named 'extracted'.
    """
    # initialize parameters
    parser = argparse.ArgumentParser(description='Extract data from lists in Wikipedia pages and serialize it in RDF. '
                                                 'Example: -a Writer en.')
    parser.add_argument('collect_mode',
                        help="Use 's' to specify a single Wikipedia page; 'a' for all resources from a DBpedia class.",
                        choices=['s', 'a'])
    parser.add_argument('source', type=lambda s: unicode(s, sys.getfilesystemencoding()),
                        help="Single Wikipedia page (example: William_Gibson) or DBpedia ontology class (example: Writer)")
    parser.add_argument('language', type=str, choices=['en', 'it'],
                        help="Language prefix of Wikipedia pages to analyze.")
    args = parser.parse_args()

    # initialize RDF graph which will contain the triples
    g = rdflib.Graph()
    g.bind("dbo", "http://dbpedia.org/ontology/")
    g.bind("dbr", "http://dbpedia.org/resource/")

    if args.collect_mode == 's':  # extract list information from a single resource
        try:
            resource = args.source.encode('utf-8')  # apply utf-8 encoding
            resDict = wikiParser.main_parser(args.language, resource)  # create a dictionary representing the resource
            print (resDict)
            ''' Decomment the line below to create a file inside a resources folder containing the dictionary'''
            utilities.createResFile(resDict, args.language, resource)
            # Asks the endpoint for a list of types/classes associated to the resource
            rdf_type = utilities.get_resource_type(args.language, resource)
        except:
            print("Could not find specified resource: " + args.source)
            sys.exit(0)
        list_elems = 0  # Used to keep trace of the number of list elements extracted
        for t in rdf_type:  # for each type found, look for a suitable mapping and apply it
            list_elems += mapper.select_mapping(resDict, resource, args.language, t,
                                                g)  # get number of elements extracted
        tot_list_elems = utilities.count_listelem_dict(resDict)  # count all list elements of the resource
        print("Total elements extracted: " + str(list_elems) + "/" + str(tot_list_elems))

    elif args.collect_mode == 'a':  # extract lists from a class of resources from DBpedia ontology (e.g. 'Writer','Actor',..)
        try:
            resources = utilities.get_resources(args.language, args.source)
            res_num = len(resources)  # total number of resources
            curr_num = 1  # current resource to be analyzed
        except:
            print("Could not find specified class of resources: " + args.source)
            parser.print_help()
            sys.exit(0)
        tot_elems = 0  # Used to keep trace of the number of list elements extracted
        for res in resources:
            try:
                print(res + " (" + str(curr_num) + " of " + str(res_num) + ")")
                resDict = wikiParser.main_parser(args.language, res)  ##
                curr_num += 1
                '''Decomment the line below to create a file inside a resources folder containing the dictionary'''
                # utilities.createResFile(resDict, args.language, res)
            except:
                print("Could not parse " + args.language + ":" + res)
            else:
                print(">>> " + args.language + ":" + res + "  has been successfully parsed <<<")
                extr_elems = mapper.select_mapping(resDict, res, args.language, args.source, g)
                mapper.mapped_domains = []  # reset domains already mapped for next resource
                tot_elems += extr_elems
                print(">>> Mapped " + args.language + ":" + res + ", extracted elements: " + str(extr_elems) + "  <<<")
        print ("Total elements extracted: " + str(tot_elems))

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
