#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re

OSM_PATH = "Schaumburg_vic.osm"


def process_map(filename):
    ''' OSM file -> set of unique user IDs ("uid")

    called by test()
    '''

    users = set()
    for _, element in ET.iterparse(filename):
        for key, value in element.attrib.items():
            if key == 'uid':
            	
                users.add(element.attrib['uid'])

    return users


def test():

    users = process_map(OSM_PATH)
    pprint.pprint(len(users))
    print 
    print "Number of unique users: {}".format(len(users))


if __name__ == "__main__":
    test()