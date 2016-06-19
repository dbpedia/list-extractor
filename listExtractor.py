# coding: utf-8

__author__ = 'feddie - Federica Baiocchi - feddiebai@gmail.com'

import wikiParser
import utilities
import mapper
import rdflib

# language = 'en'
language = 'it'

# resource = 'August_von_Platen-Hallermünde'
# resource = 'J._K._Rowling'
# resource = 'Publio_Virgilio_Marone'
# resource = 'George_R._R._Martin'
#resource = 'William_Gibson'

g = rdflib.Graph()
g.bind("dbo", "http://dbpedia.org/ontology/")
g.bind("dbr", "http://dbpedia.org/resource/")

# decomment to read all writer resources
resources = utilities.get_resources(language)
# resources = ['William_Gibson'] #specify each resource

for res in resources:
    try:
        resDict = wikiParser.mainParser(language, res)
        print(resDict)
        # Decomment the line below to create a file inside a resources folder containing the dictionary
        # utilities.createResFile(resDict, language, resource)

    except:
        print("--- Could not parse : " + language + ":" + res + " ---")
    else:
        print(">>> " + language + ":" + res + "  has been successfully parsed <<<")

        mapper.select_mapping(resDict, res, language, g)

        print(">>> " + language + ":" + res + "  has been mapped <<<")

file_name = "ListExtractor_" + utilities.getDate() + ".ttl"
g.serialize(file_name, format="turtle")
