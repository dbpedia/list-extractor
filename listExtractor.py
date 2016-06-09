__author__ = 'feddie - Federica Baiocchi - feddiebai@gmail.com'

import wikiParser
import utilities


language = 'en'
#language = 'it'
#resource = 'List_of_works_of_William_Gibson'
resource = 'William_Gibson'

try :
    resDict = wikiParser.mainParser(language, resource)
    utilities.createResFile(resDict, language, resource)
except :
    print("--- Could not parse : " + language+":" + resource + " ---")
else:
    print(">>> " + language+":" + resource + "  has been successfully parsed and stored <<<")