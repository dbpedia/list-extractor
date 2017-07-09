#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

############################
### rulesGenerator.py ###
############################

* This is the module that allows the user to add new mapping rules that can be used by the extractor. Follow
  the rules below to add a new language/domain or mapper function to the list-extractor.

'''

import sys
import os
import argparse
import json
from collections import defaultdict

mappers = [ "BIBLIOGRAPHY", "FILMOGRAPHY", "DISCOGRAPHY", "BAND_MEMBERS", "CONCERT_TOURS", "ALUMNI",
            "STAFF", "PROGRAMS_OFFERED", "HONORS", "CAREER", "OTHER_PERSON_DETAILS", "CONTRIBUTORS",
            "OTHER_LITERATURE_DETAILS"]

settings = dict()
custom_mappers = dict()

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
    custom_mappers = load_custom_mappers()
    merge_mappers()

    prompt_str = "Select one of the following options:\n\n" \
                  "1. Show existing mapping rules\n" \
                  "2. Show available mapper functions\n" \
                  "3. Add new rules\n" \
                  "4. Add new mapper function\n" \
                  "5. Show custom mapper functions\n" \
                  "0. exit" \
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
            elif run == 4:
                add_mapper_fn()
            elif run == 5:
                show_custom_mappers()
            elif run == 0:
                sys.exit(0)
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
    class_name = raw_input().replace(" ","")

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

def add_mapper_fn():
    global custom_mappers
    mapper_function = defaultdict(dict)
    mapper_name = raw_input('Enter Name of Mapper Function: ').strip().upper()
    if mapper_name in mappers:
        mapper_function = custom_mappers[mapper_name]
        print mapper_name, 'already exists. Do you want to update it?(Y/N): '
        if raw_input() not in ['Y', 'y', 'yes']: return

    lang = raw_input('Enter the language code: ')

    headers = raw_input('Enter headers of the Wiki Page to map(comma seperated): ')
    headers = [header.strip() for header in headers.split(',')]

    extractor_fn_str = "Choose the extractors you want to use(comma seperated):\n" \
                        "1. Italics Mapper\n" \
                        "2. Reference Mapper\n" \
                        "3. Quote Mapper\n" \
                        "4. General Mapper\n" \
                        "\nRefer docs for more information about extractors: "
    extractors = raw_input(extractor_fn_str).split(',')
    extractors = [extractor.strip() for extractor in extractors]

    ontology_mappings = dict()

    print '\nNow adding mapping properties (dbr:<property>) ....'
    while True:
        add_more = raw_input("Do you want to add more properties(Y/N): ")
        if add_more not in ['y', 'Y', 'yes', 'Yes']:
            break
        try:
            key_value = raw_input("Input a key value pair (\"header\":\"Property\"): ").split(":")
            key = key_value[0].strip()
            value = key_value[1].strip()
            ontology_mappings[key]=value
        except:
            print 'Invalid entry!!'
    
    choose_year_str = raw_input('Does the list have year/time-period (Y/N): ')
    if choose_year_str in ['y', 'Y', 'yes', 'Yes']: choose_year = True
    else: choose_year = False
    
    mapper_function['years'] = choose_year
    mapper_function['extractors'] = extractors
    mapper_function['headers'][lang] = headers
    mapper_function['ontology'][lang] = ontology_mappings
    print '\nFollowing is the Mapper Function that would be added:\n\n"' + mapper_name + '"'  
    print json.dumps(mapper_function, indent=4)
    save_mapper = raw_input("\nDo you want to save this Mapper Function?? (Y/N): ")
    if save_mapper in ['y', 'Y', 'yes', 'Yes']:
        dump_custom_mappers(mapper_name, mapper_function)
        print 'Mapper Function saved!!'
        return
    else:
        print 'Aborted!!!'
        return


def merge_mappers():
    global mappers
    global custom_mappers
    for key in custom_mappers.keys():
        if key not in mappers:
            mappers.append(key)

def dump_custom_mappers(mapper_name, mapper_function):
    global custom_mappers
    custom_mappers[mapper_name] = mapper_function
    custom_mappers_file = open("custom_mappers.json", "w+")
    custom_mappers_file.write(json.dumps(custom_mappers))
    custom_mappers_file.close()
    custom_mappers = load_custom_mappers()
    merge_mappers()
    return

def load_custom_mappers():
    global custom_mappers
    try:
        with open("custom_mappers.json") as custom_mappers_file:
            try:
                custom_mappers = json.load(custom_mappers_file)
                print 'Successful!\n'
            except:
                print 'Empty file!'
                custom_mappers = dict()

            return custom_mappers
    except IOError:
        print "Settings files doesn't exist!!! "
        sys.exit(1)

def dump_settings(new_settings):
    global settings
    settings_file = open("settings.json", "w+")
    settings_file.write(json.dumps(new_settings))
    settings_file.close()
    settings = load_settings()
    return

def load_settings():
    global settings
    try:
        with open('settings.json') as settings_file:
            settings = json.load(settings_file)
            print 'Successful!\n'
            return settings
    except IOError:
        print "Settings files doesn't exist!!! "
        sys.exit(1)

def show_custom_mappers():
    global custom_mappers
    if len(custom_mappers) == 0:
        print '\nNo custom mappings yet!!\n'
        return

    print '\nAvailable custom mappers:',
    for key in custom_mappers.keys(): print key + ",",
    print '\nDetails:\n-------\n'
    print json.dumps(custom_mappers, indent=4)

if __name__ == "__main__":
    main()
