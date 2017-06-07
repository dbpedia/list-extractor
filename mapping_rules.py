# -*- coding: utf-8 -*-


'''

########################
### mapping_rules.py ###
########################

* This is the main module that contains all the mapping rules that are used by the extractor. Follow
  the rules below to add a new language or domain to the list-extractor.

* This module is structured in three parts:

    * First, an entry is created in the MAPPING DICTIONARY, which maps a DBpedia ontology to one 
      of the mapping dicts that contains the list of possible section headers for which mapper
      functions run.

    * Next, an entry in the SECTION DICTIONARY is created.
      Now a MAPPING_DICT is created, which contains the section headers that would be explored
      in the given resource. If the wiki-article contains any of these headers, the corresponding 
      mapper functions would be run, as present in the mapper.py.

    * At last, entries (if any) are made in the ATTRIBUTE DICTIONARY.
      Here, dictionaries for additional properties are created. These are used by the sub-mapper
      functions to add other relevant triplets.

    * Add the following sections to the EXCLUDED_SECTIONS dictionary to avoid processing uninformative
      lists:
            'External links', 'References', 'See also', 'Further reading',  #language


'''

#############################################################


'''
##########################
### MAPPING DICTIONARY ###
##########################

* The "MAPPING" dictionary is used to select a mapping function for the given resource class, each 
  key represents a class of resources from DBpedia ontology, while values MUST correspond to mapping 
  methods in mapper.py and begin with 'map_'

* Add entries in the format 
    OntologyClass : SectionDictionary

'''

MAPPING = {'Writer': 'BIBLIOGRAPHY', 'Actor': 'FILMOGRAPHY', 'MusicalArtist': 'DISCOGRAPHY',
            'Band':'DISCOGRAPHY', 'Group':'BAND_MEMBERS'}

EXCLUDED_SECTIONS = [
                        'External links', 'References', 'See also', 'Further reading',  #en
                        'Collegamenti esterni', 'Bibliografia', 'Altri progetti', 'Voci correlate', #it
                        'Einzelnachweise', 'Weblinks', 'Literatur', 'Siehe auch', #de
                    ]


#############################################################


'''
############################
### SECTION DICTIONARIES ###
############################

Contains the substrings or keywords to be searched inside section names in order to relate a list to the topic.
The name of the dictionary describes the topic and MUST be a value from MAPPING.
Keys correspond to language prefix from the page to be extracted, their values to a list of section titles
used to express the concept.
'''

BIBLIOGRAPHY = {
    'en': ['bibliography', 'works', 'novels', 'books', 'publications'],
    'it': ['opere', 'romanzi', 'saggi', 'pubblicazioni', 'edizioni'],
    'de': ['bibliographie', 'werke','arbeiten', 'bücher', 'publikationen']
}

FILMOGRAPHY = {
    'en': ['filmography'],
    'it': ['filmografia'],
    'de': ['filmografie']
}

DISCOGRAPHY = {
    'en' : ['discography', 'studio', 'singles', 'soundtrack', 'compilation'],
    'it' : ['discografia'],
    'de' : ['Diskografie']
}

BAND_MEMBERS = {
    'en' : ['members', 'bands', 'personnel', 'team', ],
    'it' : ['Formazione','Membri', 'bande', 'personale', 'team'],
    'de' : ['Bandmitglieder', 'Besetzung', 'Mitglieder', 'Gruppe', 'Personal']
}



#############################################################

'''
##############################
### ATTRIBUTE DICTIONARIES ###
##############################

Contains dictionaries that contains various properties that a particular resource can have, inside the 
given section. These are used inside the mapper functions.

'''

"""Used in map_bibliography to reconcile section names with literary genres expressed by DBpedia ontology classes"""
BIBLIO_GENRE = {
    'en': {'Novels': 'Novel', 'Short stories': 'Short_story', 'Short Fiction': 'Short_story',
           'Comics': 'Comic', 'Articles': 'Article', 'Essays': 'Essay', 'Plays': 'Play_(theatre)',
           'Anthologies': 'Anthology', 'Non-fiction': 'Non-fiction',
           'Nonfiction': 'Non-fiction', 'Poetry': 'Poetry', 'Science fiction': 'Science_fiction',
           'Biographies': 'Biography'},

    'it': {'Romanzi': 'Romanzo', 'Racconti': 'Racconto', 'Antologie': 'Antologia',
           'Audiolibri': 'Audiolibro', 'Saggi': 'Saggio', 'Poesie': 'Poesia', 'Drammi': 'Dramma'},

    'de': { 'poesie': 'Poetry', 'dramen': 'Drama', 'kurzgedichte': 'Poem', 'kurzgeschichten': 'Short_story',
            'Übersetzungen':'translator', 'erzählungen':'story','romane':'Romance', 'verfilmungen':'adaptations',
            'dokumentarfilm':'documentary', 'journal':'journal', 'gedichte':'poem', 'märchen':'fairy_tales', 
            'bühnenstücke':'Play_(theatre)', 'essays':'essay', 'gedichtbände':'poem', 'aufzeichnungen':'record', 
            'hörbücher':'Audiobook', 'autobiografisches':'Autobiography', 'briefe':'letter'}

}

