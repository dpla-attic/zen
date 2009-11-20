"""A alternate implementation of the persistent dict found in 
http://erezsh.wordpress.com/2009/05/24/filedict-a-persistent-dictionary-in-python/
"""

import sqlite3, UserDict, pickle

def key(k):
    return hash(k), pickle.dumps(k)

class persistentDict(UserDict.DictMixin):
    def __init__(self, filetable, d=None, **kwarg):
        if isinstance(filetable, tuple):
            filename, self._table = filetable
        else:
            filename = filetable
            self._table = 'dict'
        self._db = sqlite3.connect(filename)
        self._db.execute('create table if not exists %s (hash integer, key blob, value blob);' % self._table)
        self._db.execute('create index if not exists %s_index ON %s(hash);' % (self._table, self._table))
        self._db.commit()
        self.update(d, **kwarg)
    def __getitem__(self, k):
        v = self._db.execute('select value from %s where hash=? and key=?;' % self._table, key(k)).fetchone()
        if v:
            return pickle.loads(str(v[0]))
        raise KeyError, k
    def _setitem(self, (hkey, pkey), pval):
        if self._contains((hkey, pkey)):
            self._db.execute('update %s set value=? where hash=? and key=?' % self._table, (pval, hkey, pkey))
        else:
            self._db.execute('insert into %s values (?,?,?)' % self._table, (hkey, pkey, pval))
    def __setitem__(self, k, v):
        self._setitem(key(k), pickle.dumps(v))
        self._db.commit()
    def __delitem__(self, k):
        if self._db.execute('delete from %s where hash=? and key=?;' % self._table, key(k)).rowcount <=0:
            raise KeyError, k
        self._db.commit()
    def _contains(self, k):
        res, = self._db.execute('select count(*) from %s where hash=? and key=?;' % self._table, k)
        return res[0]>0
    def __contains__(self, k):
        return self._contains(key(k))
    def __iter__(self):
        for k,  in self._db.execute('select key from '+self._table):
            yield pickle.loads(str(k))
    def keys(self):
        return list(iter(self))
    def insert(self, seq):
        for k,v in seq:
            self._setitem(key(k), pickle.dumps(v))
        self._db.commit()


if __name__ == '__main__':
    d = persistentDict((r'c:\bortest\db.dat', 'new'), k1=1)
    d['k2'] = 1
    d['k2'] = 2
    try:
        del d['k3']
    except KeyError:
        print 'OK'
    print d.keys()
    del d['k1']
    d.insert((i, str(i)) for i in range(10000))
    try:
        print d['k4']
    except KeyError:
        print 'OK'