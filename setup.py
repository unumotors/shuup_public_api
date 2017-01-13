#!/usr/bin/env python
from setuptools import find_packages, setup

setup(name='shuup_public_api',
      version='0.0.0',
      description='A shuup extension to provide a public API',
      author='unu GmbH',
      author_email='jonatan@unumotors.com',
      url='https://github.com/unumotors/shuup_public_api/',
      packages=find_packages(),
      install_requires=(
          'djangorestframework==3.5.3',
          'drf-extensions==0.3.1',
          'drf-nested-routers==0.11.1',
          'shuup==1.0.0')
      )
