# -*- coding: utf-8 -*-
__author__ = 'feddie - Federica Baiocchi - finalfed@hotmail.it'

import sys
import argparse
import rdflib
import wikiParser
import utilities
import mapper

# initialize script parameters
parser = argparse.ArgumentParser(description='Extract data from lists in Wikipedia pages and serialize it in RDF')
group = parser.add_mutually_exclusive_group()
group.add_argument('-s', '--single', help="To specify a single Wikipedia resource to parse.", action="store_true")
group.add_argument('-a', '--all', help="To parse all resources from the given DBpedia ontology concept.",
                   action="store_true")
parser.add_argument('res_type', type=lambda s: unicode(s, sys.getfilesystemencoding()),
                    help="if using -s (single resource) example: William_Gibson |"
                         "\nwith -a (all resources) example: Writer")

parser.add_argument('language', type=str, choices=['en', 'it'], help="Language of Wikipedia pages/resources to analyze")
args = parser.parse_args()


#initialize RDF graph which will contain the triples
g = rdflib.Graph()
g.bind("dbo", "http://dbpedia.org/ontology/")
g.bind("dbr", "http://dbpedia.org/resource/")

if args.single:  #extract lists from single resource
    try:
        resource = args.res_type.encode('utf-8')
        resDict = wikiParser.main_parser(args.language, resource)
        print (resDict)

    except:
        print("Could not retrieve specified resource: " + args.res_type)
        sys.exit(0)

    mapper.select_mapping(resDict, resource, args.language, 'Writer', g)

elif args.all:  # extract lists from a class of resources (it works with Writer)
    try:
        resources = utilities.get_resources(args.language, args.res_type)
        res_num = len(resources)  # total number of resources
        curr_num = 1  # current resource to be analyzed
    except:
        print("Could not retrieve specified class of resources: " + args.res_type)
        parser.print_help()
        sys.exit(0)

    tot_nodes = 0
    for res in resources:
        try:
            print(res + " (" + str(curr_num) + " of " + str(res_num) + ")")
            resDict = wikiParser.main_parser(args.language, res)  ##
            curr_num += 1
        # Decomment the line below to create a file inside a resources folder containing the dictionary
        # utilities.createResFile(resDict, language, resource)
        except:
            err = str(sys.exc_info()[0])
            print("Could not parse " + args.language + ":" + res + "  -  Error " + err)
        else:
            print(">>> " + args.language + ":" + res + "  has been successfully parsed <<<")
            tot_nodes += mapper.select_mapping(resDict, res, args.language, args.res_type, g)
            print(">>> " + args.language + ":" + res + "  has been mapped <<<")
    print ("Total nodes extracted: " + str(tot_nodes))

# If the graph contains at least one statement, create a .ttl file with the RDF triples created
if len(g) > 0:
    file_name = "ListExtractor_" + args.res_type + "_" + args.language + "_" + utilities.getDate() + ".ttl"
    g.serialize(file_name, format="turtle")
    print("Triples serialized in file: " + file_name)
else:
    print("Could not serialize any RDF statement! :(")
