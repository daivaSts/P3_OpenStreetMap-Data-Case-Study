#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import re
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

import cerberus

import schema3

OSM_PATH = "Schaumburg_vic.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema3.schema

# The fields order in the csvs to match the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']

WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

#Credit: /http://stackoverflow.com/questions/3939361/remove-specific-characters-from-a-string-in-python/
phone_type_re = re.compile(r'^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$')


expected = ["Avenue", "Boulevard", "Commons", "Center", "Court", "Circle", "Drive", "Highway", "Lane", 
            "Place", "Parkway", "Road", "Square", "Street",  "Trail", 'Trail', "Way"]            

mapping = { "Ave": "Avenue",
            "Ave.": "Avenue",
            'Avenaue': "Avenue",
            "Blvd": "Boulevard",            
            "Ct": "Court",
            "Ct.": "Court",
            "Couth": "Court", 
            "center": "Center",
            "Dr": "Drive",
            "Dr.": "Drive",  
            "Hway": "Highway", 
            "Ln": "Lane",
            "Rd": "Road",
            "Rd.": "Road",
            "rd": "Road",
            "road": "Road",                   
            "St": "Street",
            "St.": "Street",
            "way": "Way",
            "trail": "Trail",
            "West.": "West",
            "W.": "West",
            "W": "West",
            "S.": "South",
            "S": "South",
            "E.": "East",
            "E": "East",
            "N.": "North",
            "N": "North"
            }
 

def update_phone(child_dict):
    ''' dictionary -> dictionary
    
    Replaces non-uniform phone number with the correct version 
    Called by shape_element()
    '''    
    if child_dict['key'] == 'phone':
        m = phone_type_re.search(child_dict['value'])
        if m:
            phone_o  = m.group() 

            result = re.sub('[+ ()-]', '', phone_o)
            phone_n = '('+result[-10:-7]+') '+result[-7:-4]+'-'+result[-4:]   
            child_dict['value'] = phone_n
            
    return  child_dict       

def update_name(name, mapping):
    ''' string, mapping dictionary -> string
    
    Replaces problematic part of the street name with correct version 
    Called by shape_element()
    '''
    keys = mapping.keys()
    name_list = name.split(' ')
    
    for key in keys:
        if key in name_list:
            name = name.replace(key, mapping[key])    
  
    return name


def update_tag_node(child, element, child_id, problem_chars=PROBLEMCHARS) :
    ''' element object , element object, string, RE pattern -> dictionary
    
    Loops through secondary node 'tag', adds 'type' attribute, assigns values to attributes.
    Called by shape_element()
    '''    

    # mapping the secondary node attribute keys
    convert = {'id': 'id',
                'k': 'key',
                'v': 'value',
                'type': "regular"} 

    if element.tag == 'node':
        tag_fields  = NODE_TAGS_FIELDS
    elif  element.tag == 'way':  
        tag_fields  = WAY_TAGS_FIELDS

    # innitial child node dictionary    
    child_dict = {'id': child_id,
                'key': '',
                'value': '',
                'type': 'regular'}
            
    for key, value in child.items():

        # performing the element shaping for atribute K
        if key == 'k': 

            # if the tag "k" value contains problematic characters, the tag should be ignored
            key_problem = problem_chars.search(value)
            if key_problem == None:

                # dictionary should contain only listed fields from the secondary tag attributes:
                if convert[key] in tag_fields:

                    # if the tag "k" value contains a ":" the characters before the ":" should be set as the tag type
                    # and characters after the ":" should be set as the tag key
                    key_value = LOWER_COLON.search(value)
                    if key_value != None:
                        colon_index  = key_value.group().find(':')

                        child_dict['type'] = value[:colon_index]
                        child_dict['key'] = value[colon_index+1:]
                    else:
                        child_dict['key'] = value  

        # fixing the steet names if needed  
        if key == 'v':
            value = update_name(value,mapping)

        # adding the atribute key:value pair to the node dictionary
        child_dict['value'] = value     
        
    return child_dict       


        

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS):
    '''Element object, list, list, re_patern, string -> dictionery

    Clean and shape node or way XML element  to Python dict
    Calls update_name(name, mapping) function
    '''

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    # Cleaning and shaping node element /points in space/   
    if element.tag == 'node':

        # looping the top level elements 'node' and adding attribute values to node_attribs dictionary
        for key, value in element.attrib.items():
            if key in node_attr_fields:
                node_attribs[key] = value

        child_id =   node_attribs['id'] 

        for child in  element:

            # re-shaping the 'tag' secondary node atributes and adding values to the child_dict  dictionary
            child_dict = update_tag_node(child,element,child_id)

            #updating the phone   
            child_dict = update_phone(child_dict)    
            tags.append(child_dict)

        return {'node': node_attribs, 'node_tags': tags}


    # Cleaning and shaping way element /linear features and area boundaries/ 
    elif element.tag == 'way':
        # 'nd' node counter
        position = 0

         # looping the top level elements 'way' and adding attribute values to way_attribs dictionary
        for key, value in element.attrib.items():
          
            if key in WAY_FIELDS:
                way_attribs[key] = value
          
        child_id =   way_attribs['id']  

        # looping the secondary level elements /tag, nd/of 'way' and adding data to tags list         
        for child in  element:

            if child.tag == 'tag':
                # re-shaping the 'tag' secondary node atributes and adding values to the child_dict  dictionary
                child_dict = update_tag_node(child,element,child_id)

                # updating the phone
                child_dict = update_phone(child_dict)

                tags.append(child_dict)

            elif child.tag == 'nd':
                # initial dictionary (attribute: value) of the secondary level element
                child_dict = {'id': way_attribs['id'],
                            'node_id': 0,
                            'position': position}
            
                for key, value in child.items():
                    child_dict['node_id'] = value
                    child_dict['position'] = position
                position += 1  

                way_nodes.append(child_dict)
  
     
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )

class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
