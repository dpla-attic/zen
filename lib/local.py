'''
The catalog of local services supplied with Zen
'''

from zen.services import register_service

#Local services
from zen.geo import geolookup

geolookup.serviceid = u'http://purl.org/com/zepheira/geo/geolookup'

register_service(geolookup)

from zen.temporal import smart_parse_date

smart_parse_date.serviceid = u'http://purl.org/com/zepheira/zen/temporal/parse-date'

register_service(smart_parse_date)

from zen.exhibit import prep

prep.serviceid = u'http://purl.org/com/zepheira/zen/exhibit/prep'

register_service(prep)

#Other built-ins
#This is really just a demo.  Silly to use in practice.  Just do spam.strip()
import string
string.strip.serviceid = u'http://purl.org/xml3k/akara/builtins/string/strip'

register_service(string.strip)

