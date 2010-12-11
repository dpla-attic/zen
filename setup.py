#!/usr/bin/env python

from distutils.core import setup

execfile('lib/version.py')

setup(name = "zen",
      version = __version__,
      description="Zepheira's private data services components",
      author='Zepheira',
      author_email='info@zepheira.com',
      url='http://freemix.it',
      package_dir={'zen': 'lib', 'geopy': 'thirdparty/geopy_export/geopy',
                     '': 'thirdparty',
                    },
      packages=['zen', 'zen.akamod', 'geopy', 'geopy.geocoders', 'geopy.parsers'],
      py_modules = ['diff_match_patch', 'y_serial_v060', 'pagerank'],
      scripts=['sign_rulesheet', 'load_geonames', 'wikibootstrap'],
      #install_requires=["amara", "akara"],
      #package_data={'akara': ["akara.conf"]},
      )

