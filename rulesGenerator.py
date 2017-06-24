#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

############################
### rulesGenerator.py ###
############################

* This is the module that allows the user to add new mapping rules that can be used by the extractor. Follow
  the rules below to add a new language or domain to the list-extractor.

'''

import sys
import os
import argparse
import json


def main():
    """
    Entry point for rulesGenerator.
    Parses parameters and calls other modules in order to create/modify settings file.
    """
    
    # initialize argparse parameters
    parser = argparse.ArgumentParser(description=' Add/Replace mapping rules in settings.json for different domains'
                                                 '\n that can be used by list-extractor.'
                                                 '\n Example: `python rulesGenerator.py d Writer`',
                                    formatter_class = argparse.RawTextHelpFormatter,
                                    usage="rulesGenerator.py [--help] collection_mode resource language "
                                    "\nUse rulesGenerator.py -h for more details.\n ")
    # parser.add_argument('edit_mode',
    #                     help="'d' to specify rules for a particular domain(DBpedia ontology class);\n"
    #                         "'c' add custom rules that can be called with any resource/domain.\n ",
    #                     choices=['d', 'c'])
    # parser.add_argument('source', type=lambda s: unicode(s, sys.getfilesystemencoding()),
    #                     help="Select resource to extract lists from. Options are:"
    #                         "\nDBpedia ontology class (example: Writer)\n "
    #                         "\n")

    args = parser.parse_args()
    print os.path.abspath(__file__)
    # if os.path.isfile(os.path.abspath(__file__))




if __name__ == "__main__":
    main()