"""Used in map_filmography to select a property which specifies how the given resource takes part in the movie"""
FILMOGRAPHY_PARTICIPATION = {
    'en': {'Actor': 'starring', 'Director': 'director', 'Producer': 'producer', 'Dubbing': 'voice'},

    'it': {'Attore': 'starring', 'Attrice': 'starring', 'Sceneggiatore': 'screenWriter',
           'Sceneggiatrice': 'screenwriter',
           'Doppiatore': 'voice', 'Doppiatrice': 'voice', 'Regista': 'director', 'Montaggio': 'editing',
           'Montatore': 'editing', 'Montatrice': 'editing', 'Produttore': 'producer', 'Produttrice': 'producer'}

    'de': {'Darsteller': 'starring', 'Spielfilme': 'starring', 'Fernsehserien':'starring', 
            'Schauspieler':'starring', 'Synchronsprecher':'voice', 'Produzent': 'producer', 
            'Drehbuchautor':'screenWriter', 'Darsteller':'starring', 'Regisseur':'director' }
}

"""Used in map_filmography to map the rdf:type of filmography elements in current section"""
FILMOGRAPHY_TYPE = {
    'en': {'TV': 'TelevisionShow', 'Television': 'TelevisionShow', 'Animation': 'Cartoon', 'Anime': 'Anime',
           'Videogame': 'Videogame', 'Video game': 'Videogame'},

    'it': {'Televisione': 'TelevisionShow', 'TV': 'TelevisionShow', 'Animazione': 'Cartoon'}

    'de': {'Fernseh Show':'TelevisionShow', 'Fernsehen':'TelevisionShow', 'Trickfilm':'Cartoon',
            'Anime':'Anime', 'Videogame': 'Videospiel', 'Videogame' : 'Videospiel'}
}


FOOTBALL_CLUBS = {
    'en' : ['honors', 'honours', 'achievements', 'former', 'records', 'board', 'officials', 'staff', 'members', 
            'managers', 'players', 'honorary']
}

EDUCATIONAL_INSTITUTES = {
    'en' : ['organisation', 'organization', 'alumni', 'scholarships', 'faculty', 'administration', 
            'institutions', 'research', 'academics', 'principals', 'courses', 'campuses'],
    'it' : []   
}

MAGAZINE_CONTRIBUTION = {
    'en' : ['contributor', 'contributors', 'mastheads', 'staff', 'ex-staff', 'winners', 'editors', 
            'members', 'team', 'columnists', 'correspondents', 'reporters'],
    'it' : []
}

NEWSPAPER_CONTRIBUTION = {
    'en' : ['contributor', 'contributors', 'mastheads', 'staff', 'ex-staff', 'writers', 'editors', 
            'members', 'personalitites','team', 'columnists', 'cartoonists', 'alumni', 'correspondents', 'reporters'],
    'it' : []
}

MUSIC_GENRE = {
    'en': { 'Blues':'Blues', 'Folk': 'Folk', 'Classical': 'Classical', 'Ballet': 'Ballet', 'Opera': 'Opera',
            'Country': 'Country', 'Alternative': 'Alternative', 'Electronic': 'Electronic', 'Ambient': 'Ambient',
            'Dance': 'Dance', 'Trance': 'Trance', 'Hip Hop': 'Hip_Hop', 'Indie': 'Hip Hop', 'Jazz': 'Jazz',
            'Latin': 'Latin', 'Acoustic': 'Acoustic', 'Pop': 'Pop', 'R&B/Soul': 'R&B',
            'Rock': 'Rock', 'Grunge': 'Grunge', 'Hard Rock': 'Hard_Rock', 'Metal': 'Metal', 'Reggae':'Reggae',
            'Rap': 'Rap' 
        },

    'it': {}
}


CONTRIBUTION_TYPE = {
    'en': {

    },

    'it': {
    }
}

