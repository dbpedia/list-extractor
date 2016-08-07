# -*- coding: utf-8 -*-
import utilities
import time

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
        # checks whether to concatenate the title or not
        if section['level'] > 0:  # represents a nested section
            title += " - " + section['title']  # concatenate titles
        else:
            title = section['title']
            section_lists[title] = ""

        # don't consider keys since they are non-relevant (e.g. an0, an1,..)
        content = section['content'].values()
        sect_list = []  # will contain the list extracted from current section

        '''Extract section content - values inside dictionary inside 'content' key '''
        for val in content:
            if ('@type' in val):
                # look for lists in current section
                if (val['@type'] == 'list'):
                    level = 1  # level is used to keep trace of list inception
                    nest_list = []  # will contain a nested list if there is one
                    # pass list elements to be parsed
                    for cont in val['content']:
                        # check if current list element is nested
                        if ('level' in cont and cont['level'] > level):
                            level = cont['level']  # update inception level
                            nest_cont = parse_list(
                                cont)  # call parse_list on nested list and store it in nest_list variable
                            nest_list.append(nest_cont)
                            sect_list.append(nest_list)
                            nest_list = []
                            level = 1
                        else:
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
    if ('content' in list_elem and list_elem['content'] != None):
        for cont in list_elem['content']:
            if ('@type' in cont and cont['@type'] != 'list_element'):
                cont_type = cont['@type']
                if (cont_type == 'template' or cont_type == 'link'):
                    tl_cont = cont['content']
                    if type(tl_cont) == list:
                        for tl_val in tl_cont.values():  # look for significant info in templates or links
                            list_content += tl_val[0] + " "
                    elif type(tl_cont) == dict:
                        if '@an0' in tl_cont:  # structure type with ad anonymous field
                            tl_val = tl_cont['@an0']  # template content lies inside first anonymus value
                            if type(tl_val) == list:
                                for tlv in tl_val:
                                    if type(tlv) == dict:
                                        list_content += tlv['label']  # for references
                                    else:
                                        list_content += tlv + " "  # for actual values
                                        # list_content += tl_val + " "
                elif (cont_type == 'reference'):
                    # this format helps me to discriminate the references
                    list_content += " {{" + cont['label'] + "}} "

            elif ('label' in cont):  # if there is a label key, take only its value
                cont = cont['label']
                list_content = list_content + " " + cont + " "  # necessary to avoid lack of spaces between words

            elif ('attributes' not in cont):  # Take everything else but ignore bottom page references
                list_content += cont
    return list_content


def jsonpedia_convert(language, resource):
    """
    Calls JSONpedia online service to get a JSON representation of the Wikipedia page divided in sections
    :param language: language of the resource we want to parse (e.g. it, en, fr...)
    :param resource:  name of the resource
    :return: a JSON with significant info about the resource
    """
    input = language + "%3A" + resource

    # JSONpedia call to retrieve sections  - in this way I can retrieve both section titles and their lists
    jsonpediaURL_sect = "http://jsonpedia.org/annotate/resource/json/" + input + "?filter=@type:section&procs=Structure"
    try:
        sections = utilities.json_req(jsonpediaURL_sect)
    except (IOError):
        print('Network Error - please check your connection and try again')
        raise IOError
    except (ValueError):
        raise ValueError
    else:
        if 'success' in sections and sections['success'] == "false":
            if sections['message'] == 'Invalid page metadata.':
                print("JSONpedia error: Invalid metadata. "),
                raise
            else:
                print("JSONpedia error! - the web service may be currently overloaded, please try again in a while. "
                      "Error: " + sections['message'])
                time.sleep(1)
                return jsonpedia_convert(language, resource)  # try again JSONpedia call
        else:
            #JSON index with actual content
            result = sections['result']
            return result


def main_parser(language, resource):
    """
    Main method, returns final dictionary containing all extracted data from given resource in given language
    :param language: Language of Wikipedia page, needed by JSONpedia to identify the resource
    :param resource: Resource name, needed by JSONpedia
    :return: a dictionary containing section names as keys and featured lists as values, without empty fields
    """
    result = jsonpedia_convert(language, resource)
    if result == []:
        new_resource = find_page_redirects(resource, language)
        result = jsonpedia_convert(language, new_resource)

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


def find_page_redirects(res, lang):
    """
    Calls JSONpedia to find out whether the resource name provided redirects to another Wikipedia page
    (prevents from losing pages due to non-existing names)
    :param lang: Wikipedia language of the resource
    :param res: initial resource name which may trigger a redirection
    :return: the redirection page if found
    """
    redirect = []
    jsonpedia_req = "http://jsonpedia.org/annotate/resource/json/" + lang + ":" + res + "?&procs=Structure"
    result = utilities.json_req(jsonpedia_req)
    if 'wikitext-dom' in result:
        dom = result['wikitext-dom'][0]
        if 'structure' in dom:
            new_res = dom['structure'][1]['label']
            redirect = new_res.replace(" ", "_").encode('utf-8')
    return redirect
