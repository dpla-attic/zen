#!/usr/bin/env python

import sys, hashlib

secret = sys.argv[1]
rsheet = sys.argv[2]
#rulesheet = sys.stdin.read()
rulesheet = open(rsheet).read()

print hashlib.sha1(secret + rulesheet).hexdigest()
sys.stdout.write(rulesheet)
