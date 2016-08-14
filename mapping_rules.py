"""
The "MAPPING" dictionary is used to select a mapping function for the given resource class,
each key represents a class of resources from DBpedia ontology, while values must correspond
to mapping methods in mapper.py and begin with 'map_'
"""
MAPPING = {'Writer': 'BIBLIOGRAPHY', 'Actor': 'FILMOGRAPHY', 'Director': 'FILMOGRAPHY'}

###################################################################

"""
Contains the substrings to be searched inside section names in order to relate a list to the topic (here: Bibliography)
The name of the dictionary describes the topic and must be a value from MAPPING.
Keys correspond to language prefix from the page to be extracted, their values to various section titles used to express that concept
"""
BIBLIOGRAPHY = {
    'en': ['bibliography', 'works', 'fiction', 'novels', 'books', 'publications', 'comics'],
    'it': ['opere', 'romanzi', 'saggi', 'pubblicazioni', 'edizioni']
}

FILMOGRAPHY = {
    'it': ['filmografia', 'cinema'],
    'en': ['filmography']
}

CAST = {
    'en': ['cast'],
    'it': ['personaggi']
}

####################################################################

# Used in map_bibliography to reconcile section names with literary genres expressed by DBpedia ontology
BIBLIO_GENRE = {
    'en': {'Novels': 'Novel', 'Short stories': 'Short_story', 'Short Fiction': 'Short_story',
           'Comics': 'Comic', 'Articles': 'Article', 'Essays': 'Essay', 'Plays': 'Play_(theatre)',
           'Anthologies': 'Anthology', 'Non-fiction': 'Non-fiction',
           'Nonfiction': 'Non-fiction', 'Poetry': 'Poetry', 'Science fiction': 'Science_fiction',
           'Biographies': 'Biography'},
    'it': {'Romanzi': 'Romanzo', 'Racconti': 'Racconto', 'Antologie': 'Antologia',
           'Audiolibri': 'Audiolibro', 'Saggi': 'Saggio', 'Poesie': 'Poesia', 'Drammi': 'Dramma'}
}

# Used in map_filmography to map how the given resource takes part in the movie from the section title
FILMOGRAPHY_PARTICIPATION = {
    'it': {'Attore': 'starring', 'Attrice': 'starring', 'Regista': 'director', 'Sceneggiatore': 'screenWriter',
           'Sceneggiatrice': 'screenwriter'},
    'en': {'Actor': 'starring', 'Director': 'director'}
}
