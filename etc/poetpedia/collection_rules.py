import simplejson

#Declare transform services
#request_resource = service(u'http://purl.org/com/zepheira/zen/moinmodel/request-resource')

#Used to serve requests for a raw Python dictionary
@handles('GET', 'raw/pydict')
def objectify(resource):
    #Data extraction
    items = resource.list_section(u'collection:items')
    resources = [ R(resource.absolute_wrap(U(link))) for link in items ]
    return resources[0].get_proxy('collect', 'raw/pydict')(resources) if resources else []

#Used to serve normal HTTP GET requests for the default representation of this resource
@handles('GET')
def get_collection(resource):
    return simplejson.dumps(objectify(resource))

