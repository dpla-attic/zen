import sys
import logging
from nose.tools import raises

from amara.thirdparty import json

from zen import ejsonify

#logging.basicConfig(level=logging.DEBUG)


def test_pull_ejson_by_patterns1():
    expected = {u'items': [{'date': u'2009', u'label': u'_1', u'id': u'_1', 'format': u'audio'}, {'date': u'2007', u'label': u'_2', u'id': u'_2', 'format': u'audio'}, {'date': u'1997', u'label': u'_3', u'id': u'_3', 'format': u'language material -- serial'}]}
    patterns = [(('docs',), {'date': ('dpla.date',), 'format': ('dpla.format', 0)})]
    items = ejsonify.pull_ejson_by_patterns(json.loads(DPLA_TEST), patterns)
    assert items == expected, items
    return


def test_pull_ejson_by_patterns2():
    patterns = [(('spam',), {'date': ('dpla.date',), 'format': ('dpla.format', 0)})]
    items = ejsonify.pull_ejson_by_patterns(json.loads(DPLA_TEST), patterns)
    assert items == {u'items': []}, items
    return


def test_pull_ejson_by_patterns3():
    expected = {u'items': [{'date': u'2009', u'label': u'_1', 'format': [u'audio', u'mp3'], u'id': u'_1', 'creator': [u'Susan Jane Gilman']}, {'date': u'2007', u'label': u'_2', 'format': [u'audio', u'mp3'], u'id': u'_2', 'creator': [u'Linda Kulman']}, {'date': u'1997', u'label': u'_3', 'format': u'language material -- serial', u'id': u'_3', 'creator': [u"B'nai B'rith. Albert Einstein Lodge No. 5020"]}]}
    patterns = [(('docs',), {'date': ('dpla.date',), 'format': ('dpla.format',), 'creator': ('dpla.creator',)})]
    items = ejsonify.pull_ejson_by_patterns(json.loads(DPLA_TEST), patterns)
    assert items == expected, items
    return


def test_pull_ejson_by_patterns4():
    expected = {u'items': [{'date': u'2009', 'bogon': u'spam', u'label': u'_1', u'id': u'_1', 'format': u'audio'}, {'date': u'2007', u'label': u'_2', u'id': u'_2', 'format': u'audio'}, {'date': u'1997', '710a': u"B'nai B'rith.", u'label': u'_3', u'id': u'_3', 'format': u'language material -- serial'}]}
    patterns = [[["docs"], {"date": ["dpla.date"], "format": ["dpla.format", 0], "bogon": ["dpla.bogon"], "710a": ["710a"]}]]
    DPLA_TEST_PARSED = json.loads(DPLA_TEST)
    DPLA_TEST_PARSED[u"docs"][0][u"dpla.bogon"] = u"spam"
    items = ejsonify.pull_ejson_by_patterns(DPLA_TEST_PARSED, patterns)
    assert items == expected, items
    return


def test_pull_ejson_by_patterns5():
    expected = {u'items': [{'date': u'2009', u'label': u'_1', u'id': u'_1', 'format': u'audio'}, {'date': u'2007', u'label': u'_2', u'id': u'_2', 'format': u'audio'}, {'date': u'1997', u'label': u'_3', u'id': u'_3', 'format': u'language material -- serial'}]}
    patterns = [(('docs',), {'date': ('dpla.date',), 'format': ('dpla.format', 0)})]
    DPLA_TEST_PARSED = json.loads(DPLA_TEST)
    DPLA_TEST_PARSED[u"docs"][0][u"dpla.bogon"] = u"spam"
    items = ejsonify.pull_ejson_by_patterns(DPLA_TEST_PARSED, patterns)
    assert items == expected, items
    return


