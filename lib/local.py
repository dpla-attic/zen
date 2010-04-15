'''
The catalog of local services supplied with Zen
'''

from zenlib import register_service

#Local services
from zenlib.geo import geolookup

geolookup.serviceid = u'http://purl.org/com/zepheira/geo/geolookup'

register_service(geolookup)

from zenlib.temporal import smart_parse_date

smart_parse_date.serviceid = u'http://purl.org/com/zepheira/zen/temporal/parse-date'

register_service(smart_parse_date)

from zenlib.exhibit import fixup

#Other built-ins
import string
string.strip.serviceid = u'http://purl.org/xml3k/akara/builtins/string/strip'

register_service(string.strip)

