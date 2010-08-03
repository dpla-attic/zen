#See also: 


#def fixdate(d):
    #return u"%s-%s-%sT%s:%s:%s"%(d[0:4], d[4:6], d[6:8], d[8:10], d[10:12], d[12:14])
#    return u"%s-%s-%s"%(d[0:4], d[4:6], d[6:8])

def webfeed(body):
    import feedparser
    #Abstracted from Akara demo/modules/atomtools.py
    feed = feedparser.parse(body)
    
    def process_entry(e):
        from akara import logger; logger.info('webfeed entry: ' + repr(dict(e)))
        data = {
            u'id': e.link,
            u'label': e.link,
            u'title': e.title,
            u'link': e.link,
            u'updated': e.updated,
        }
        #Optional bits
        if 'content' in e:
            data[u'content'] = e.content
        if 'description' in e:
            data[u'description'] = e.description
        if 'author_detail' in e:
            data[u'author_name'] = e.author_detail.name
        return data

    return [ process_entry(e) for e in feed.entries ] if feed.entries else None

