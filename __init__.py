# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ImproperlyConfigured

from shuup.apps import AppConfig


class ShuupMoreApiAppConfig(AppConfig):
    name = 'shuup_more_api'
    verbose_name = 'Shuup more API endpoints'
    label = 'shuup_more_api'
    required_installed_apps = (
        'shuup.api',
    )

    provides = {
        'api_populator': [
            'shuup_more_api.api:populate'
        ]
    }


default_app_config = 'shuup_more_api.ShuupMoreApiAppConfig'
