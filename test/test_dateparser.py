import re
import doctest

from zenlib import dateparser
from zenlib.dateparser import regex_patterns, to_iso8601

TEST_DATES = """
# Lines starting 'ISO:' contain an ISO date.  The tester does a
# round-trip test of the date, to make sure it matches, then uses the
# date as a reference date for the successive dates, until the next
# 'ISO:' line.

ISO: 2003-11-16

16 November 2003
16 Nov 2003
16 November 2003 AD
16 November 2003 CE


# This was one of Dave Woods test candidates.
# Fields are in day/month/year order.
# I do not support this because while it's
# possible to figure out that this date is
# for the 16th of November, it's not possible
# to figure out how to parse "01/02/2003".
# Suppose a data set contains both items.
# Should one be parsed as day/month/year
# and the other as month/day/year? 
#16/11/2003
#16-11-2003
#16-11-03
#16.11.2003

2003 November 16
2003Nov16
2003-Nov-16
2003-11-16

November 16, 2003
November 16 2003
Nov. 16, 2003
Nov 16, 2003
11/16/2003
11-16-2003
11.16.2003

## Skip this one as the syntax is too ambiguous
# Should this implement Y2K logic?
#11.16.03

20031116

ISO: 1970-08-02

2 August 1970
02 August 1970
2 Aug 1970
02 Aug 1970
02 August 1970 AD
2 August 1970 CE

1970 Aug 2
1970 Aug 02
1970Aug2
1970Aug02
1970-Aug-02
1970-08-02

August 2, 1970
August 02, 1970
August 2 1970
Aug. 2, 1970
Aug 2, 1970
08/02/1970
08-02-1970
08.02.1970

## Skip this one as the syntax is too ambiguous
# Should this implement Y2K logic?
#08.02.70

19700802


# Year is 3BC
ISO: -0002-03-31

31 March 3 BC
31 March 3 BCE
31 Mar 3 B.C.
31 Mar 3 BCE

March 31 3 B.C.
March 31, 3 B.C.
Mar 31, 3 B.C.
Mar 31 3 B.C.

# Just do the ISO round-trip testing

ISO: 1997
ISO: 1997-07
ISO: 1997-07-16

ISO: 1997-07-16T01:20+02:00
ISO: 1997-07-16T19:20:30+01:00
ISO: 1997-07-16T19:20:30.45+01:00

ISO: 1997-07-16T19:20
ISO: 1997-07-16T19:20:30
ISO: 1997-07-16T19:20:30.45

ISO: 1997-07-16T19:20-01:00
ISO: 1997-07-16T19:20:30-01:00
ISO: 1997-07-16T19:20:30.45-01:00

ISO: 1997-07-16T19:20Z
ISO: 1997-07-16T19:20:30Z
ISO: 1997-07-16T19:20:30.45Z

ISO: 1997
ISO: 1997-07
ISO: 1997-07-16

ISO: 0000-07-16T19:20+01:00
ISO: -0001-07-16T19:20:30+01:00
ISO: -0002-07-16T19:20:30.45+01:00

ISO: 9999-07-16T19:20
ISO: -9999-07-16T19:20:30

ISO: 1970-08

August 1970
August, 1970
Aug 1970
Aug, 1970

ISO: 2010-03

March 2010
March, 2010
Mar 2010
March, 2010
"""

def test_time_strings():
    reference_date = None
    for line in TEST_DATES.splitlines():
        if not line or line.startswith("#"):
            # Ignore blank lines and comments
            continue
        if line.startswith("ISO:"):
            # This is a new date reference.
            # Check that it's value and save for future comparisons
            _, reference_date = line.split()
            # Test for round-trip parsing
            iso_date = to_iso8601(reference_date)
            assert iso_date is not None, reference_date  # could not be parsed
            assert iso_date == reference_date, (iso_date, reference_date) # did not match
            print "New date:", reference_date
            continue

        print "Test", line
        date = to_iso8601(line)
        assert date == reference_date, (line, date, reference_date)


def test_ranges():
    # Test that the patterns work correctly against a set of valid and
    # invalid strings for that pattern.
    for name, valid, invalid in (
        ("DAY", "01 02 03 04 05 06 07 08 09".split() + map(str, range(1, 32)),
         "00 0 32 40 99".split()),
        ("DD", ["%02d" % x for x in range(1, 32)], "00 1 9 32 33 40 99".split()),
        ("MONTH", "1 2 3 4 5 6 7 8 9 10 11 12 01 02 03 04 05 06 07 08 09".split(),
         "0 00 13 A".split()),
        ("MM", "01 02 03 04 05 06 07 08 09 10 11 12".split(),
         "1 2 3 4 5 6 7 8 9 13".split()),
        ("YEAR", "0000 70 100 1970 2010 3001 9999".split(), "A100 A".split()),
        ("YYYY", "0000 0001 1970 2010 3001 9999".split(), "70 100 100A".split()),
        ("ISOYEAR", "0000 0001 1970 2010 3001 9999 -0001 -0002 9999 -9999".split(),
                     "70 100 100A A1970".split()),
        #("YY", "70 80 01 00 99".split(), "1 -2".split()),
        ("ERA?", "AD A.D. CE BC B.C. BCE".split(), "AC DC A.D B.C".split()),

        ("hh", ["%02d" % i for i in range(25)], "1 1 -1 25".split()),
        ("mm", ["%02d" % i for i in range(60)], "1 +1 -1 60".split()),
        ("ss", ["%02d" % i for i in range(60)], "1 +1 -1 60".split()),
        ("ss", ["%02d" % i for i in range(60)], "1 +1 -1 60".split()),
        ("ss.s", ["%02d.%d" % (i, i**2) for i in range(60)], "1.1 .1 1.A 00 01 60.0".split()),

        ):
        regex = regex_patterns[name]
        if regex.endswith("?"):
            regex = regex[:-1]
        pat = re.compile(regex)
        for term in valid:
            assert pat.match(term), (name, term)
        for term in invalid:
            assert not pat.match(term), (name, term)


def test_docstring():
    doctest.testmod(dateparser, verbose=True, raise_on_error=True)