def test_pull_ejson_by_patterns6():
    #FIXME: Vet this last expected result
    expected = {u'items': [{u'dpla.date': u'2009', u'dpla.id': u'EF2485B2-0EF6-B47F-59EC-3F54E252AD79', u'dpla.bogon': u'spam', u'dpla.contributor': u'npr_org', u'dpla.dataset_id': u'npr_org_1312156800', u'dpla.language': u'English', u'dpla.contributor_record_id': u'2636', u'dpla.creator': [u'Susan Jane Gilman'], u'dpla.resource_type': u'item', u'label': u'_1', u'dpla.description': [u"<em>Time and Again</em> spans time, finds mystery, delves into Science-Fiction, grounds itself in Einstein's theories and ultimately, settles into romance fantasy.  So what's the problem?  Author Susan Jane Gilman explains her guilty addiction to this cult pop thriller."], u'dpla.format': [u'audio', u'mp3'], u'dpla.publisher': u'National Public Radio', u'dpla.title': u'<em>Time and Again</em> spans time, delves into Science Fiction, and ultimately becomes romance fantasy.', u'id': u'_1'}, {u'dpla.date': u'2007', u'dpla.id': u'159920DE-B8FE-2626-7252-ACF35F34E044', u'dpla.contributor': u'npr_org', u'dpla.dataset_id': u'npr_org_1312156800', u'dpla.language': u'English', u'dpla.contributor_record_id': u'1360', u'dpla.creator': [u'Linda Kulman'], u'dpla.resource_type': u'item', u'label': u'_2', u'dpla.description': [u"It was Albert Einstein's tendency to rebel that was the source of his great creativity, says Walter Isaacson in a new bestseller. Einstein's real genius was his ability to focus on mundane things that most people overlook."], u'dpla.format': [u'audio', u'mp3'], u'dpla.publisher': u'National Public Radio', u'dpla.title': u"A new biography argues that Einstein's tendency to rebel was the source of his creative genius.", u'id': u'_2'}, {u'dpla.date': u'1997', u'710a': u"B'nai B'rith.", u'710b': u'Albert Einstein Lodge No. 5020.', u'dpla.dataset_id': u'harvard_edu_1334336961', u'dpla.contributor': u'harvard_edu', u'988a': u'20040722', u'dpla.language': u'English', u'9060': u'MH', u'dpla.contributor_record_id': u'009416163', u'dpla.creator': [u"B'nai B'rith. Albert Einstein Lodge No. 5020"], u'dpla.id': u'BB275112-5EFB-A228-0E2B-D4E62FCC5208', u'dpla.resource_type': u'item', u'label': u'_3', u'dpla.format': u'language material -- serial', u'dpla.publisher': u"B'nai B'rith, Albert Einstein Lodge No. 5020,", u'260b': u"B'nai B'rith, Albert Einstein Lodge No. 5020,", u'dpla.title': u'Albert Einstein Lodge newsletter', u'245a': u'Albert Einstein Lodge newsletter.', u'id': u'_3', u'260a': u'Jerusalem :'}]}
    patterns = [(('docs',), None)]
    DPLA_TEST_PARSED = json.loads(DPLA_TEST)
    DPLA_TEST_PARSED[u"docs"][0][u"dpla.bogon"] = u"spam"
    items = ejsonify.pull_ejson_by_patterns(DPLA_TEST_PARSED, patterns)
    assert items == expected, items
    return


