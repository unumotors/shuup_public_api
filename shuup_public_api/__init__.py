# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.apps import AppConfig


class ShuupGuestApiAppConfig(AppConfig):
    name = 'shuup_public_api'
    verbose_name = 'Shuup more API endpoints'
    label = 'shuup_public_api'
    required_installed_apps = (
        'rest_framework',
        'shuup.api',
    )

default_app_config = 'shuup_public_api.ShuupGuestApiAppConfig'
