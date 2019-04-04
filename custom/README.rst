*********************************
Add your custom applications here
*********************************

If you would like to add a custom Django application for your organization (to enable custom functionality or templates), do so in this location.

If you are using either Docker or Heroku, then this folder will be automatically added to your PYTHONPATH so that you can reference your package name directly in settings.py (e.g. by adding 'myschoolname' to INSTALLED_APPS).

If your custom app has dependencies that are not included in the main project, then list them in ``requirements.txt`` and they will be automatically installed when you run ``docker/setup_stack.sh``.

Additionally, If you are using Docker, then this folder will automatically be added to your Docker container as a mounted volume.  When you update your custom app, you do not need to rebuild the web container, only to restart it (unless you have added new requirements).
