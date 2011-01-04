import latlong
import doctest
import time


def test_no_answers():
    lalo = latlong.latlong("geonames.sqlite3")
    assert lalo.using_city_state("Miami", "QQ") is None
    assert lalo.using_city_country_code("Miami-Youramai", "PR") is None

    assert lalo.using_city_country("Miami-Youramai", "Sweden") is None

    assert lalo.using_city_and_state_then_country("Miami-Youramai", "PR") is None
    assert lalo.using_city_and_country_then_state("Miami-Youramai", "PR") is None
    assert lalo.using_city("QWERTYUIOP") is None

def test_bad_country_code():
    lalo = latlong.latlong("geonames.sqlite3")
    try:
        lalo.using_city_country_code("Miami", "**")
        raise AssertionError
    except TypeError, s:
        assert "two-digit ISO country code" in str(s), str(s)
        assert "**" in str(s), str(s)

def test_docstrings():
    lalo = latlong.latlong("geonames.sqlite3")
    doctest.testmod(lalo, globs=dict(lalo=lalo),
                    verbose=True, raise_on_error=True)

    
def _time(f, *args):
    N = 10
    x = range(N)
    t1 = time.time()
    for _ in x:
        result = f(*args)
    return (time.time()-t1)/N, result


def test_city_state_timing():
    lalo = latlong.latlong("geonames.sqlite3")
    t1, ll1 = _time(lalo._get_lat_long, lalo.CITY_STATE_SQL,
                    dict(city_name="MIAMI", admin1_code="FL", country_code="US"))
    t2, ll2 = _time(lalo._get_lat_long, """
SELECT latitude, longitude
    FROM geoname
    WHERE (city_name = "MIAMI" AND admin1_code = "FL" and country_code = "US")
    ORDER BY population DESC
    limit 1
""", {})
    assert ll1 == ll2 == (u'25.7742658', u'-80.1936589'), (ll1, ll2)
    # The real search is more complicated, but not all that more complicated
    assert t1 < t2*1.2, (t1, t2)


def test_city_country_code_timing():
    lalo = latlong.latlong("geonames.sqlite3")

    t1, ll1 = _time(lalo._get_lat_long, lalo.CITY_COUNTRY_CODE_SQL,
                    dict(city_name="MIAMI", country_code="US"))
    t2, ll2 = _time(lalo._get_lat_long, """
SELECT latitude, longitude
    FROM geoname
    WHERE (city_name = "MIAMI" AND country_code = "US")
    ORDER BY population DESC
    limit 1
""", {})
    assert ll1 == ll2 == (u'25.7742658', u'-80.1936589'), (ll1, ll2)
    assert t1 < t2*1.2, (t1, t2)

def test_city_timing():
    lalo = latlong.latlong("geonames.sqlite3")

    t1, ll1 = _time(lalo._get_lat_long, lalo.CITY_SQL,
                    dict(city_name="MIAMI"))
                    
    t2, ll2 = _time(lalo._get_lat_long, """
SELECT latitude, longitude
    FROM geoname
    WHERE city_name = "MIAMI" OR city_asciiname = "MIAMI"
    ORDER BY population DESC
    limit 1
""", {})
    assert ll1 == ll2 == (u'25.7742658', u'-80.1936589'), (ll1, ll2)
    # For some reason, 'OR' searches take a lot longer than 'UNION's
    assert t1 < t2, (t1, t2)

if __name__ == "__main__":
    raise SystemExit("use nosetests to run these tests")
