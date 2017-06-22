# List-extractor - Extract Data from Wikipedia Lists

#### [GSoC'16 Detailed Progress available here](https://github.com/dbpedia/extraction-framework/wiki/GSoC_2016_Progress_Federica)
#### [GSoC'17 Detailed Progress available here](https://github.com/dbpedia/list-extractor/wiki/GSoC-2017:-Krishanu-Konar-progress)
#### [List-Extractor wiki available here](https://github.com/dbpedia/list-extractor/wiki)

## How to run the tool

`python listExtractor.py [collect_mode] [source] [language]`

* `collect_mode` : `s` or `a`

    * use `s` to specify a single resource or `a` for a class of resources in the next parameter.

* `source`: a string representing a class of resources from DBpedia ontology (find supported domains below), or a single Wikipedia page of an actor/writer.

* `language`: `en`, `it`, `de`, `es` (for now, available only for selected domains)

    * a two-letter prefix corresponding to the desired language of Wikipedia pages and SPARQL endpoint to be queried.

## Examples: 

* `python listExtractor.py a Writer it` 
* `python listExtractor.py s William_Gibson en`

If successful, a .ttl file containing RDF statements about the specified source is created inside a subdirectory called `extracted`.

### Supported Domains(In progress):

* English (`en`):
    * **Person**: `Writer`, `Actor`, `MusicalArtist`, `Athelete`, `Polititcian`, `Manager`, `Coach`, `Celebrity` etc.
    * **EducationalInstitution**: `University`, `School`, `College`, `Library`
    * **PeriodicalLiterature**: `Magazines`, `Newspapers`, `AcademicJournals`
    * **Group**: `Band`

* Other (`it`, `de`, `es`):
    * `Writer`, `Actor`, `MusicalArtist`


### Requirements
* [Python 2.7](https://www.python.org/download/releases/2.7/) and [RDFlib library](http://rdflib.readthedocs.io/en/stable/gettingstarted.html)
* Stable internet connection

