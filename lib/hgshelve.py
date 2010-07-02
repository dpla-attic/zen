# -*- encoding: utf-8 -*-
"""
Shelve with mercurial backend

(c) 2008-2009 Yury Yurevich, Alexander Solovyov
"""
# Inspired by gitshelve, but disappointed also
# see also:
# http://www.newartisans.com/blog_files/git.versioned.data.store.php
# http://twistedmatrix.com/trac/browser/trunk/twisted/persisted/dirdbm.py

import UserDict
import os, re, hashlib

import simplejson
from mercurial import localrepo, repo, ui, node, cmdutil

class HgShelve(UserDict.DictMixin):
    """
    This class implements a Python "shelf" using a version control within a Hg
    repository. There is no "writeback" argument, meaning changes are only
    written upon calling close or sync.
    """
    _keys = None
    _pending_keys = None
    hg_book_prefix = 'hgbook'
    hg_book_re = None

    def __init__(self, repopath):
        self.ui = ui.ui(quiet=True, interactive=False)
        self.repopath = os.path.abspath(repopath)
        self.repo = self.open_or_create_repo(self.repopath)
        if self.hg_book_re is None:
            self.hg_book_re = re.compile('^%s-(.+)-(.{40})$' % self.hg_book_prefix)
        self._keys = self.get_persisted_objects_keys()

    def open_or_create_repo(self, repopath):
        """
        Open existing repo, or create it otherwise
        """
        if os.path.isdir(repopath):
            try:
                r = localrepo.localrepository(self.ui, repopath)
            except repo.RepoError:
                # dir is not an hg repo, we must init it
                r = localrepo.localrepository(self.ui, repopath, create=1)
        else:
            os.makedirs(repopath)
            r = localrepo.localrepository(self.ui, repopath, create=1)
        return r

    def get_persisted_objects_keys(self):
        keys = []
        for fn in self.repo['tip']:
            if self.hg_book_re.match(fn):
                keys.append(self.get_key_from_fn(fn))
        return keys

    def get_key_from_fn(self, fn):
        m = self.hg_book_re.match(fn)
        if not m:
            raise ValueError("File %s doesn't seem to be hg book" % fn)
        key, keyhash = m.groups()
        if keyhash != hashlib.sha1(key).hexdigest():
            raise ValueError(
                'Filename %s is possibly corrupted (hash summm is not matched) '
                % fn)
        return key

    def get_fn_from_key(self, key):
        key = str(key)
        if '/' in key:
            raise ValueError("Hmmm, slash is not good ;)")
        return "%s-%s-%s" % (self.hg_book_prefix, key, sha.new(key).hexdigest())

    def get_raw_data(self, key, rev=None):
        if key not in self.keys():
            raise KeyError("Key %r is not found in hg shelf" % key)
        ctx = self.repo.changectx(rev)
        return ctx.filectx(self.get_fn_from_key(key)).data()

    def get_data(self, key, rev=None):
        return simplejson.loads(self.get_raw_data(key, rev), encoding='utf-8')

    def keys(self):
        if not self._keys:
            self._keys = self.get_persisted_objects_keys()
        return self._keys

    def __len__(self):
        return len(self.keys())

    def has_key(self, key):
        return key in self

    def __contains__(self, key):
        return key in self.keys()

    def get(self, key, default=None):
        if key not in self._keys:
            return default
        else:
            return self.get_data(key)

    def __getitem__(self, key):
        if self._pending_keys and key in self._pending_keys:
            raise KeyError("Data for key %r is not committed yet" % key)
        return self.get_data(key)

    def __setitem__(self, key, value):
        fn = self.get_fn_from_key(key)
        fh = file(os.path.join(self.repopath, fn), 'w')
        fh.write(simplejson.dumps(value, encoding='utf-8'))
        fh.close()
        if self._pending_keys is None:
            self._pending_keys = []
        # will not add key as pending if value is the same
        if key in self._keys and value == self.get_data(key):
            return

        if key not in self._pending_keys:
            self._pending_keys.append(key)

    def __delitem__(self, key):
        os.remove(os.path.join(self.repopath, get_fn_from_key(key)))
        if self._pending_keys is None:
            self._pending_keys = []
        if key not in self._pending_keys:
            self._pending_keys.append(key)

    def commit(self, message='hgshelve auto commit', key=None):
        """
        Commit unsynchronized data to disk.
        Arguments::

         - message: mercurial's changeset message
         - key: supply to sync only one key
        """
        commited = False
        rev = None
        files_to_add = []
        files_to_remove = []
        files_to_commit = []
        if not self._pending_keys:
            # nothing to commit
            return None
        # first of all, add absent data and clean removed
        if key is None:
            # will commit all keys
            pending_keys = self._pending_keys
        else:
            if key not in self._pending_keys:
                # key isn't changed
                return None
            else:
                pending_keys = [key]
        for key in pending_keys:
            fn = self.get_fn_from_key(key)
            files_to_commit.append(fn)
            if key in self.keys():
                if not os.path.exists(os.path.join(self.repopath, fn)):
                    # file removed
                    files_to_remove.append(fn)
            else:
                # file added
                files_to_add.append(fn)
        # hg add
        if files_to_add:
            self.repo.add(files_to_add)
        # hg forget
        if files_to_remove:
            self.repo.forget(files_to_remove)
        # ---- hg commit
        if files_to_commit:
            rev = self.repo.commit(files_to_commit, message)
            commited = True
        # clean pending keys
        for key in pending_keys:
            self._pending_keys.remove(key)
        if commited:
            # reread keys
            self._keys = self.get_persisted_objects_keys()
            return node.hex(rev)

    def sync(self):
        """
        Sync changes to disk
        """
        self.commit()

def open(repository_path):
    return HgShelve(repository_path)
