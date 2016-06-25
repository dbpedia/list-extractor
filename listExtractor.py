# coding: utf-8
__author__ = 'feddie - Federica Baiocchi - feddiebai@gmail.com'

import sys
import argparse
import rdflib
import wikiParser
import utilities
import mapper

parser = argparse.ArgumentParser(description='Extract data from lists in Wikipedia pages and serialize it in RDF')
parser.add_argument('res_type', type=str,
                    help="DBpedia ontology concept you are looking for. Example: Writer")
parser.add_argument('language', type=str, choices=['en', 'it'],
                    help="Language of Wikipedia pages/resources to analyze")
args = parser.parse_args()

g = rdflib.Graph()
g.bind("dbo", "http://dbpedia.org/ontology/")
g.bind("dbr", "http://dbpedia.org/resource/")

try:
    resources = utilities.get_resources(args.language, args.res_type)
    # resources = ['Charles_Marie_René_Leconte_de_Lisle'] #use this line to specify each resource
except:
    print("Could not retrieve specified resources")
    sys.exit(0)

for res in resources:
    try:
        resDict = wikiParser.mainParser(args.language, res)
        print(res + " -> " + str(resDict))
        # Decomment the line below to create a file inside a resources folder containing the dictionary
        # utilities.createResFile(resDict, language, resource)
    except:
        print("--- Could not parse : " + args.language + ":" + res + " ---")
    else:
        print(">>> " + args.language + ":" + res + "  has been successfully parsed <<<")
        mapper.select_mapping(resDict, res, g, args.language)
        print(">>> " + args.language + ":" + res + "  has been mapped <<<")

file_name = "ListExtractor_" + args.language + "_" + utilities.getDate() + ".ttl"
g.serialize(file_name, format="turtle")
print("Triples serialized in file: " + file_name)
