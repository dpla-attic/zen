import simplejson

#Declare transform services
strip = service(u'http://purl.org/xml3k/akara/builtins/string/strip')
parsedate = service(u'http://purl.org/com/zepheira/zen/temporal/parse-date')
obj_urls = service(u'http://purl.org/com/zepheira/zen/moinmodel/get-obj-urls')
link_urls = service(u'http://purl.org/com/zepheira/zen/moinmodel/get-link-urls')

#Used to serve requests for a raw Python dictionary
@handles('GET', 'raw/pydict')
def objectify(resource):
    #Data extraction
    bio = resource.definition_section(u'poet:bio')

    #Output
    obj = {
      u'id': resource.rest_uri,
      u'name': strip(U(bio[u'poet:name'])),
      u'born': U(parsedate(U(bio[u'poet:born']))),
      u'died': U(parsedate(U(bio[u'poet:died']))),
      u'images': obj_urls(bio[u'poet:image']),
      u'wikipedia': link_urls(bio[u'poet:wikipedia']),
      u'description': U(resource.section(u'About')),
    }
    return obj

#Used to serve normal HTTP GET requests for the default representation of this resource
@handles('GET')
def get_poet(resource):
    return simplejson.dumps(objectify(resource))

#Used to serve requests for a collection of resources, in raw form
@handles('collect', 'raw/pydict')
def collect_poets(resources):
    return simplejson.dumps([objectify(resource) for resource in resources])

