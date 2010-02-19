import feedparser
import datetime

from amara.lib.date import timezone, UTC

def mods_convention_date(d):
    #Feedparser extension to parse a date format idiosyncratic to MODS
    if len(d) == 14:
        try:
            #FIXME: converting via tuple to datetime, then back to tuple.  Wasteful.
            return datetime.datetime(int(d[0:4]), int(d[4:6]), int(d[6:8]), int(d[8:10]), int(d[10:12]), int(d[12:]), 0, UTC).timetuple() #.utctimetuple()
        except ValueError:
            return None
    return None

#
def plain_year(d):
    if len(d) == 4:
        try:
            #FIXME: converting via tuple to datetime, then back to tuple.  Wasteful.
            return datetime.datetime(int(d[0:4])).timetuple()
        except ValueError:
            return None
    return None

feedparser.registerDateHandler(mods_convention_date)
feedparser.registerDateHandler(plain_year)

def smart_parse_date(date):
    parts = date.split('/')
    try:
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[0]), int(parts[1])).timetuple()
    except ValueError:
        pass
    try:
        dt = datetime.datetime(*feedparser._parse_date(date)[:7])
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception, e:
        dt = None
    return dt

