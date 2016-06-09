# list-extractor - Extract Data from Wikipedia Lists
### Abstract
_The project focuses on the extraction of relevant but hidden data which lies inside lists in Wikipedia pages. The information is unstructured and thus cannot be easily used to form semantic statements and be integrated in the DBpedia ontology. Hence, the main task consists in creating a tool which can take one or more Wikipedia pages with lists within as an input and then construct appropriate mappings to be inserted in a DBpedia dataset. The extractor must prove to work well on a given domain and to have the ability to be expanded to reach generalization._


### Modules
**WikiParser** takes a language and a wiki-page (for now: english and List_of_works_of_William_Gibson) and parses its json format returned from a call to JSONpedia web service. The result is a dictionary containing section titles as keys and corresponding lists as values.
