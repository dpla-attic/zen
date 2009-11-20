'''

Outline of MODS elements:
 * http://www.loc.gov/standards/mods/mods-outline.html#identifier

MODS Schemata: 
 * http://www.loc.gov/standards/mods/mods-schemas.html

MODS examples:
 * http://www.loc.gov/standards/mods/v3/mods-userguide-examples.html
 * http://www.scripps.edu/~cdputnam/software/bibutils/mods_intro.html

'''

from itertools import groupby
from operator import itemgetter

from amara.xpath import datatypes
from amara import bindery
from amara.bindery.model import *
from amara.bindery.util import dispatcher, node_handler

MODS_MODEL_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<modsCollection xmlns="http://www.loc.gov/mods/v3"
  xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/xml3k/akara/xmlmodel">
<!--mods ID="ref1060-2004" ak:resource="@ID"-->
<mods ID="ref1060-2004" ak:resource="">
    <ak:rel name="'resource-type'" value="'biblio:item'"/>
    <titleInfo>
        <title ak:rel="">NetKernel Open Source Community</title>
    </titleInfo>
    <name ak:rel="constructedName" type="personal" ak:value="concat(namePart[@type='given'], namePart[@type='family'])">
        <namePart type="given">Uche</namePart>
        <namePart type="given">Gerald</namePart>
        <namePart type="family">Ogbuji</namePart>
        <role>
            <roleTerm authority="marcrelator" type="text" ak:rel="">author</roleTerm>
        </role>
        <displayForm ak:rel="">Uche Ogbuji</displayForm>
    </name>
    <originInfo>
        <dateIssued ak:rel="">2004</dateIssued>
        <dateCaptured point="start" encoding="iso8601" ak:rel="">20020702</dateCaptured>
        <issuance ak:rel="">2004</issuance>
        <publisher ak:rel="">X</publisher>
        <copyrightDate encoding="w3cdtf" ak:rel="">2003</copyrightDate>
   	   	<place>
  	  	  	<placeTerm type="text" ak:rel="">New York</placeTerm>
       	</place>
    </originInfo>
    <language>
      	<languageTerm authority="iso639-2b" ak:rel="">eng</languageTerm>
    </language>
  	<physicalDescription>
  	  	<internetMediaType eg:occurs="*" ak:rel="">text/html</internetMediaType>
        <digitalOrigin ak:rel="">reformatted digital</digitalOrigin>
        <note ak:rel="physicalDescriptionNote">100 f 6.3 tl</note>
     	<form authority="marcform" ak:rel="">print</form>
      	<extent ak:rel="">15 p.</extent>
  	</physicalDescription>
  	<abstract ak:rel="">Web site promoting the candidacy of Fran Ulmer</abstract>
   	<subject authority="lcsh">
  	  	<topic eg:occurs="*" ak:rel="">Gettysburg, Battle of, Gettysburg, Pa., 1863</topic>
  	  	<geographic eg:occurs="*" ak:rel="">Alaska</geographic>
   	   	<hierarchicalGeographic>
  	  	  	<country ak:rel="">United States</country>
  	  	  	<state ak:rel="">California</state>
  	  	  	<county ak:rel="">Inyo</county>
  	  	</hierarchicalGeographic>
  	</subject>
    <classification authority="lcc" ak:rel="">E475.53 .A42</classification>
    <typeOfResource ak:rel="">software, multimedia</typeOfResource>
    <genre authority="gmgpc" ak:rel="">Landscape photographs</genre>
    <identifier displayLabel="Cite key" type="citekey" ak:rel="">1060-2004</identifier>
    <location eg:occurs="*">
        <url displayLabel="Uche's home" usage="primary display" access="preview" ak:rel="">http://uche.ogbuji.net/</url>
    </location>
    <note type="system details" ak:rel="">http://example.org/</note>
   	<relatedItem type="host" eg:occurs="*">
   	    <!-- Note: Looks like just about any of the top-level elements can go here -->
  	  	<!--
  	  	<titleInfo>
  	  	  	<title ak:rel="relatedItemTitle">Election 2002 Web Archive</title>
  	  	</titleInfo>
  	  	<location>
  	  	  	<url ak:rel="'relatedItemUrl'">http://www.loc.gov/minerva/collect/elec2002/</url>
  	  	</location>
  	  	-->
  	</relatedItem>
  	<accessCondition ak:rel="">Personal, noncommercial use of this item is permitted in the United States of America. Please see http://digital.library.upenn.edu/women/ for other rights and restrictions that may apply to this resource.
    </accessCondition>
    <recordInfo>
      	<recordSource ak:rel="">University of Pennsylvania Digital Library</recordSource>
      	<recordOrigin ak:rel=""> MODS auto-converted from a simple Online Books Page metadata record. For details, see http://onlinebooks.library.upenn.edu/mods.html </recordOrigin>
      	<languageOfCataloging ak:rel="">
      	  	<languageTerm type="code" authority="iso639-2b">eng</languageTerm>
      	</languageOfCataloging>
      	<recordContentSource ak:rel="">Indiana University Digital Library Program</recordContentSource>
      	<recordCreationDate encoding="w3cdtf" ak:rel="">2004-09-09</recordCreationDate>
      	<recordIdentifier ak:rel="">archives/cushman/P07803</recordIdentifier>
    </recordInfo>
