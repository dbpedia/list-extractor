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
            'language' : ['External links', 'References', 'See also', 'Further reading']


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

EXCLUDED_SECTIONS = {
        "de": ["Einzelnachweise", "Weblinks", "Literatur", "Siehe auch"],
        "en": ["External links", "References", "See also", "Further reading"],
        "it": ["Collegamenti esterni", "Bibliografia", "Altri progetti", "Voci correlate"],
        "es": ["Referencias", "V\u00e9ase tambi\u00e9n", "Enlaces externos", "Notas"]
    }
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
    'de': ['bibliographie', 'werke','arbeiten', 'bücher', 'publikationen'],
    'es': ['Obras', 'Bibliografía', '']
}

FILMOGRAPHY = {
    'en': ['filmography','shows'],
    'it': ['filmografia'],
    'de': ['Filmografie'],
    'es': ['Filmografía', 'Televisión']
}

DISCOGRAPHY = {
    'en' : ['discography', 'studio', 'singles', 'soundtrack'],
    'it' : ['discografia'],
    'de' : ['Diskografie'],
    'es' : ['Discografía', 'Albumes'],
}

BAND_MEMBERS = {
    'en' : ['members', 'bands', 'personnel', 'team', ],
    'it' : ['Formazione','Membri', 'bande', 'personale', 'team'],
    'de' : ['Bandmitglieder', 'Besetzung', 'Mitglieder', 'Gruppe', 'Personal'],
    'es' : ['Miembros', 'banda', 'grupo', 'personal'],
}

CONCERT_TOURS = {
    'en': ['Concert', 'tours'],
    'it': ['Tournée', 'concerto'],
    'de': ['Tourneen', 'Konzerte', 'Konzert'],
    'es': ['Giras musicales', 'Giras'],
}

ALUMNI = {
    'en': ['alumni', 'pupil'],
    'it': [],
    'de': []
}

STAFF = {
    'en': ['professors', 'Presidents', 'Faculty', 'staff', 'people', 'Principals', 'recipients'],
    'it': [],
    'de': []
}

PROGRAMS_OFFERED = {
    'en': ['Programs', 'Programmes', 'Faculties', 'Academics', 'Courses', 'Departments' ],
    'it': [],
    'de': []
}

HONORS = {
    'en': ['Recognition','awards','honors','honours', 'legacy','titles', 'accomplishments']
}

CAREER = {
    'en': ['works', 'work', 'career','expeditions','tree']
}


OTHER_PERSON_DETAILS = {
    'en': ['family','marriages','restaurants', 'memberships']
}

CONTRIBUTORS = {
    'en': ['contributors', 'staff' , 'cover', 'editors', 'editor', 'publisher', 'publishers', 'celebrity',
            'celebrities', 'mastheads', 'columnist', 'correspondent', 'reporter', 'personalities', 'personnel',
            'personal' ]
}

OTHER_LITERATURE_DETAILS = {
    'en': {'edition':'edition', 'reprints':'edition', 'publication':'publisher', 'Columns':'Article',
            'feature':'features', 'supplement':'sisterNewspaper', 'papers':'researchPaper', 
            'Characters':'FictionalCharacter', 'adaptations':'Adaptation'}
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
           'Anthologies': 'Anthology', 'Non-fiction': 'Non-fiction', 'Comedy':'comedy', 'other':'other',
           'Nonfiction': 'Non-fiction', 'Poetry': 'Poetry', 'Science fiction': 'Science_fiction',
           'Biographies': 'Biography'},

    'it': {'Romanzi': 'Novel', 'Racconti': 'Story', 'Antologie': 'Anthology', 'Non-fiction': 'Non-fiction',
           'Audiolibri': 'Audiobook', 'Saggi': 'Essay', 'Poesie': 'Poetry', 'Drammi': 'Drama', 'Altri':'other',
           'audiolibro':'Audiobook', 'finzione':'Fiction', 'saggistica':'Non-Fiction'},

    'de': { 'poesie': 'Poetry', 'dramen': 'Drama', 'kurzgedichte': 'Poem', 'kurzgeschichten': 'Short_story',
            'Übersetzungen':'translator', 'erzählungen':'story','romane':'Romance', 'verfilmungen':'adaptations',
            'dokumentarfilm':'documentary', 'journal':'journal', 'gedichte':'poem', 'märchen':'fairy_tales', 
            'bühnenstücke':'Play_(theatre)', 'essays':'essay', 'gedichtbände':'poem', 'aufzeichnungen':'record', 
            'hörbücher':'Audiobook', 'autobiografisches':'Autobiography', 'briefe':'letter'},

    'es': {'Novela': 'Novel', 'Antologías':'Anthology', 'Cuentos':'story', 'Guiones':'Script', 'Películas':'Movie',
            'Prosa':'letter', 'Tragedia':'Tragedy', 'Comedia':'comedy', 'Relatos':'story', 'No ficción':'Non-ficton',
            'ficción':'Ficton', 'drama':'drama', 'tragedia':'drama', 'otros':'other'}

}