def test_analyze_for_nav1():
    expected = [(3, [u'docs'], [{u'dpla.date': u'2009', u'dpla.id': u'EF2485B2-0EF6-B47F-59EC-3F54E252AD79', u'dpla.contributor': u'npr_org', u'dpla.language': u'English', u'dpla.dataset_id': u'npr_org_1312156800', u'dpla.contributor_record_id': u'2636', u'dpla.creator': [u'Susan Jane Gilman'], u'dpla.resource_type': u'item', u'dpla.description': [u"<em>Time and Again</em> spans time, finds mystery, delves into Science-Fiction, grounds itself in Einstein's theories and ultimately, settles into romance fantasy.  So what's the problem?  Author Susan Jane Gilman explains her guilty addiction to this cult pop thriller."], u'dpla.format': [u'audio', u'mp3'], u'dpla.publisher': u'National Public Radio', u'dpla.title': u'<em>Time and Again</em> spans time, delves into Science Fiction, and ultimately becomes romance fantasy.'}, {u'dpla.date': u'2007', u'dpla.id': u'159920DE-B8FE-2626-7252-ACF35F34E044', u'dpla.contributor': u'npr_org', u'dpla.language': u'English', u'dpla.dataset_id': u'npr_org_1312156800', u'dpla.contributor_record_id': u'1360', u'dpla.creator': [u'Linda Kulman'], u'dpla.resource_type': u'item', u'dpla.description': [u"It was Albert Einstein's tendency to rebel that was the source of his great creativity, says Walter Isaacson in a new bestseller. Einstein's real genius was his ability to focus on mundane things that most people overlook."], u'dpla.format': [u'audio', u'mp3'], u'dpla.publisher': u'National Public Radio', u'dpla.title': u"A new biography argues that Einstein's tendency to rebel was the source of his creative genius."}, {u'dpla.date': u'1997', u'dpla.id': u'BB275112-5EFB-A228-0E2B-D4E62FCC5208', u'710b': u'Albert Einstein Lodge No. 5020.', u'dpla.dataset_id': u'harvard_edu_1334336961', u'dpla.contributor': u'harvard_edu', u'988a': u'20040722', u'dpla.language': u'English', u'9060': u'MH', u'dpla.contributor_record_id': u'009416163', u'dpla.creator': [u"B'nai B'rith. Albert Einstein Lodge No. 5020"], u'dpla.resource_type': u'item', u'dpla.format': u'language material -- serial', u'dpla.publisher': u"B'nai B'rith, Albert Einstein Lodge No. 5020,", u'260b': u"B'nai B'rith, Albert Einstein Lodge No. 5020,", u'dpla.title': u'Albert Einstein Lodge newsletter', u'710a': u"B'nai B'rith.", u'245a': u'Albert Einstein Lodge newsletter.', u'260a': u'Jerusalem :'}], {u'dpla.date': 3, u'dpla.id': 3, u'710b': 1, u'dpla.contributor': 3, u'dpla.language': 3, u'dpla.dataset_id': 3, u'988a': 1, u'dpla.contributor_record_id': 3, u'dpla.creator': 3, u'dpla.resource_type': 3, u'260a': 1, u'dpla.description': 2, u'dpla.format': 3, u'dpla.publisher': 3, u'9060': 1, u'dpla.title': 3, u'710a': 1, u'245a': 1, u'260b': 1}), (2, [u'docs', 1, u'dpla.format'], [u'audio', u'mp3'], {}), (2, [u'docs', 0, u'dpla.format'], [u'audio', u'mp3'], {}), (1, [u'docs', 2, u'dpla.creator'], [u"B'nai B'rith. Albert Einstein Lodge No. 5020"], {}), (1, [u'docs', 1, u'dpla.description'], [u"It was Albert Einstein's tendency to rebel that was the source of his great creativity, says Walter Isaacson in a new bestseller. Einstein's real genius was his ability to focus on mundane things that most people overlook."], {}), (1, [u'docs', 1, u'dpla.creator'], [u'Linda Kulman'], {}), (1, [u'docs', 0, u'dpla.description'], [u"<em>Time and Again</em> spans time, finds mystery, delves into Science-Fiction, grounds itself in Einstein's theories and ultimately, settles into romance fantasy.  So what's the problem?  Author Susan Jane Gilman explains her guilty addiction to this cult pop thriller."], {}), (1, [u'docs', 0, u'dpla.creator'], [u'Susan Jane Gilman'], {}), (0, [u'facets'], [], {}), (0, [u'facet_queries'], [], {}), (0, [u'errors'], [], {})]
    analysis = ejsonify.analyze_for_nav(json.loads(DPLA_TEST))
    expected_freq1 = {u'dpla.date': 3, u'dpla.id': 3, u'710b': 1, u'dpla.contributor': 3, u'dpla.language': 3, u'dpla.dataset_id': 3, u'988a': 1, u'dpla.contributor_record_id': 3, u'dpla.creator': 3, u'dpla.resource_type': 3, u'260a': 1, u'dpla.description': 2, u'dpla.format': 3, u'dpla.publisher': 3, u'9060': 1, u'dpla.title': 3, u'710a': 1, u'245a': 1, u'260b': 1}
    freq1 = analysis[0][-1] #Frequency dict is the last item pr list found in analysis
    assert freq1 == expected_freq1, freq1
    assert analysis == expected, analysis
    return


