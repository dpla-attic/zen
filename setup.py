#!/usr/bin/env python

from distutils.core import setup

setup(name = "zenlib",
      version = "0.8.0",
      description="Zepheira's private data services components",
      author='Zepheira',
      author_email='info@zepheira.com',
      url='http://freemix.it',
      package_dir={'zenlib': 'lib'},
      packages=['zenlib'],
      #package_data={'akara': ["akara.conf"]},
      )

