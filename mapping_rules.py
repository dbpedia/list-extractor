# Used to select a mapping function for the given resource class,
# Values must correspond to mapping methods in the form of 'map_bibliography()'
MAPPING = {'Writer': 'BIBLIOGRAPHY'}

# Contains the substrings to be searched in section names in order to relate a list to the topic (here: Bibliography)
# Title describes the topic and is a value from MAPPING
# Keys correspond to language prefix from the page to be extracted, Values to section titles
BIBLIOGRAPHY = {
    'en': ['bibliography', 'works', 'fiction', 'novels', 'books', 'publications', 'comics'],
    'it': ['opere', 'romanzi', 'saggi', 'pubblicazioni', 'edizioni']
}

# Used to reconcile section names with literary genres of inner list elements (for bibliography-kind lists)
BIBLIO_GENRE = {
    'en': {'Novels': 'Novel', 'Short stories': 'Short_story', 'Short Fiction': 'Short_story',
           'Comics': 'Comic', 'Articles': 'Article', 'Essays': 'Essay', 'Plays': 'Play_(theatre)',
           'Anthologies': 'Anthology', 'Non-fiction': 'Non-fiction',
           'Nonfiction': 'Non-fiction', 'Poetry': 'Poetry', 'Science fiction': 'Science_fiction',
           'Biographies': 'Biography'},
    'it': {'Romanzi': 'Romanzo', 'Racconti': 'Racconto', 'Antologie': 'Antologia',
           'Audiolibri': 'Audiolibro', 'Saggi': 'Saggio', 'Poesie': 'Poesia', 'Drammi': 'Dramma'}
}
