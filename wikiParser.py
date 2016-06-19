import utilities

def parse_section(section, title):
    '''
    Returns a dictionary with section names as keys and their list contents as values
    :param section: current section to parse in json format
    :param title: a string used to concatenate names of nested sections
    :return: a dictionary element representing the section
    '''

    section_lists = {}  # initializing dictionary
    # parse only if there is available content
    if ('content' in section and section['content'] != ""):
        """
        #for sections with empty content, acting only as header
        if section['content'] == "" and 'title' in section :
            title = section['title']
            section_lists[title] = ""
        """
        # checks whether to concatenate the title or not
        if section['level'] > 0:  # represents a nested section
            title = str(title) + " - " + section['title']  # concatenate titles

        else:
            title = section['title']
            section_lists[title] = ""

        # don't consider keys since they are non-relevant (e.g. an0, an1,..)
        content = section['content'].values()

        sect_list = []  # will contain the list extracted from current section

        '''Extract section content - values inside dictionary inside 'content' key '''
        for val in content:
            if ('@type' in val):
                if (val['@type'] == 'list'):
                    level = 1  # level is used to keep trace of list inception
                    nest_list = []  # will contain a nested list if there is one

                    # pass list elements to be parsed
                    for cont in val['content']:
                        # check if current list element is nested
                        if ('level' in cont and cont['level'] > level):
                            level = cont['level']
                            # call parse_list on nested list and store it in nest_list variable
                            nest_cont = parse_list(cont)
                            nest_list.append(nest_cont)
                        else:
                            # if there is nested content, append it like a nested list
                            if nest_list != []:
                                sect_list.append(nest_list)
                                nest_list = []
                                level = 1
                            sect_list.append(parse_list(cont))

                    # adds a new voice in the dictionary representing list in the given section
                    section_lists[title] = sect_list

    return section_lists


def parse_list(list_elem):
    """
    Parses a list element extracting relevant info
    :param list_elem: current list item in json format
    :return: a string containing useful info from list element
    """

    list_content = ""  # initializing output

    if ('content' in list_elem and list_elem['content'] != ""):

        for cont in list_elem['content']:
            if ('@type' in cont and cont['@type'] != 'list_element'):
                # we don't want to consider templates and links
                cont_type = cont['@type']
                if (cont_type == 'link') or (cont_type == 'template'):
                    pass
                elif (cont_type == 'reference'):
                    # this format helps me to discriminate the references
                    list_content += " {{" + cont['label'] + "}} "

            elif ('label' in cont):  # if there is a label key, take only its value
                cont = cont['label']
                list_content = list_content + " " + cont + " "  # necessary to avoid lack of spaces between words

            elif ('attributes' not in cont):  # Take everything else but ignore bottom page references
                list_content += cont
    return list_content


def mainParser(language, resource):
    """
    Main method, returns final dictionary containing all extracted data from given resource in given language
    :param language: language of the resource we want to parse (e.g. it, en, fr...)
    :param resource:  name of the resource
    :return: a dictionary with sections as keys and lists as values
    """

    input = language + ":" + resource

    # JSONpedia call to retrieve sections  - in this way I can retrieve both section titles and their lists
    jsonpediaURL_sect = "http://jsonpedia.org/annotate/resource/json/" + input + "?filter=@type:section&procs=Structure"
    try:
        sections = utilities.json_req(jsonpediaURL_sect)
    except (IOError, ValueError):
        print('Network Error - please check your connection and try again')
        raise
    else:
        if 'success' in sections and sections['success'] == "false":
            print("JSONpedia error! - the web service may be currently overloaded, please try again in a while")
            # mainParser(language, resource)  #brute force approach on JSONpedia
            raise
        else:
            # JSON index with actual content
            result = sections['result']
            # dictionary containing section names as keys and featured lists as values
            lists = {}
            # iterate on every section
            for res in result:
                if '@type' in res and res['@type'] == 'section':
                    if res['level'] == 0:
                        parsed_sect = parse_section(res, "")
                        lists.update(parsed_sect)
                        keys = parsed_sect.keys()
                        header_title = keys[0]

                    elif res['level'] > 0:
                        # if it's a nested section, concatenate its name with last header title
                        parsed_sect = parse_section(res, header_title)
                        lists.update(parsed_sect)
            cleanlists = utilities.clean_dictionary(lists)  # clean resulting dictionary and leave only meaningful keys
            return cleanlists