def test_analyze_for_nav2():
    expected = [(3, [u'docs'], [{u'dpla.date': u'2009', u'dpla.id': u'EF2485B2-0EF6-B47F-59EC-3F54E252AD79', u'dpla.bogon': u'spam', u'dpla.contributor': u'npr_org', u'dpla.language': u'English', u'dpla.dataset_id': u'npr_org_1312156800', u'dpla.contributor_record_id': u'2636', u'dpla.creator': [u'Susan Jane Gilman'], u'dpla.resource_type': u'item', u'dpla.description': [u"<em>Time and Again</em> spans time, finds mystery, delves into Science-Fiction, grounds itself in Einstein's theories and ultimately, settles into romance fantasy.  So what's the problem?  Author Susan Jane Gilman explains her guilty addiction to this cult pop thriller."], u'dpla.format': [u'audio', u'mp3'], u'dpla.publisher': u'National Public Radio', u'dpla.title': u'<em>Time and Again</em> spans time, delves into Science Fiction, and ultimately becomes romance fantasy.'}, {u'dpla.date': u'2007', u'dpla.id': u'159920DE-B8FE-2626-7252-ACF35F34E044', u'dpla.contributor': u'npr_org', u'dpla.language': u'English', u'dpla.dataset_id': u'npr_org_1312156800', u'dpla.contributor_record_id': u'1360', u'dpla.creator': [u'Linda Kulman'], u'dpla.resource_type': u'item', u'dpla.description': [u"It was Albert Einstein's tendency to rebel that was the source of his great creativity, says Walter Isaacson in a new bestseller. Einstein's real genius was his ability to focus on mundane things that most people overlook."], u'dpla.format': [u'audio', u'mp3'], u'dpla.publisher': u'National Public Radio', u'dpla.title': u"A new biography argues that Einstein's tendency to rebel was the source of his creative genius."}, {u'dpla.date': u'1997', u'dpla.id': u'BB275112-5EFB-A228-0E2B-D4E62FCC5208', u'710b': u'Albert Einstein Lodge No. 5020.', u'dpla.dataset_id': u'harvard_edu_1334336961', u'dpla.contributor': u'harvard_edu', u'988a': u'20040722', u'dpla.language': u'English', u'9060': u'MH', u'dpla.contributor_record_id': u'009416163', u'dpla.creator': [u"B'nai B'rith. Albert Einstein Lodge No. 5020"], u'dpla.resource_type': u'item', u'dpla.format': u'language material -- serial', u'dpla.publisher': u"B'nai B'rith, Albert Einstein Lodge No. 5020,", u'260b': u"B'nai B'rith, Albert Einstein Lodge No. 5020,", u'dpla.title': u'Albert Einstein Lodge newsletter', u'710a': u"B'nai B'rith.", u'245a': u'Albert Einstein Lodge newsletter.', u'260a': u'Jerusalem :'}], {u'dpla.date': 3, u'dpla.id': 3, u'dpla.bogon': 1, u'dpla.contributor': 3, u'dpla.language': 3, u'dpla.dataset_id': 3, u'988a': 1, u'dpla.contributor_record_id': 3, u'dpla.creator': 3, u'710b': 1, u'dpla.resource_type': 3, u'260a': 1, u'dpla.description': 2, u'dpla.format': 3, u'dpla.publisher': 3, u'9060': 1, u'dpla.title': 3, u'710a': 1, u'245a': 1, u'260b': 1}), (2, [u'docs', 1, u'dpla.format'], [u'audio', u'mp3'], {}), (2, [u'docs', 0, u'dpla.format'], [u'audio', u'mp3'], {}), (1, [u'docs', 2, u'dpla.creator'], [u"B'nai B'rith. Albert Einstein Lodge No. 5020"], {}), (1, [u'docs', 1, u'dpla.description'], [u"It was Albert Einstein's tendency to rebel that was the source of his great creativity, says Walter Isaacson in a new bestseller. Einstein's real genius was his ability to focus on mundane things that most people overlook."], {}), (1, [u'docs', 1, u'dpla.creator'], [u'Linda Kulman'], {}), (1, [u'docs', 0, u'dpla.description'], [u"<em>Time and Again</em> spans time, finds mystery, delves into Science-Fiction, grounds itself in Einstein's theories and ultimately, settles into romance fantasy.  So what's the problem?  Author Susan Jane Gilman explains her guilty addiction to this cult pop thriller."], {}), (1, [u'docs', 0, u'dpla.creator'], [u'Susan Jane Gilman'], {}), (0, [u'facets'], [], {}), (0, [u'facet_queries'], [], {}), (0, [u'errors'], [], {})]
    DPLA_TEST_PARSED = json.loads(DPLA_TEST)
    DPLA_TEST_PARSED[u"docs"][0][u"dpla.bogon"] = u"spam"
    analysis = ejsonify.analyze_for_nav(DPLA_TEST_PARSED)
    expected_freq1 = {u'dpla.date': 3, u'dpla.id': 3, u'dpla.bogon': 1, u'dpla.contributor': 3, u'dpla.language': 3, u'dpla.dataset_id': 3, u'988a': 1, u'dpla.contributor_record_id': 3, u'dpla.creator': 3, u'710b': 1, u'dpla.resource_type': 3, u'260a': 1, u'dpla.description': 2, u'dpla.format': 3, u'dpla.publisher': 3, u'9060': 1, u'dpla.title': 3, u'710a': 1, u'245a': 1, u'260b': 1}
    freq1 = analysis[0][-1] #Frequency dict is the last item pr list found in analysis
    assert freq1 == expected_freq1, freq1
    assert analysis == expected, analysis
    return


