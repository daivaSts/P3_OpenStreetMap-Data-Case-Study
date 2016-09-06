#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import pprint

OSM_PATH = "Schaumburg_vic.osm"

def count_tags(filename):
    result = dict()

    for a, b in ET.iterparse(filename, events= ('start',)):
        result[b.tag]  = result.get(b.tag, 0) + 1
    return result   

def count_tags1(filename):
        # YOUR CODE HERE
    tree = ET.parse(filename)
    root = tree.getroot()
    
    tags = dict()
    for element in root.iter():
       
        tags[element.tag] = tags.get(element.tag, 0) + 1
    return tags 



def test():

    tags = count_tags(OSM_PATH)
    print
    pprint.pprint(tags)
    print 


    

if __name__ == "__main__":
    test()