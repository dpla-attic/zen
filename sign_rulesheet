#!/usr/bin/env python

import sys, hashlib

secret = sys.argv[1]
rsheet = sys.argv[2]
#rulesheet = sys.stdin.read()
rulesheet = open(rsheet).read()

#FIXME: use / from akara.thirdparty import argparse
sys.stdout.write('#')
sys.stdout.write(hashlib.sha1(secret + rulesheet).hexdigest())
sys.stdout.write('\n')
sys.stdout.write(rulesheet)
