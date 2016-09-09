# list-extractor - Extract Data from Wikipedia Lists

#### [GSoC'16 Detailed Progress available here](https://github.com/dbpedia/extraction-framework/wiki/GSoC_2016_Progress_Federica)

###How to run the script
`python listExtractor.py collect_mode source language`
* `collect_mode` : use `s` to specify a single resource or `a` for a class of resources in the next parameter.
* `source`: a string representing a class of resources from DBpedia ontology (right now it works for Writer and Actor), or a single Wikipedia page of an actor/writer.
* `language`: a two-letter prefix corresponding to the desired language of Wikipedia pages and SPARQL endpoint to be queried (it currently accepts only `en` or `it`).

Examples: `python listExtractor.py a Writer it`  | `python listExtractor.py s William_Gibson en`

If successful, a .ttl file containing RDF statements about the specified source is created inside a subdirectory called 'extracted'.

###Requirements
* [Python 2.7](https://www.python.org/download/releases/2.7/) and [RDFlib library](http://rdflib.readthedocs.io/en/stable/gettingstarted.html)
* Stable internet connection
