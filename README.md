# Public API Extensions for shuup

This module aims to provide a proper API for client consumers to the [shuup] e-commerce platform.
Shuup 1.0.0 already provides an [REST API] which is rather designed to integrate with other backend level applications. I lacks of features needed by client consumers, like for example your SPA which should integrate some shop features.

This module provides API endpoints which might not be pure "RESTish" but provide all the calls and actions to implement a shopping flow for a customer.

## State of development

The software is in a very early stage where there are no tests, proper documentation or contribution guidelines. So use with caution.

## Run workbench product

```
cd workbench
pip install -r requirements.txt
python manage.py migrate
python manage.py shuup_init
python manage.py runserver
```

## Install it in your project

Look at the [shuup documentation] to learn how to get a basic shuup project set up. If you have successfully done that add shuup_public_api to your INSTALLED_APPS

```
INSTALLED_APPS = [
    # ...
    'shuup_public_api'
]
```

and hook the urls to your urls.py

```
urlpatterns = [
    url(r'^api/', include('shuup_public_api.urls')),
]
```

Note this app doesn't use the api populate provider of shuup because it uses the [nested router] of drf-extensions.

## Attention! Permission system is not ready

All endpoints are absolutely public by now. That could be an issue, although resources like basket or order are identified by some sort of uuid you could sniff HTTPS traffic and read the urls. After that you could read another persons order or alter the basket.
A better, configurable solution to provide permissions will be added in future - or submit a PR if you like to.

## Contribute

If you are interested please contribute. No guidelines or what so ever yet.

[nested router]: http://chibisov.github.io/drf-extensions/docs/#nested-router-mixin
[shuup]: https://www.shuup.com/en/
[shuup documentation]: http://shuup.readthedocs.io/en/latest/howto/getting_started.html
[REST API]: http://shuup.readthedocs.io/en/latest/web_api/rest_documentation.html