</mods>
</modsCollection>
'''

MODS_MODEL = examplotron_model(MODS_MODEL_XML)

def mods2json(body):
    doc = bindery.parse(body, model=MODS_MODEL)
    items = []
    for rid, triples in groupby(generate_metadata(doc), itemgetter(0)):
        item = {'id': rid, 'label': rid}
        for row in triples:
            item[row[1]] = datatypes.string(row[2])
        items.append(item)
        if 'topic' in item: item['topic'] = item['topic'].split(', ')
        #import sys; print >> sys.stderr, item.keys()
    return items
    mods_handler = mods_content_handlers(items)
    doc.modsCollection.xml_namespaces[u'm'] = MODS_NAMESPACE
    list(mods_handler.dispatch(doc.modsCollection))
    return items

#
class mods_content_handlers(dispatcher):
    def __init__(self, items):
        dispatcher.__init__(self)
        #We could also handle this with a pattern of "yield key, value" to be used by the caller to populate the items dict
        self.items = items
        return

    @node_handler(u'm:mods')
    def mods(self, node):
        #print >> sys.stderr, "GRIPPO", node.xml_children
        self.item = {}
        #Use list to consume the iterator of child dispatch
        try:
            self.item[u'id'] = self.item[u'label'] = node.ID
        #except AttributeError, KeyError:
        except:
            pass
        for child in node.xml_children:
            for chunk in self.dispatch(child):
                yield None
            #print >> sys.stderr, "GRIPPO", self.items[-1]
        self.items.append(self.item)
        #list(chain(*imap(self.dispatch, node.xml_children)))

    @node_handler(u'm:titleInfo') #priority=10
    #http://www.loc.gov/standards/mods/mods-outline.html#titleInfo
    #Ignore: partNumber, partName, nonSor
    def titleInfo(self, node):
        self.item[u'title'] = unicode(node.title)
        try:
            self.item[u'subtitle'] = unicode(node.subtitle)
        except AttributeError:
            pass
        yield None

    @node_handler(u'm:name')
    #http://www.loc.gov/standards/mods/mods-outline.html#name
    #Ignore: partNumber, partName, nonSor
    def name(self, node):
        for namepart in node.namePart:
            self.item['name_parts'] = [ unicode(np) for np in node.namePart ]
        for roleterm in iter(node.role or []):
            #self.item[roleterm.authority + u'_' + unicode(roleterm) + u'_' + unicode(namepart.type)] = unicode(namepart)
            #self.item[unicode(roleterm) + u'_' + unicode(namepart.type)] = unicode(namepart)
            self.item['role'] = unicode(roleterm.roleTerm)
        yield None

    @node_handler(u'm:role')
    #http://www.loc.gov/standards/mods/mods-outline.html#name
    def role(self, node):
        for roleterm in node.roleTerm:
            #self.item[roleterm.authority + u'_' + unicode(roleterm) + u'_' + unicode(namepart.type)] = unicode(namepart)
            #self.item[unicode(roleterm) + u'_' + (roleterm.authority or u'')] = unicode(namepart)
            self.item['role'] = unicode(roleterm)
        yield None

    @node_handler(u'm:identifier')
    #http://www.loc.gov/standards/mods/mods-outline.html#identifier
    #Ignore: partNumber, partName, nonSor
    def identifier(self, node):
        self.item[unicode(node.type)] = unicode(node)
        yield None

    @node_handler(u'm:originInfo')
    def originInfo(self, node):
        if node.issuance:
            self.item[u'issuance'] = unicode(node.issuance)
        if node.publisher:
            self.item[u'publisher'] = unicode(node.publisher)
        for dc in iter(node.dateCaptured or []):
            try:
                #FIXME: seems dc might not gave a @point
                self.item[u'dateCaptured'+dc.point] = isobase(smart_parse_date(str(dc))) + UTC.name
            except TypeError:
                #If the augmented feedparser can't handle the date we'll get "argument must be 9-item sequence, not None"
                pass
        for dc in iter(node.dateIssued or []):
            try:
                self.item[u'dateIssued'] = isobase(smart_parse_date(str(dc))) + UTC.name
            except TypeError:
                #If the augmented feedparser can't handle the date we'll get "argument must be 9-item sequence, not None"
                pass
        yield None

    @node_handler(u'm:genre')
    def genre(self, node):
        self.item[u'genre'] = unicode(node)
        yield None

    @node_handler(u'm:language')
    def language(self, node):
        #FIXME: multi-lang case?
        self.item[u'language'] = unicode(node.languageTerm)
        yield None

    @node_handler(u'm:targetAudience')
    def targetAudience(self, node):
        self.item[u'targetAudience'] = unicode(node)
        yield None

    @node_handler(u'm:typeOfResource')
    def typeOfResource(self, node):
        self.item[u'typeOfResource'] = unicode(node)
        yield None

    @node_handler(u'm:abstract')
    def abstract(self, node):
        value = unicode(node).strip()
        if value: self.item[u'abstract'] = value
        yield None

    @node_handler(u'm:note')
    def note(self, node):
        #FIXME: Undo when Amara bug is fixed
        try:
            if getattr(node, "type") == u'system details':
                self.item[u'system_details'] = unicode(node)
                (scheme, netloc, path, query, fragment) = urlparse.urlsplit(self.item[u'system_details'])
                print >> sys.stderr, "Looking up:", netloc.encode('utf-8')
                domain_location = iplookup(netloc)
                if domain_location:
                    self.item['domain_latlong'] = domain_location
            else:
                self.item[u'note'] = unicode(node)
        except KeyError:
            self.item[u'note'] = unicode(node)
        yield None

    @node_handler(u'm:subject')
    def subject(self, node):
        if hasattr(node, 'topic'):
            self.item.setdefault(u'topics', []).extend([
                t.strip()
                for t in unicode(node.topic).split(u',')
                    if t.strip()
            ])
        if hasattr(node, 'geographic'):
            self.item.setdefault(u'places', []).extend([
                t.strip()
                for t in unicode(node.geographic).split(u',')
                    if t.strip()
            ])
        try:
            if hasattr(node, 'name'):
                self.item.setdefault(u'people', []).extend([
                    unicode(n).strip()
                    for n in node.name
                        if unicode(n).strip()
                ])
        except TypeError:
            pass
        yield None

    @node_handler(u'm:location')
    def location(self, node):
        #Beware.  displayLabel could have spaces etc.
        #self.item[unicode(node.displayLabel)] = unicode(node.url)
        self.item[u'location_url'] = unicode(node.url)
        if u'id' not in self.item:
            self.item[u'id'] = self.item[u'label'] = self.item[u'location_url']
        yield None

    @node_handler(u'm:relatedItem')
    def relatedItem(self, node):
        self.item[u'relatedItem'] = unicode(node.titleInfo.title)
        yield None