"""Used in map_filmography to select a property which specifies how the given resource takes part in the movie"""
FILMOGRAPHY_PARTICIPATION = {
    'en': {'Actor': 'starring', 'Director': 'director', 'Producer': 'producer', 'Dubbing': 'voice',
            'Actress':'starring', 'screen Writer':'screenWriter', 'voice':'voice'},

    'it': {'Attore': 'starring', 'Attrice': 'starring', 'Sceneggiatore': 'screenWriter',
           'Sceneggiatrice': 'screenwriter', 'Produttore': 'producer', 'Produttrice': 'producer',
           'Doppiatore': 'voice', 'Doppiatrice': 'voice', 'Regista': 'director', 'Montaggio': 'editing',
           'Montatore': 'editing', 'Montatrice': 'editing' },

    'de': {'Darsteller': 'starring', 'Spielfilme': 'starring', 'Fernsehserien':'starring', 
            'Darstellung': 'starring', 'Kinofilme': 'starring', 'Darstellerin':'starring',
            'Schauspieler':'starring', 'Synchronsprecher':'voice', 'Produzent': 'producer', 
            'Drehbuchautor':'screenWriter', 'Darsteller':'starring', 'Regisseur':'director',
            'Synchronsprecherin':'voice' },

    'es': {'actor':'starring', 'actriz':'starring', 'productor':'producer', 'directora':'director',
            'productora':'producer', 'director':'director', 'Escritor':'screenWriter', 
            'Películas':'starring' }

}

"""Used in map_filmography to map the rdf:type of filmography elements in current section"""
FILMOGRAPHY_TYPE = {
    'en': {'TV': 'TelevisionShow', 'Television': 'TelevisionShow', 'Animation': 'Cartoon', 'Anime': 'Anime',
           'Videogame': 'Videogame', 'Video game': 'Videogame'},

    'it': {'Televisione': 'TelevisionShow', 'TV': 'TelevisionShow', 'Animazione': 'Cartoon'},

    'de': {'Fernseh Show':'TelevisionShow', 'Fernsehen':'TelevisionShow', 'Trickfilm':'Cartoon',
            'Anime':'Anime', 'Videogame': 'Videospiel', 'Video game' : 'Videospiel'},

    'es': {'Videos musicales':'MusicVideo', 'Televisión': 'TelevisionShow', 'caricatura':'cartoon',
            'cómica':'cartoon', 'videojuego':'Videogame'}
}

"""Used in award_status_mapper to map the rdf:type of awards in current section"""
AWARD_STATUS_TYPE = {
    'en': {'Wins':'Winner', 'Won':'Winner', 'Nominated':'Nominated', 'Nominations':'Nominated', 
            'Nominee': 'Nominated', 'win':'Winner', 'winner':'winner', 'honorary':'HonoraryDegree'}
}

PERSON_DETAILS = {
    'en': {'family': 'relative', 'marriages':'spouse', 'works': 'notableWork', 'career': 'Employer', 
            'expeditions':'notableWork', 'work': 'notableWork', 'restaurants': 'owner', 
            'tree':'colleague', 'memberships':'member'}
}

TRANSLATIONS = {
    ### key: english word; val: dict of translation of words in diff lang; lang:translation
    ### ADD SPACES BEFORE AND AFTER THE ENTRY 
    'for': {'en':' for ', 'it':' per '},
    'from': {'en': ' from '}
}

CONTRIBUTION_TYPE = {
    'en': { 'covers':'coverArtist', 'publisher':'Publisher', 'producer':'Producer', 'Journalist':'Journalist',  
            'celebrity':'coverArtist', 'mastheads':'Writers', 'columnist':'Journalist', 'correspondent':'Journalist',
            'reporter':'Journalist', 'writer':'writer', 'celebrities':'coverArtist', 'president':'president',
            'cartoonist':'artist', 'director':'director', 'Satirist':'Journalist', 'editor':'chiefEditor'},
}

MONTHS = ['january', r'\Wjan\W', 'february', r'\Wfeb\W','march', r'\Wmar\W', 'april', r'\Wapr\W', r'\Wmay\W',
            'june', r'\Wjun\W', 'july' , r'\Wjul\W' , 'august', r'\Waug\W', 'september', r'\Wsep\W',r'\Wsept\W',
            'october', r'\Woct\W', 'november', r'\Wnov\W' ,'december', r'\Wdec\W']

