# -- %< --

#Useful sources related to data & file type ID
# * http://www.garykessler.net/library/file_sigs.html - "This table of file signatures (aka "magic numbers") is a continuing work-in-progress...."
# * http://stackoverflow.com/questions/43580/how-to-find-the-mime-type-of-a-file-in-python
# * http://www.fileformat.info/ - "The Digital Rosetta Stone "
# * http://www.wotsit.org/ - "This site contains information on hundreds of different file types, data types, hardware interface details and all sorts of other useful programming information; algorithms, source code, specifications, etc."
# * re: python-magic http://gavinjnet.blogspot.com/2007/05/python-file-magic.html

import sys, urllib
from subprocess import *

# Requires python-magic <http://pypi.python.org/pypi/python-magic/0.1>
# >>> import magic
# >>> m = magic.Magic()
# >>> m.from_file("testdata/test.pdf")
# 'PDF document, version 1.2'
# >>> m.from_buffer(open("testdata/test.pdf").read(1024))
# 'PDF document, version 1.2'
# For MIME types
# >>> mime = magic.Magic(mime=True)
# >>> mime.from_file("testdata/test.pdf")
# 'application/pdf
'''
try:
    import magic
    def guess_mediatype(content):
        m = magic.Magic()
        pass
except ImportError:
    pass
'''

def guess_imt(body):
    '''
    Support function for freemix services.  Inital processing to guess media type of post body.
    '''
    #from magic import Magic
    #fileguesser = Magic(mime=True)
    cmdline = guess_imt.MAGIC_FILE_CMD
    process = Popen(cmdline, stdin=PIPE, stdout=PIPE, universal_newlines=True, shell=True)
    imt = "application/unknown"
    try:
        imt, perr = process.communicate(input=body)
        if not imt:
            #FIXME: L10N
            raise RuntimeError('Empty output from the command line.  Probably a failure.  Command line: "%s"'%cmdline)
            #raise ValueError('Empty output from the command line.  Probably a failure.  Command line: "%s"'%cmdline)
    except OSError:
        raise RuntimeError('Error upon file type sniff.  Command line: "%s"'%cmdline)
    #print >> sys.stderr, imt
    #imt might look like:
    # * foo.dat: text/plain; charset=us-ascii
    # * foo.dat: text/plain charset=us-ascii
    imt = imt.split(':')[-1].split(';')[0].split()[0].strip()
    #imt = fileguesser.from_buffer(body)
    return imt

guess_imt.MAGIC_FILE_CMD = 'file -I -'

