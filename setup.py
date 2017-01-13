#!/usr/bin/env python

from distutils.core import setup

setup(name='shuup_public_api',
      version='0.0',
      description='A shuup extension to provide a public API',
      author='unu GmbH',
      author_email='jonatan@unumotors.com',
      url='https://github.com/unumotors/shuup_public_api/',
      packages=[
            'shuup_public_api',
            'shuup_public_api.api',
            'shuup_public_api.api.basket',
            'shuup_public_api.api.order',
            'shuup_public_api.api.payment_method',
            'shuup_public_api.api.product',
            'shuup_public_api.api.shipping_method',
            'shuup_public_api.api.shop',
            'shuup_public_api.api.tax',
            'shuup_public_api.common',
      ],
      )
