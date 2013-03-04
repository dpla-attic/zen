#zen.ejsonify

#Tools for coverting other data formats to Exhibit JSON
#The is_* functions are for checkign data format.
#These return boolean, and also, through the output param, possible
#Outputs which were produced in the process of checking which we
#Don't want to have to reproduce in the process of consumption
#Or which are problematic to reproduce, e.g. if the input comes from a stream

import logging

from amara.thirdparty import json

def is_json(data, output=None):
    '''
    Attempt to load the given data; return True if it's JSON, and put the resulting object
    in the output placeholder.  If it's not JSON, return False
    '''
    try:
        obj = json.loads(data)
        if output is not None: output.append(obj)
    except ValueError, e:
        return False
    return True


def pull_ejson_by_patterns(obj, patterns):
    '''
    Extract data JSON from an object based on XML-XPath-like patterns provided.

    Each pattern is a tuple, of which the first item is the locator,
    giving the root pattern for extracted items.  The second is a mapping
    giving the keys for the result, and for each the source pattern.  e.g.:

    ('docs',), {'date': ('dpla.date',), 'format': ('dpla.format', 0)}

    '''
    items = []

    #def process_pattern()
    for root, iteminfo in patterns:
        cursor = obj
        #First navigate the "cursor" to refer to the desired root container
        for pathcomp in root:
            if isinstance(pathcomp, basestring) or isinstance(pathcomp, int):
                if isinstance(pathcomp, str): pathcomp = pathcomp.decode('utf-8')
                try:
                    cursor = cursor[pathcomp]
                except (TypeError, KeyError):
                    cursor = None
        #Now iterate over the container, if found
        if cursor:
            for contained in cursor:
                item = {}
                for key, path in iteminfo.items():
                    subcursor = contained
                    for pathcomp in path:
                        #logging.debug(str((pathcomp, subcursor)))
                        if isinstance(pathcomp, basestring) or isinstance(pathcomp, int):
                            if isinstance(pathcomp, str): pathcomp = pathcomp.decode('utf-8')
                            subcursor = subcursor[pathcomp]
                            if isinstance(subcursor, unicode):
                                #If we find a string, just abort the search for lower structures
                                break
                    item[key] = subcursor
                items.append(item)

    return items


def analyze_for_nav(data, sample_max=3):
    '''
    Analyze data from JSON and generate:

     * A list of viable arrays in order of length
     * Per array:
      * The array JSON "XPath"
      * The array length
      * A limited set of items for each array if the count exceeds some N
      * A list of all properties used in the items for each array
        * Where each property has the property name and the count of its use

    Assume everything is a dict, a list or a scalar, which would be the
    case the source is indeed JSON
    '''
    arrays = []
    path = []
    def handle_dict(d, path):
        for k, v in d.iteritems():
            if isinstance(v, list):
                handle_list(v, path + [k])
            elif isinstance(v, dict):
                handle_dict(v, path + [k])
    def handle_list(l, path):
        for count, i in enumerate(l):
            if isinstance(i, list):
                handle_list(i, path + [count])
            elif isinstance(i, dict):
                handle_dict(i, path + [count])
        #Each list is also an output item
        def freq_dict(l):
            fd = {}
            for li in l:
                if isinstance(li, dict):
                    for k in li:
                        if k in fd:
                            fd[k] += 1
                        else:
                            fd[k] = 1
            return fd
        arrays.append((len(l), path, l[:sample_max], freq_dict(l)))
    if isinstance(data, list):
        handle_list(data, path)
    elif isinstance(data, dict):
        handle_dict(data, path)
    return sorted(arrays, reverse=True)

