# list-extractor - Extract Data from Wikipedia Lists

#### [GSoC'16 Progress available here](https://github.com/dbpedia/extraction-framework/wiki/GSoC_2016_Progress_Federica)



###How to run the script
`python listExtractor.py collect_mode source language`
* `collect_mode` : use `s` to specify a single resource or `a` for a class of resources in the next parameter
* `source`: a string representing a class of resources from DBpedia ontology (it works with Writer for now), or a single resource of a writer
* `language`: a two-letters long prefix corresponding to the desired language of Wikipedia pages and SPARQL endpoint to be queried (it accepts only `en` or `it` at the moment)
(e.g. `python listExtractor.py a Writer it`  | `python listExtractor.py s William_Gibson en`)
If successful, a .ttl file containing RDF triples with the literary work as subject, related to its author, publication year and possibly ISBN will be returned.

###Requirements
* Python 2.7 and [RDFlib library](http://rdflib.readthedocs.io/en/stable/gettingstarted.html)
* Stable internet connection

### Modules:
**listExtractor** Starting point, calls other modules. Verifies input parameters, collects the single resource or all the resources from a domain and then starts the mapping process iteratively adding statements to the graph. Finally, if the graph is non-empty, a .ttl file (dataset) with all the RDF statements is created in a sub-directory named 'extracted', and the total number of statement is printed.
 
**wikiParser** _mainParser_ function takes a language and a wiki-page and returns a dictionary containing all lists from page connected to their section and sub-section title (every key is a section title and its value corresponds to the related list). To do so it uses the [JSONpedia web service] (http://jsonpedia.org/frontend/index.html) calling _jsonpedia_convert_ (which returns a JSON representation of given page), and _parse_section_ which iterates on every section and constructs the dicionary using _parse_list_ on each list element. 

**mapper** Takes a resource dictionary and extracts statements adding RDF triples to the graph. In order to do so, it must try to apply a set of specified rules to every list element, considering the resource type and its section titles. It uses different mappings for each domain and other support functions to extract particular portions of text, typically by applying regular expressions or by using [WikiData API](https://www.wikidata.org/w/api.php) to reconcile URI references and querying the endpoint for the corresponding DBpedia resource.

**utilities** contains accessory functions (e.g. querying a SPARQL endpoint, creation of a file containing the dictionary which represents a resource...)

**mapping_rules** contains the dictionaries used by _mapper_ module to select the domain and to link key-words to concepts in order to form statements. It can be easily extended with new domains and key-words to expand the potential of listExtractor.

### Abstract:
 _The project focuses on the extraction of relevant but hidden data which lies inside lists in Wikipedia pages. The information is unstructured and thus cannot be easily used to form semantic statements and be integrated in the DBpedia ontology. Hence, the main task consists in creating a tool which can take one or more Wikipedia pages with lists within as an input and then construct appropriate mappings to be inserted in a DBpedia dataset. The extractor must prove to work well on a given domain and to have the ability to be expanded to reach generalization._