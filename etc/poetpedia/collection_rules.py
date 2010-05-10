from string import Template
import simplejson
from zenlib.moinmodel import linkify


#Declare transform services
strip = service(u'http://purl.org/xml3k/akara/builtins/string/strip')
parsedate = service(u'http://purl.org/com/zepheira/zen/temporal/parse-date')
#extract_tags = service(u'http://purl.org/com/zepheira/zen/util/extract-tags')

#Used to serve requests for a raw Python dictionary
@handles('GET', 'raw/pydict')
def objectify(resource):
    #Metadata
    info = resource.definition_section(u'collection:metadata')
    metadata = {
        u'name': strip(U(info[u'collection:name'])),
        u'description': U(resource.section(u'collection:description')),
        u'category': u'collection',
        u'tags': extract_tags(U(info[u'collection:tags'])),
        u'owner': strip(U(info[u'collection:owner'])),
        u'source':strip(U(info[u'collection:source'])),
        u'last-modified': U(parsedate(U(bio[u'collection:last-modified']))),
    }
    #Data extraction
    items = resource.list_section(u'collection:items')
    resources = [ R(resource.absolute_wrap(U(link))) for link in items ]
    data = resources[0].get_proxy('collect', 'raw/pydict')(resources) if resources else []
    return {u'meta': meta, u'data': data}

#Used to serve normal HTTP GET requests for the default representation of this resource
@handles('GET')
def get_collection(resource):
    return simplejson.dumps(objectify(resource))

#Used to process HTTP PUT requests to update this resource
@handles('PUT')
def put_collection(resource_type, body):
    data = simplejson.loads(body)
    items = u'\n'.join([ u' * ' linkify(item, resource_type.wrapped_base) for item in data[u'items'] ])
    return COLLECTION_PAGE_TEMPLATE.substitute(locals())


COLLECTION_PAGE_TEMPLATE = Template(u'''\
= collection:items =

$items

= akara:metadata =

 akara:type:: [[poetpaedia/collection]]
''')

