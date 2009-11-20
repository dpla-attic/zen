import datetime
import feedparser

# To be moved to amara lib
# Reuses some code from: http://seehuhn.de/blog/52
class timezone(datetime.tzinfo):
    def __init__(self, name="+0000"):
        self.name = name
        seconds = int(name[:-2])*3600+int(name[-2:])*60
        self.offset = datetime.timedelta(seconds=seconds)

    def utcoffset(self, dt):
        return self.offset

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return self.name


UTC = timezone()

def mods_convention_date(d):
    #Feedparser extension to parse a date format idiosyncratic to MODS
    if len(d) == 14:
        try:
            #FIXME: converting via tuple to datetime, then back to tuple.  Wasteful.
            return datetime.datetime(int(d[0:4]), int(d[4:6]), int(d[6:8]), int(d[8:10]), int(d[10:12]), int(d[12:]), UTC).timetuple() #.utctimetuple()
        except ValueError:
            return None
    return None

#
feedparser.registerDateHandler(mods_convention_date)

def smart_parse_date(date):
    parts = date.split('/')
    try:
        if len(parts) == 3:
            return datetime.date(int(parts[2]), int(parts[0]), int(parts[1])).timetuple()
    except ValueError:
        pass
    return datetime.datetime(*feedparser._parse_date(date)[:7])


