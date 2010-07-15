import sys
from nose.tools import raises

from amara import bindery
from amara.test.xslt import filesource, stringsource

from zenlib import moinmodel

STRUCT1 = '''\
== Locations ==

=== Location ===
 Name:: !UAB Comprehensive Cancer Center
 Status:: Recruiting
 Location:: Birmingham, Alabama
 Zip:: 35294
 Country:: United States
==== Contact ====
 Last Name:: Clinical Trials Office - !UAB Comprehensive Cancer Center
 Phone:: 205-934-0309

=== Location ===
 Name:: Phoenix Children's Hospital
 Status:: Recruiting
 Location:: Phoenix, Arizona
 Zip:: 85016-7710
 Country:: United States
==== Contact ====
 Last Name:: Jessica L. Boklan
 Phone:: 602-546-0920
'''

STRUCT1_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<s1 title="xpage">
<s2 id="Locations" title="Locations">
  <p/>
  <s3 id="Location" title="Location">
    <gloss>
      <label>Name</label>
      <item>UAB Comprehensive Cancer Center 1</item>
      <label>Status</label>
      <item>Recruiting </item>
      <label>Location</label>
      <item>Birmingham, Alabama </item>
      <label>Zip</label>
      <item>35294 </item>
      <label>Country</label>
      <item>United States </item>
    </gloss>
    <p/>
    <s4 id="Contact" title="Contact">
      <gloss>
        <label>Last Name</label>
        <item>UAB Comprehensive Cancer Center </item>
        <label>Phone</label>
        <item>205-934-0309 </item>
      </gloss>
      <p/>
    </s4>
  </s3>
  <s3 id="Location" title="Location">
    <gloss>
      <label>Name</label>
      <item>Phoenix Children's Hospital </item>
      <label>Status</label>
      <item>Recruiting </item>
      <label>Location</label>
      <item>Phoenix, Arizona </item>
      <label>Zip</label>
      <item>85016-7710 </item>
      <label>Country</label>
      <item>United States </item>
    </gloss>
    <p/>
    <s4 id="Contact" title="Contact">
      <gloss>
        <label>Last Name</label>
        <item>Jessica L. Boklan </item>
        <label>Phone</label>
        <item>602-546-0920 </item>
      </gloss>
      <p/>
    </s4>
  </s3>
</s2>
</s1>
'''

EXPECTED1 = {u'xpage': {u'Locations':
    [{u'Location': [{u'Country': u'United States ',
       u'Location': u'Birmingham, Alabama ',
       u'Name': u'UAB Comprehensive Cancer Center 1',
       u'Status': u'Recruiting ',
       u'Zip': u'35294 '},
      {u'Contact': {u'Last Name': u'UAB Comprehensive Cancer Center ',
            u'Phone': u'205-934-0309 '}}]},
      {u'Location': [{u'Country': u'United States ',
            u'Location': u'Phoenix, Arizona ',
            u'Name': u"Phoenix Children's Hospital ",
            u'Status': u'Recruiting ',
            u'Zip': u'85016-7710 '},
      {u'Contact': {u'Last Name': u'Jessica L. Boklan ',
            u'Phone': u'602-546-0920 '}}]}]}}

def test_simple_struct1():
    doc = bindery.parse(STRUCT1_XML)
    result = moinmodel.simple_struct(doc)
    assert result == EXPECTED1, (result, EXPECTED1) # did not match
    #import pprint; pprint.pprint(result, stream=sys.stderr)
    return

    #assert iso_date is not None, reference_date  # could not be parsed
    #assert iso_date == reference_date, (iso_date, reference_date) # did not match

#locations = [ l_inner[u'Location'] for loc_list in EXPECTED1.values()[0][u'Locations'] for l_inner in loc_list[u'Location'] if u'Location' in l_inner]

