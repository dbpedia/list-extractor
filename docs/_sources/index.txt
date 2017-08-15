
Welcome to Wikipedia List-Extractor's documentation!
====================================================

The List-Extractor is a tool that can *extract information from wikipedia lists and form appropriate RDF triples*, written by Krishanu Konar and Federica Baiocchi and licensed under the `GNU General Public License v3.0`.

Wikipedia, being the world’s largest encyclopedia, has humongous amount of information present in form of text. While key facts and figures are encapsulated in the resource’s infobox, and some detailed statistics are present in the form of tables, but there’s also a lot of data present in form of lists which are quite unstructured and hence its difficult to form into a semantic relationship. This tool allows the extraction of relevant but hidden data which lies inside lists in Wikipedia pages. This tool can extract information from wikipedia lists and form appropriate RDF triplets that can be inserted in the DBpedia dataset.


Quick-Start
===========

.. code:: python

	python listExtractor.py [collect_mode] [source] [language] [-c class_name]

**Examples:**

To simply start extracting triples form a particular resource, use ``collect_mode=s``.

* ``python listExtractor.py s Berlin en`` : Uses the default inbuilt mapper-functions
* ``python listExtractor.py s William_Gibson en -c CUSTOM_WRITER`` : Uses the `CUSTOM_WRITER` mapping only to extract list elements.

To simply start extracting triples form a domain, use ``collect_mode=a``.

* ``python listExtractor.py a Writer it`` 
* ``python listExtractor.py a MusicalArtist en`` 

Contents
========

.. toctree::
	:maxdepth: 2

	about
	mapping_process
	rules_generator
	code
	license
	3rd_party
	contact

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

