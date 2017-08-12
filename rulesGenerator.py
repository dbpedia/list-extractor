#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

#########################
### rulesGenerator.py ###
#########################

* This is the module that allows the user to add new mapping rules that can be used by the extractor. Follow
  the rules below to add a new language/domain or mapper function to the list-extractor.

* This modifies the `settings.json` and `custom_mappers.json` to store all the mapping rules and the user-
  defined custom mapping functions.

'''

import sys
import os
import argparse
import json
from collections import defaultdict

#list of default mapping functions. (Present in `mapping_rules.py`)
mappers = [ "BIBLIOGRAPHY", "FILMOGRAPHY", "DISCOGRAPHY", "BAND_MEMBERS", "CONCERT_TOURS", "ALUMNI",
            "STAFF", "PROGRAMS_OFFERED", "HONORS", "CAREER", "OTHER_PERSON_DETAILS", "CONTRIBUTORS",
            "OTHER_LITERATURE_DETAILS"]

#stores and updates mapping rules and mapper functions to be used
settings = dict()
custom_mappers = dict()

def main():
    """
    Entry point for rulesGenerator.
    Parses parameters and calls other modules in order to create/modify settings file.

    :return: void
    """
    
    # initialize argparse parameters
    parser = argparse.ArgumentParser(description=' Add/Replace mapping rules in settings.json for different domains'
                                                 '\n that can be used by list-extractor.'
                                                 '\n Example: `python rulesGenerator.py d Writer`',
                                    formatter_class = argparse.RawTextHelpFormatter,
                                    usage="rulesGenerator.py [--help] collection_mode resource language "
                                    "\nUse rulesGenerator.py -h for more details.\n ")
    print 'Loading settings file....'

    #initialize the dictionaries with the saved settings
    settings = load_settings()  #initializes mapping rules
    custom_mappers = load_custom_mappers()  #initializes user defined mapper functions
    merge_mappers()  #loads both in-built and user defined mapper functions into a single dict

    #the prompt message
    prompt_str = "Select one of the following options:\n\n" \
                  "1. Show existing mapping rules\n" \
                  "2. Show available mapper functions\n" \
                  "3. Add new rules\n" \
                  "4. Add new mapper function\n" \
                  "5. Show custom mapper functions\n" \
                  "0. exit" \
                  "\nYour option: "
    print ''

    #option parser; decides the flow of the program according to what user wants to do.
    while True:
        try:
            #display and accept actions for different options
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
        #if user gives any other input, loop the prompt.
        except SyntaxError: print 'Invalid option! \n'


def show_mappings(settings):
    ''' show existing class and related mappings and display all the mapping rules. 

    :param settings: the existing settings dict, containing mapping rules

    :return: void
    '''
    mappings = settings["MAPPING"]  #load the default mapping rules
    print 'Following are the classes whose mappings exist:'
    print 'Format: Ontology Class : \n    [ List of mapper functions ]\n'
    
    #prints all the existing mapping rules
    for key in mappings.keys():
        print '   ', key, ':'
        print '   ', '-' * (len(key)+2), "\n"
        for func in mappings[key]:
            print '       ', func
        print '\n'

def show_mapper_functions():
    ''' Show available mapper functions 

    :return: void
    '''
    print 'Available mapper functions (See mapping_rules.py for details):\n'
    
    #prints all the existing mapper functions (including in-built and user defined)
    for mapper in mappers:
        print '   ', mapper
    print ''

def add_mapping_rule(settings):
    ''' The main method for adding a user defined mapping rules.
        It's an interactive method that asks user for class(domain) name and mapping functions 
        to be used and updates the `settings.json` accordingly.

    :param settings: the existing settings dict, containing mapping rules
    :return: void
    '''

    mappings = settings['MAPPING']  #load the default mapping rules

    #get the domain/class name
    print '\nEnter Ontology Class (Domain) name/ Custom Name: '
    class_name = raw_input().replace(" ","")

    #if an entry for the class already exists, determine whether to update the mapping rules
    #for the domain or not.
    if class_name in mappings.keys():
        print 'A mapping with the given classname already exists:'
        print '   ', class_name
        for func in mappings[class_name]:
            print '       ', func
        print '\n Do you want to change the existing mapping?? (Y/N)'
        
        #if user wants to update, remove the existing entry
        opt = raw_input()
        if opt in ['Y', 'y', 'yes']:
            settings['MAPPING'].pop(class_name)
        else:
            print 'Aborting....'
            return

    print 'Enter Mapping functions with the class (comma seperated):'
    mapper_functions = []

    #get the mapper function user wants to associate with the domain and add those if the mapper function
    #exists, else throw an error message
    map_str = raw_input().split(",")
    for s in map_str:
        if s.strip().upper() in mappers:
            mapper_functions.append(s.strip().upper())  #adding mapper functions to the domain
    if len(mapper_functions) == 0:
        print 'No matching mapper functions were found!\nAborting...'
        return
    else:
        print 'Following mapper functions were found!'
        print mapper_functions,'\n'
        opt = raw_input('Do you want to save this mapping? (Y/N): ')
        if opt in ['Y', 'y', 'yes']:
            #saving the mapper functions with  associated domain
            settings['MAPPING'][class_name] = mapper_functions  
            dump_settings(settings)  #updating the `settings.json` file
            print 'Mapping saved!!'
            return
        else:
            print 'Mapping cancelled!!'
            return

def add_mapper_fn():
    ''' The main method for adding a user defined mapper function.
        Its an interactive method that asks user for mapper function name, language, section headers,
        Ontology to be used, extractor functions to be used.
        Upon completion, it stores the details in `custom_mappers.json` for future use.

    :return: void
    '''
    global custom_mappers
    mapper_function = defaultdict(dict)
    mapper_name = raw_input('Enter Name of Mapper Function: ').strip().upper()
    
    #check if the mapper function already exists
    if mapper_name in mappers:
        mapper_function = custom_mappers[mapper_name]
        print mapper_name, 'already exists. Do you want to update it?(Y/N): '
        if raw_input() not in ['Y', 'y', 'yes']:  #if user doesn't want to update; stop the process
            return

    #add the language and the section headers in that language 
    lang = raw_input('Enter the language code: ')
    headers = raw_input('Enter headers of the Wiki Page to map(comma seperated): ')
    headers = [header.strip() for header in headers.split(',')]

    #select the extractor functions to be used for the element extraction
    extractor_fn_str = "Choose the extractors you want to use(comma seperated):\n" \
                        "1. Italics Mapper\n" \
                        "2. Reference Mapper\n" \
                        "3. Quote Mapper\n" \
                        "4. General Mapper\n" \
                        "\nRefer docs for more information about extractors: "
    extractors = raw_input(extractor_fn_str).split(',')
    #store the extractors to be used in form of an integer
    extractors = [int(extractor.strip()) for extractor in extractors]

    ontology_mappings = dict()
    print '\nNow adding mapping properties (dbr:<property>) ....'

    #add the ontology classes/properties to be used in the RDF triples
    #assosiate an ontology class(value) with each key    
    #also, allow the erson to use a default property, which will be used in case a match isnt found
    default_property = raw_input("Input the default key's value (Input None for no default mapping: ") 
    if default_property in ["None","none","NONE"]:
        #in this case, the mapper will ignore this list element and triple wont be added
        ontology_mappings["default"]="None"  
    else:
        #use the default value
        ontology_mappings["default"]=default_property

    while True:
        #add more ontology properties till user wants 
        add_more = raw_input("Do you want to add more properties(Y/N): ")
        if add_more not in ['y', 'Y', 'yes', 'Yes']:
            break
        try:
            #add the properties int the ontology_mappings dictionary
            key_value = raw_input("Input a key value pair (header:Property): ").split(":")
            key = key_value[0].strip()
            value = key_value[1].strip()
            ontology_mappings[key]=value
        except:
            print 'Invalid entry!!'
    
    #choose wether to extract time periods in the mapper function
    choose_year_str = raw_input('Does the list have year/time-period (Y/N): ')
    if choose_year_str in ['y', 'Y', 'yes', 'Yes']: 
        choose_year = "Yes"
    else: 
        choose_year = "No"
    
    #store all the settings input by the user as properties to a new mapper function
    mapper_function['years'] = choose_year
    mapper_function['extractors'] = extractors
    mapper_function['headers'][lang] = headers
    mapper_function['ontology'][lang] = ontology_mappings
    print '\nFollowing is the Mapper Function that would be added:\n\n"' + mapper_name + '"'  
    print json.dumps(mapper_function, indent=4)  #pretty prints the mapper function settings

    #ask user to save the new mapper function
    save_mapper = raw_input("\nDo you want to save this Mapper Function?? (Y/N): ")
    if save_mapper in ['y', 'Y', 'yes', 'Yes']:
        #dump the existing dictionary into `custom_mappers.json` and save mapper function permanently
        dump_custom_mappers(mapper_name, mapper_function)
        print 'Mapper Function saved!!'
        return
    else:
        print 'Aborted!!!'
        return


def merge_mappers():
    ''' Utility function to load both in-built and user-defined mapper functions into the
        program memory and use them.

    :return: void
    ''' 
    global mappers
    global custom_mappers
    for key in custom_mappers.keys():
        if key not in mappers:
            mappers.append(key)

def dump_custom_mappers(mapper_name, mapper_function):
    ''' THis method saves the modified custom mappers into the `custom_mappers.json` file and 
        makes a call to `load_custom_mappers()` and `merge_mappers()` to reload the custom_mappers 
        file to reflect updated changes.

    :param mapper_name: the mapper function name to be saved 
    :param mapper_function: the mapper function dict, containing settings related to the mapper function

    :return: void
    '''
    global custom_mappers
    custom_mappers[mapper_name] = mapper_function
    custom_mappers_file = open("custom_mappers.json", "w+")
    custom_mappers_file.write(json.dumps(custom_mappers))  #save the new mapper function on file
    custom_mappers_file.close()
    custom_mappers = load_custom_mappers() #reload the mapper functions file in the memory
    merge_mappers() #merge user defined and inbuilt mapper functions
    return

def load_custom_mappers():
    ''' Opens and loads the custom mapper functions from `custom_mappers.json` and stores them in 
        custom_mappers so it can be used by the rulesGenerator program.

    :return: void
    '''
    global custom_mappers
    try:
        #open and load the existing mapper functions
        with open("custom_mappers.json") as custom_mappers_file:
            try:
                custom_mappers = json.load(custom_mappers_file)
                print 'Successful!\n'
            except:
                #if no existing mapper functions found, return empty dict
                print 'Empty file!'
                custom_mappers = dict()

            return custom_mappers
    
    #handle IO exceptions
    except IOError:
        print "Settings files doesn't exist!!! "
        sys.exit(1)

def dump_settings(new_settings):
    ''' This method save the modified settings into the `setting.json` file and makes call to load_settings()
        which reloads the settings file to reflect the updated changes.

    :param new_settings: the updated settings dict to be saved 

    :return: void
    '''
    global settings
    settings_file = open("settings.json", "w+")
    settings_file.write(json.dumps(new_settings)) #saves/updates the existing settings
    settings_file.close()
    settings = load_settings() #reload the saved settings into the memory
    return

def load_settings():
    ''' This method loads the saved settings (mapping rules) from `settings.json`.

    :return: void
    '''
    global settings
    try:
        #open the settings.json file and store mapping rules in settings dict
        with open('settings.json') as settings_file:
            settings = json.load(settings_file)
            print 'Successful!\n'
            return settings
    
    except IOError:  #handles IO errors
        print "Settings files doesn't exist!!! "
        sys.exit(1)

def show_custom_mappers():
    ''' This is a utility function that displays all the mapper function created by user 
        using rulesGenerator.py

    :return: void
    '''
    global custom_mappers
    if len(custom_mappers) == 0:
        print '\nNo custom mappings yet!!\n'
        return

    #prints all custom mapper functions
    print '\nAvailable custom mappers:',
    for key in custom_mappers.keys(): print key + ",",
    print '\nDetails:\n-------\n'
    print json.dumps(custom_mappers, indent=4)

if __name__ == "__main__":
    main()
