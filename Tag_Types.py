#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re

OSM_PATH = "Schaumburg_vic.osm"

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    """ element object, dictionary -> dictionary

    function 'key_type' counts each of four tag categories in a dictionary:
    "lower", for tags that contain only lowercase letters and are valid,
    "lower_colon", for otherwise valid tags with a colon in their names,
    "problemchars", for tags with problematic characters, and
    "other", for other tags that do not fall into the other three categories.

    called by process_map()
    """
   
    if element.tag == "tag":
        
        if lower.search(element.attrib['k']) !=  None: 
            keys['lower'] = keys.get('lower', 0) + 1
            
        elif lower_colon.search(element.attrib['k']) != None:
            keys['lower_colon'] = keys.get('lower_colon', 0) + 1

        elif problemchars.search(element.attrib['k']) != None:
            keys['problemchars'] = keys.get('problemchars', 0) + 1

        else:
            keys['other'] = keys.get('other', 0) + 1
        
    return keys



def process_map(filename):
    ''' OSM file -> dictionary

    calls key_type(element, keys)

    called by test()
    '''
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys



def test():
    keys = process_map(OSM_PATH)
    print 
    pprint.pprint(keys)
    print
   


if __name__ == "__main__":
    test()