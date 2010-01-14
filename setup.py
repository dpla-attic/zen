#!/usr/bin/env python

from distutils.core import setup

setup(name = "zenlib",
      version = "0.8.5",
      description="Zepheira's private data services components",
      author='Zepheira',
      author_email='info@zepheira.com',
      url='http://freemix.it',
      package_dir={'zenlib': 'lib', 'geopy': 'geopy_export/geopy'},
      packages=['zenlib', 'geopy'],
      #package_data={'akara': ["akara.conf"]},
      )

