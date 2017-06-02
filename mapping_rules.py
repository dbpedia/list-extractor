'''
The "MAPPING" dictionary is used to select a mapping function for the given resource class,
each key represents a class of resources from DBpedia ontology, while values MUST correspond
to mapping methods in mapper.py and begin with 'map_'
'''
MAPPING = {'Writer': 'BIBLIOGRAPHY', 'Actor': 'FILMOGRAPHY', 'MusicalArtist': 'DISCOGRAPHY'}

'''
Contains the substrings or keywords to be searched inside section names in order to relate a list to the topic.
The name of the dictionary describes the topic and MUST be a value from MAPPING.
Keys correspond to language prefix from the page to be extracted, their values to a list of section titles
used to express the concept.
'''
BIBLIOGRAPHY = {
    'en': ['bibliography', 'works', 'fiction', 'novels', 'books', 'publications', 'comics'],
    'it': ['opere', 'romanzi', 'saggi', 'pubblicazioni', 'edizioni']
}

FILMOGRAPHY = {
    'en': ['filmography'],
    'it': ['filmografia']
}

DISCOGRAPHY = {
    'en' : ['discography', 'album', 'studio', 'singles', 'live', 'soundtrack', 'compilation'],
    'it' : ['discografia']
}

"""Used in map_bibliography to reconcile section names with literary genres expressed by DBpedia ontology classes"""
BIBLIO_GENRE = {
    'en': {'Novels': 'Novel', 'Short stories': 'Short_story', 'Short Fiction': 'Short_story',
           'Comics': 'Comic', 'Articles': 'Article', 'Essays': 'Essay', 'Plays': 'Play_(theatre)',
           'Anthologies': 'Anthology', 'Non-fiction': 'Non-fiction',
           'Nonfiction': 'Non-fiction', 'Poetry': 'Poetry', 'Science fiction': 'Science_fiction',
           'Biographies': 'Biography'},
    'it': {'Romanzi': 'Romanzo', 'Racconti': 'Racconto', 'Antologie': 'Antologia',
           'Audiolibri': 'Audiolibro', 'Saggi': 'Saggio', 'Poesie': 'Poesia', 'Drammi': 'Dramma'}
}

"""Used in map_filmography to select a property which specifies how the given resource takes part in the movie"""
FILMOGRAPHY_PARTICIPATION = {
    'en': {'Actor': 'starring', 'Director': 'director', 'Producer': 'producer', 'Dubbing': 'voice'},
    'it': {'Attore': 'starring', 'Attrice': 'starring', 'Sceneggiatore': 'screenWriter',
           'Sceneggiatrice': 'screenwriter',
           'Doppiatore': 'voice', 'Doppiatrice': 'voice', 'Regista': 'director', 'Montaggio': 'editing',
           'Montatore': 'editing', 'Montatrice': 'editing', 'Produttore': 'producer', 'Produttrice': 'producer'}
}

"""Used in map_filmography to map the rdf:type of filmography elements in current section"""
FILMOGRAPHY_TYPE = {
    'en': {'TV': 'TelevisionShow', 'Television': 'TelevisionShow', 'Animation': 'Cartoon', 'Anime': 'Anime',
           'Videogame': 'Videogame', 'Video game': 'Videogame'},
    'it': {'Televisione': 'TelevisionShow', 'TV': 'TelevisionShow', 'Animazione': 'Cartoon'}
}
