# list-extractor - Extract Data from Wikipedia Lists

#### [GSoC'16 Progress available here](https://github.com/dbpedia/extraction-framework/wiki/GSoC_2016_Progress_Federica)

###How to run the script
`python listExtractor.py res_type language`
* `res_type`: a string representing a class of resources from DBpedia ontology (it works with Writer for now)
* `language`: a language two-letters long prefix corresponding to the desired language of Wikipedia pages and SPARQL endpoint (it accepts only 'en'' or 'it' at the moment)
(e.g. `python listExtractor.py Writer en`)
If successful, a .ttl file containing RDF triples with the literary work as subject, related to its author and publication year will be returned.

### Modules:
**listExtractor** Starting point, calls other modules. Ideally it will call the collector once and iterate the other calls on each resource found to extract data
 
**wikiParser** mainParser function takes a language and a wiki-page and returns a dictionary containing section names as keys and their inner lists as values. To do so it uses the [JSONpedia web service] (http://jsonpedia.org/frontend/index.html) and calls _jsonpedia_req function_ (which returns a json representation of given page), and _parse_section_ which iterates on every section and constructs the dicionary using _parse_list_ on each list element. 

**mapper** Takes a resource dictionary and construct the RDF triples. In order to do so, it must try to apply a set of specified rules to every list element, considering also the section name. It uses [WikiData API](https://www.wikidata.org/w/api.php) to reconcile URI references and then queries the endpoint for the correspondant DBpedia resource. It also applies regular expressions to unstructured text in list elements in order to extract relevant info.

**utilities** contains accessory functions (e.g. querying a sparql endpoint, creation of a file containing the dictionary which represents a resource...)

### Abstract:
 _The project focuses on the extraction of relevant but hidden data which lies inside lists in Wikipedia pages. The information is unstructured and thus cannot be easily used to form semantic statements and be integrated in the DBpedia ontology. Hence, the main task consists in creating a tool which can take one or more Wikipedia pages with lists within as an input and then construct appropriate mappings to be inserted in a DBpedia dataset. The extractor must prove to work well on a given domain and to have the ability to be expanded to reach generalization._