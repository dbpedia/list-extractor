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

mappers = [ "BIBLIOGRAPHY", "FILMOGRAPHY", "DISCOGRAPHY", "BAND_MEMBERS", "CONCERT_TOURS", "ALUMNI",
            "STAFF", "PROGRAMS_OFFERED", "HONORS", "CAREER", "OTHER_PERSON_DETAILS", "CONTRIBUTORS",
            "OTHER_LITERATURE_DETAILS"]

settings = dict()

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
    print 'Loading settings file....'
    settings = load_settings()

    prompt_str = "Select one of the following options:\n\n" \
                  "1. Show existing mapping rules\n" \
                  "2. Show available mapper functions\n" \
                  "3. Add new rules\n" \
                  "3. exit" \
                  "\nYour option: "

    print ''
    while True:
        try:
            run = int(input(prompt_str))
            if run == 1:
                show_mappings(settings)
            elif run == 2:
                show_mapper_functions()
            elif run == 3:
                add_mapping_rule(settings)
            else: 
                print 'Invalid option! \n'
                continue
            raw_input()
        except SyntaxError: print 'Invalid option! \n'


def show_mappings(settings):
    mappings = settings["MAPPING"]
    print 'Following are the classes whose mappings exist:'
    print 'Format: Ontology Class : \n    [ List of mapper functions ]\n'
    for key in mappings.keys():
        print '   ', key, ':'
        print '   ', '-' * (len(key)+2), "\n"
        for func in mappings[key]:
            print '       ', func
        print '\n'

def show_mapper_functions():
    print 'Available mapper functions (See mapping_rules.py for details):\n'
    for mapper in mappers:
        print '   ', mapper
    print ''

def add_mapping_rule(settings):
    mappings = settings['MAPPING']
    print '\nEnter Ontology Class (Domain) name/ Custom Name: '
    class_name = raw_input().replace(" ","").upper()

    if class_name in mappings.keys():
        print 'A mapping with the given classname already exists:'
        print '   ', class_name
        for func in mappings[class_name]:
            print '       ', func
        print '\n Do you want to change the existing mapping?? (Y/N)'
        opt = raw_input()
        if opt in ['Y', 'y', 'yes']:
            settings['MAPPING'].pop(class_name)
        else:
            print 'Aborting....'
            return

    print 'Enter Mapping functions with the class (comma seperated):'
    mapper_functions = []
    map_str = raw_input().split(",")
    for s in map_str:
        if s.strip().upper() in mappers:
            mapper_functions.append(s.strip().upper())
    if len(mapper_functions) == 0:
        print 'No matching mapper functions were found!\nABorting...'
        return
    else:
        print 'Following mapper functions were found!'
        print mapper_functions,'\n'
        opt = raw_input('Do you want to save this mapping? (Y/N): ')
        if opt in ['Y', 'y', 'yes']:
            settings['MAPPING'][class_name] = mapper_functions
            dump_settings(settings)
            print 'Mapping saved!!'
            return
        else:
            print 'Mapping cancelled!!'
            return

def dump_settings(new_settings):
    settings_file = open("settings.json", "w+")
    settings_file.write(json.dumps(new_settings))
    settings_file.close()
    settings = load_settings()
    return

def load_settings():
    try:
        with open('settings.json') as settings_file:
            settings = json.load(settings_file)
            print 'Successful!\n'
            return settings
    except IOError:
        print "Settings files doesn't exist!!! "
        sys.exit(1)

if __name__ == "__main__":
    main()
