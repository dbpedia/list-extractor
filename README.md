# list-extractor - Extract Data from Wikipedia Lists

#### [GSoC'16 Detailed Progress available here](https://github.com/dbpedia/extraction-framework/wiki/GSoC_2016_Progress_Federica)


###How to run the script
`python listExtractor.py collect_mode source language`
* `collect_mode` : use `s` to specify a single resource or `a` for a class of resources in the next parameter.
* `source`: a string representing a class of resources from DBpedia ontology (right now it works for Writer and Actor), or a single Wikipedia page of an actor/writer.
* `language`: a two-letter prefix corresponding to the desired language of Wikipedia pages and SPARQL endpoint to be queried (it currently accepts only `en` or `it`).

(examples: `python listExtractor.py a Writer it`  | `python listExtractor.py s William_Gibson en`)

If successful, a .ttl file containing RDF statements about the specified source is created inside a subdirectory called 'extracted'.

###Requirements
* [Python 2.7](https://www.python.org/download/releases/2.7/) and [RDFlib library](http://rdflib.readthedocs.io/en/stable/gettingstarted.html)
* Stable internet connection

### Abstract
 _The project focuses on the extraction of relevant but hidden data which lies inside lists in Wikipedia pages. The information is unstructured and thus cannot be easily used to form semantic statements and be integrated in the DBpedia ontology. Hence, the main task consists in creating a tool which can take one or more Wikipedia pages with lists within as an input and then construct appropriate mappings to be inserted in a DBpedia dataset. The extractor must prove to work well on a given domain and to have the ability to be expanded to reach generalization._

###Modules
**listExtractor** Entry point, calls other modules. Verifies input parameters, collects the single resource or all the resources from a domain and proceeds with parsing, then starts the mapping process iteratively adding statements to the graph. Finally, if the graph is non-empty, a .ttl file (dataset) with all the RDF statements is created, and the total number of statement is printed.
 
**wikiParser** _mainParser_ function takes a language and a wiki-page and returns a dictionary containing all lists from page connected to their section and sub-section title (every key is a section title and its value corresponds to the related list). It uses the [JSONpedia web service] (http://jsonpedia.org/frontend/index.html) calling _jsonpedia_convert_ (which returns a JSON representation of given page), and _parse_section_ which iterates on every section and constructs the dictionary using _parse_list_ on each list element. 

**mapper** Takes a resource dictionary and extracts statements adding RDF triples to the graph. In order to do so, it must try to apply a set of specified rules to every list element, considering the resource type and its section titles. It uses different mappings for each domain and other support functions to extract particular portions of text, typically by applying regular expressions or by using [WikiData API](https://www.wikidata.org/w/api.php) to reconcile URI references and querying the endpoint for the corresponding DBpedia resource.

**utilities** contains many accessory functions (e.g. querying a SPARQL endpoint, creation of a file containing the dictionary which represents a resource...)

**mapping_rules** contains the dictionaries used by _mapper_ module to select the domain and to link key-words to concepts in order to form statements. Please refer to the paragraph below for more info about mapping. 

###Notes about mapping
When used in single resource mode, the extractor asks the endpoint for every _rdf:type_ associated to it and tries to apply every matching mapping (for example, if a person is both a writer and an actor, it will look for both lists related to bibliography and filmography). On the other hand, if using all resources mode, it will apply the related class mapping to each collected resource.
For writers, a bibliography mapping is applied to form triples having the literary work as subject, related to its author (the examined resource), publication year and ISBN if present.
For actors, a filmography mapping is applied to form triples having the movie as subject, related to its type (Film, Cartoon, TV show..), its release year and to the resource by specifying the part took in it (starring, director, producer...)
The `mapping_rules.py` file can be easily extended with new mappings, both to reach new languages and domains or to add new section keywords, thus extending the potential of List Extractor. For a new domain to be added, it is also necessary to write a new mapping function in `mapper.py`, which must be in the form of map_[ValueFromMAPPING].
The first and foremost dictionary is called MAPPING and links each class to its mapping topic; for each value in MAPPING there is another dictionary with the same name containing the specific key-words for that domain divided by language, to be matched with section titles of interest. Other dictionaries sharing the same structure are used to extract further properties from section names, like the literary genre of a written work. 

