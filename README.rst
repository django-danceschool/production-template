*****************************************
Heroku Integration of Django Dance School
*****************************************

**This branch is not yet ready for production use.**

Payment Processor Setup
-----------------------

This installation is configured to read your payment processor details from environment variables.  If you have added the appropriate payment processor details needed for the three standard payment processors, then the
appropriate payment processor app will automatically be added to ``INSTALLED_APPS``, so that you do not need to
edit the settings file at all in order to begin accepting payments.


Email Setup
-----------

By default, this installation uses the ``dj-email-url`` app for simplified email configuration.  You can specify a simple email URL that will permit you 

Examples
++++++++

- **Gmail:** set $EMAIL_URL to 'smtps://user@domain.com:pass@smtp.gmail.com:587'.


Task Scheduler Setup
--------------------

Guide coming soon.  Did we mention that this branch is not yet ready for your production use?


Amazon S3 Setup
---------------

Heroku's dynos are not set up to store your user uploaded files permamently.  Therefore, you must set up a third-party storage solution or else your user uploaded files (instructor photos, receipt attachments for expenses, etc.) will be regularly deleted.

In order for Heroku to access S3, you must set all of the following environment variables:
- ``AWS_ACCESS_KEY_ID``
- ``AWS_SECRET_ACCESS_KEY``
- ``AWS_STORAGE_BUCKET_NAME``
