import simplejson

#Declare transform services
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
      u'name': U(bio[u'poet:name'])strip(),
      u'born': U(parsedate(U(bio[u'poet:born']))),
      u'died': U(parsedate(U(bio[u'poet:died']))),
      u'images': obj_urls(bio[u'poet:image']),
      u'wikipedia': link_urls(bio[u'poet:wikipedia']),
      u'description': U(resource.section(u'About')),
    }
    return obj

#Used to serve normal HTTP GET requests for the default representation of this resource
@handles('GET')
def get_artifact(resource):
    return simplejson.dumps(objectify(resource), indent=4)

#Used to serve requests for a collection of resources, in raw form
@handles('collect', 'raw/pydict')
def collect_artifacts(resources):
    return simplejson.dumps([objectify(resource) for resource in resources], indent=4)

#Used to process HTTP PUT requests to update this resource
@handles('PUT')
def put_artifact(resource_type, body):
    data = simplejson.loads(body)
    #e.g. "id" : "http://potlach.org/2008/02/whitart/whitart/7"
    return ARTIFACT_PAGE_TEMPLATE.substitute(data)


ARTIFACT_PAGE_TEMPLATE = Template(u'''\
= artifact:metadata =

 Medium: $medium
 Creator: $creator
 Label: $label
 Date: $date
 Thimage: {{$thimage}}
 Image: {{$image}}

= akara:metadata =
##Here generic metadata at the Zen/Akara level

 akara:type:: [[poetpaedia/collection]]
''')

