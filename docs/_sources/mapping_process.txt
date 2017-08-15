**Mapping Process**
===================

This will briefly explain how the mapping process works in the List-Extractor. 

Usage
-----

.. code:: python

	python listExtractor.py [collect_mode] [source] [language] [-c class_name]

* **collect_mode** : ``s`` or ``a``

    * use ``s`` to specify a single resource or ``a`` for a class of resources in the next parameter.

* **source** : a string representing a class of resources from DBpedia ontology (find supported domains below), or a single Wikipedia page of any resource.

* **language**: ``en``, ``it``, ``de`` etc. (for now, available only for few languages in selected domains)

    * a two-letter prefix corresponding to the desired language of Wikipedia pages and SPARQL endpoint to be queried.

* **-c --classname**: a string representing classnames you want to associate your resource with. Applicable only for ``collect_mode="s"``. 

**Examples**: 

* ``python listExtractor.py a Writer it`` 
* ``python listExtractor.py s William_Gibson en`` : Uses the default inbuilt mapper-functions
* ``python listExtractor.py s William_Gibson en -c CUSTOM_WRITER`` : Uses the `CUSTOM_WRITER` mapping only to extract list elements.


Process
-------

Depending on the input, the Extractor will analyze a single Wikipedia page or all pages about resources from a given DBpedia ontology class. In both cases, each page is parsed using the `JSONpedia Library <https://bitbucket.org/hardest/jsonpedia)>`_, (`JSONpedia Web-service <http://jsonpedia.org/frontend/index.html>`_ in previous version), obtaining a representation of the inner lists, linked to their section and subsection title. The `JSONpedia wrapper` provides a simplistic command-line execution of the JSONpedia library, so it can be used easily.

At this point, it looks for all the mappings suited to the resource class and confronts the section titles to find a match with a list of keywords, depending on the requested language. If a match is found, a related mapping function is applied to each list element to form semantic triples and construct a RDF graph (for example, from a bibliography list of a writer it tries to extract info about his/her works, their literary genre, publication year and isbn code). Finally, if the graph is not empty, all statements are serialized in a .ttl file.

When used in single resource mode, the extractor asks the endpoint for every ``rdf:type`` associated to it and tries to apply every matching mapping (for example, if a person is both a writer and an actor, it will look for both lists related to bibliography and filmography). On the other hand, if using all resources mode, it will apply the related class mapping to each collected resource.

Once the resource information is retrieved and parsed, the mapping process happens.

**Mapper** module confronts the resource type(s) with a value from ``MAPPING`` dictionary inside ``settings.json`` and finds the name of the corresponding mapping function. It links each class to its mapping topic (e.g. Writer to Bibliography). For each value in MAPPING there is another dictionary with the same name containing the specific key-words for that domain divided by language, to be matched with section titles of interest. Other dictionaries sharing the same structure are used to extract further properties from section names.

- For eg., for *writers*, a bibliography mapping is applied to form triples having the literary work as subject, related to its author (the examined resource), publication year and ISBN if present. Similarly for *actors*, a filmography mapping is applied to form triples having the movie as subject, related to its type (Film, Cartoon, TV show..), its release year and to the resource by specifying the part took in it (starring, director, producer...) and so on.

The **mapping_rules.py** file can be easily extended with new mappings, both to reach new languages and domains or to add new section keywords, thus extending the potential of List Extractor. For a new domain to be added, it is also necessary to write a new mapping function in mapper.py, which must be in the form of ``map_(ValueFromMAPPING)``.

Another way of extending to include new mappings and mappers is to use **rulesGenerator**, which is an interactive tool that can be used to create mappers and rules very easily.
