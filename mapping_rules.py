# Used to select a mapping function for the given resource class,
# Values must correspond to mapping methods in the form of 'map_bibliography()'
MAPPING = {'Writer': 'BIBLIOGRAPHY'}

# Contains the substrings to be searched in section names in order to relate the inner list to the topic
# Title describes the topic and is a value from MAPPING
# Keys correspond to language prefix, Values to section titles
BIBLIOGRAPHY = {
    'en': ['bibliography', 'works', 'fiction'],
    'it': ['opere', 'romanzi', 'saggi', 'pubblicazioni']
}

# Used to reconcile section names with literary genres of inner list elements (for bibliography-kind lists)
BIBLIO_GENRE = {
    'en': {'Novels': 'Novel', 'Short stories': 'Short_story', 'Short Fiction': 'Short_story',
           'Comics': 'Comic', 'Articles': 'Article', 'Essays': 'Essay', 'Plays': 'Play_(theatre)'},
    'it': {'Romanzi': 'Romanzo', 'Racconti': 'Racconto', 'Antologie': 'Antologia',
           'Audiolibri': 'Audiolibro', 'Saggi': 'Saggio', 'Poesie': 'Poesia', 'Drammi': 'Dramma'}
}
