import urllib
import json

'''
returns a json representation of a Wiki Page obtained from a call to jsonpedia web service
'''
def jsonpedia_req(req):
    call = urllib.urlopen(req)
    answer = call.read()
    parsed_ans = json.loads(answer)
    return parsed_ans

'''
returns a dictionary with section names as keys and their list contents as values
'''
def section_parser(section, title) :
    #initializing dictionary
    page_lists = {}
    #parse only if there is available content
    if ('content' in section and section['content'] != "") :
        #checks whether to concatenate the title or not
        if section['level'] > 0 : #represents a nested section
            title = str(title) + " - " + section['title'] #concatenate titles
        else :
            title = section['title']

        content = section['content'].values() #don't consider keys since they are non-relevant (e.g. an0, an1,..)
        sect_list = [] #will contain the list extracted from current section
        '''Extract section content'''
        for val in content :
            if ('@type' in val) :
                if (val['@type'] == 'list') :

                    for cont in val['content'] : #pass list content to be parsed
                        sect_list.append(list_parser(cont))
                    #adds a new voice in the dictionary representing list in the given section
                    page_lists[title] = sect_list

                elif (title not in page_lists) :
                    page_lists[title] = ""
            elif ('title' in val) :
                page_lists[title] = ""
    return page_lists


'''
returns a list containing the list elements inside a section
'''
def list_parser(json_content) :

    list_content = "" #initializing output list
    if ('content' in json_content and json_content['content'] != ""):

        for cont in json_content['content'] :
            if ('label' in cont): # if there is a label key, take only its value
                cont = cont['label']
                list_content += cont
            elif ('@type' in cont and cont['@type'] != 'list_item'): # leave templates and links as they are, as it's structured info
                cont_type = cont['@type']
                if (cont_type == 'link') or (cont_type == 'template'):
                    list_content+=str(cont)
                '''
            elif ('content' in cont): #if there is a nested content, recursively call this function
                print("innesting")
                curr_list.append(list_parser(cont['content']))
                list_content+= str(cont)
                '''
            elif ('attributes' not in cont) :  # Take everything else but ignore bottom page references
                list_content += cont

    return list_content

'''
Main method, returns final dictionary containing all extracted data from given resource in given language
'''
def wikiParser(language, resource) :

    input = language + ":" + resource

    #JSONpedia call to retrieve sections (not using it now, but could be useful to retrieve titles
    jsonpediaURL_sect = "http://jsonpedia.org/annotate/resource/json/" + input + "?filter=@type:section&procs=Structure"

    try:
        sections = jsonpedia_req(jsonpediaURL_sect)
    except (IOError, ValueError):

        print('Network Error - please check your connection and try again')
    else:
        if 'success' in sections:
            if sections['success'] == "false":
                print("JSONpedia error! - the web service may be currently overloaded, please try again in a while")

        else:
            # JSON index with actual content
            result = sections['result']

            # dictionary containing section names as keys and featured lists as values
            lists = {}

            # iterate on every section
            for res in result:
                if '@type' in res and res['@type'] == 'section':
                    if res['level'] == 0:
                        parsed_sect = section_parser(res, "")
                        lists.update(parsed_sect)
                        keys = parsed_sect.keys()
                        header_title = keys[0]

                    elif res['level'] > 0:
                        # if it's a nested section, concatenate its name with last header title
                        parsed_sect = section_parser(res, header_title)
                        lists.update(parsed_sect)

        return lists



print(wikiParser('en', 'List_of_works_of_William_Gibson'))