#Excerpted from http://jsonviewer.stack.hu/#http://api.dp.la/v0.03/item/?filter=dpla.keyword:einstein
DPLA_TEST = '''{
  "num_found": 4010,
  "start": "0",
  "limit": "25",
  "sort": "checkouts desc",
  "filter": "dpla.keyword:einstein",
  "docs": [
    {
      "dpla.date": "2009",
      "dpla.description": [
        "<em>Time and Again<\/em> spans time, finds mystery, delves into Science-Fiction, grounds itself in Einstein's theories and ultimately, settles into romance fantasy.  So what's the problem?  Author Susan Jane Gilman explains her guilty addiction to this cult pop thriller."
      ],
      "dpla.publisher": "National Public Radio",
      "dpla.format": [
        "audio",
        "mp3"
      ],
      "dpla.creator": [
        "Susan Jane Gilman"
      ],
      "dpla.title": "<em>Time and Again<\/em> spans time, delves into Science Fiction, and ultimately becomes romance fantasy.",
      "dpla.resource_type": "item",
      "dpla.id": "EF2485B2-0EF6-B47F-59EC-3F54E252AD79",
      "dpla.dataset_id": "npr_org_1312156800",
      "dpla.language": "English",
      "dpla.contributor": "npr_org",
      "dpla.contributor_record_id": "2636"
    },
    {
      "dpla.date": "2007",
      "dpla.description": [
        "It was Albert Einstein's tendency to rebel that was the source of his great creativity, says Walter Isaacson in a new bestseller. Einstein's real genius was his ability to focus on mundane things that most people overlook."
      ],
      "dpla.publisher": "National Public Radio",
      "dpla.format": [
        "audio",
        "mp3"
      ],
      "dpla.creator": [
        "Linda Kulman"
      ],
      "dpla.title": "A new biography argues that Einstein's tendency to rebel was the source of his creative genius.",
      "dpla.resource_type": "item",
      "dpla.id": "159920DE-B8FE-2626-7252-ACF35F34E044",
      "dpla.dataset_id": "npr_org_1312156800",
      "dpla.language": "English",
      "dpla.contributor": "npr_org",
      "dpla.contributor_record_id": "1360"
    },
    {
      "dpla.date": "1997",
      "245a": "Albert Einstein Lodge newsletter.",
      "dpla.creator": [
        "B'nai B'rith. Albert Einstein Lodge No. 5020"
      ],
      "dpla.id": "BB275112-5EFB-A228-0E2B-D4E62FCC5208",
      "dpla.language": "English",
      "9060": "MH",
      "dpla.contributor_record_id": "009416163",
      "988a": "20040722",
      "dpla.publisher": "B'nai B'rith, Albert Einstein Lodge No. 5020,",
      "dpla.title": "Albert Einstein Lodge newsletter",
      "dpla.resource_type": "item",
      "dpla.format": "language material -- serial",
      "260a": "Jerusalem :",
      "710b": "Albert Einstein Lodge No. 5020.",
      "dpla.dataset_id": "harvard_edu_1334336961",
      "260b": "B'nai B'rith, Albert Einstein Lodge No. 5020,",
      "dpla.contributor": "harvard_edu",
      "710a": "B'nai B'rith."
    }
  ],
  "facets": [
    
  ],
  "facet_queries": [
    
  ],
  "errors": [
    
  ]
}
'''



