************************************************
Docker/Heroku Integration of Django Dance School
************************************************

**Note:** If you are setting up a Docker or Heroku project for the first time, it is recommended that you find someone with a background in the use of these systems to ensure that your deployment goes as smoothly as possible.  If you encounter errors or missing functionality in setting up this template, please submit an issue to the issue tracker, or email `django.danceschool@gmail.com <mailto:django.danceschool@gmail.com>`_.*

Introduction
============

The `Django Dance School <http://django-danceschool.org/>`_ project is designed to be exceptionally flexible and modular, and it can be run locally as well as on any server system that supports Django.  However, you probably want to get your school operational as quickly as possible.  That's why we've created this template.  By using this template, you can quickly set up your school to work with `Heroku <https://www.heroku.com/>`_ and `Amazon S3 <https://aws.amazon.com/s3/>`_ to handle everything and begin operating as quickly as possible.

A key feature of this template is that it is designed to load most credentials and settings from environment variables, rather than directly from your settings.

Using this template and following the manual method installation instructions below also makes it easy for you to begin adding custom templates, custom plugins, and any other custom functionality that goes beyond the basic functions of the project.

**Note:** We are also interested in making this template flexible enough to be usable with other systems and providers, most notably `Docker <https://www.docker.com/>`_, and we are always interested in easier integration with other providers.  If you have an interest in contributing to this project, please `contact us! <mailto:django.danceschool@gmail.com>`_

What This Template Implements on Heroku
=======================================

This section is for those who are unfamiliar with Heroku, its setup, or its pricing system.

Heroku is a platform-as-a-service (PaaS) in which each process in your school's project runs in a separate container known as a dyno.  Dynos can be created or destroyed at whim, allowing you to easily scale your project up or down as needed.  However, for most standard dance schools, you will need only one dyno for each of the following processes:

- Web: The Django instance that serves all web content to users.  By default, this dyno serves Django using the popular `Gunicorn <http://gunicorn.org/>`_.
- Worker: The Dance School project uses the `Huey <http://huey.readthedocs.io/en/latest/index.html>`_ system to handle asynchronous tasks such as sending emails, creating automatically-generated expenses, and closing classes for registration depending on elapsed time.
- Redis: Huey's tasks are queued in the Redis data store, which is automatically configured by this template.
- Database: This template is set up for Heroku to store all of your data in a standard PostgreSQL database which is automatically configured by this template.

Heroku's pricing is based on hours of use for these dynos, as well as their size.  Although Heroku does provide a free tier, with hours of usage limitations, this tier presents issues for the project because there are numerous tasks that are required to run at regular intervals (such as creating expense items and closing classes for registration).  Therefore, we suggest that you use "hobby" dynos.  As of October 2017, hobby web and worker dynos cost $7/month each, a "Hobby Basic" database dyno costs $9/month, and a hobby Redis dyno is free, which means that a standard setup that is suitable for most schools will cost $23/month to host on Heroku.

Initial Heroku Setup
====================

Button-Based Deployment
-----------------------

.. image:: https://www.herokucdn.com/deploy/button.svg
   :target: https://heroku.com/deploy


1. Click the button above and follow the instructions to deploy your app.  This will take several minutes.
2. When the initial deployment has finished, click on "Manage App" to open your app in the Heroku dashboard.  From there, click the button at the top right labeled "More" and select "Run console."  In the field that pops up, type in "bash" to access a command line console for your app.
3. At the command-line console, run the following, and follow the prompts at the command line to create a superuser and perform your school's initial setup:
   - Create a superuser: ``python manage.py createsuperuser``
   - Setup the school with initial pages and sensible defaults: ``python manage.py setupschool``
4. Type ``exit`` to close the command line process, close out of the console, navigate to https://<your-app>.herokuapp.com/ and enjoy!

Manual Method (Recommended for Customization)
----------------------------------------------

You will need:
- A command line Git client installed (you can install one from `here <https://git-scm.com/>`_).
- The Heroku command line client (get it `here <https://devcenter.heroku.com/articles/heroku-cli>`_).
- A Heroku account
- An Amazon AWS account (Heroku dynos cannot store user uploaded files such as instructor photos locally)
- An email address or other method for your site to send emails
- An account with one or more payment processors that you wish to use (Paypal, Square, and Stripe are all supported by default)

1. Open a command line in the location where you would like the local copy of your installation to live.
   Clone this repository to your local folder:

   ``git clone https://github.com/django-danceschool/school-template.git``

2. Login to Heroku:

   ``heroku login``

3. Create a new Heroku app:

   ``heroku create <your-app-name>``

4. Push your project to Heroku, where it will now be deployed (this will take a few minutes the first time that you do it):

   ``git push heroku master``

5. Use one-off dynos to run the initial database migrations that your project needs and to create a
   superuser (you will be prompted for a username and password):

   ::

       heroku run python manage.py migrate
       heroku run python manage.py createsuperuser

6. **Optional, but strongly recommended:** Run the easy-installer setup
   script, and follow all prompts.  This script will guide you through
   the process of setting initial values for many things, creating a few
   initial pages that many school use, and setting up user groups and
   permissions that will make it easier for you to get started running
   your dance school right away.

   ::

       heroku run python manage.py setupschool

7. Go to your site and log in!


Payment Processor Setup
-----------------------

This installation is configured to read your payment processor details from environment variables.  If you have added the appropriate payment processor details needed for the three standard payment processors, then the
appropriate payment processor app will automatically be added to ``INSTALLED_APPS``, so that you do not need to
edit the settings file at all in order to begin accepting payments.

For details on how to get the credentials that you will need for each payment processor, see the `project documentation <http://django-danceschool.readthedocs.io/en/latest/installation.html>`_.

Email Setup
-----------

Your project needs a way to send emails, so that new registrants will be notified when they register, so that you can email your students, so that private event reminder emails can be sent, etc.

By default, this installation uses the ``dj-email-url`` app for simplified email configuration.  You can specify a simple email URL that will permit you to use standard services such as Gmail.  This installation template also has built-in functionality for the popular `Sendgrid <https://sendgrid.com/>`_ email system.  For most small dance schools, the Sendgrid free tier is adequate to send all school-related emails, but Sendgrid allows larger volume emailing as well.

Examples
++++++++

- **Sendgrid:** set ``$SENDGRID_API_KEY`` to your SendGrid API key, set ``$SENDGRID_USERNAME`` to your SendGrid username and set ``$SENDGRID_PASSWORD`` to your SendGrid password.  SendGrid will then be enabled as your email service automatically.
- **Gmail:** set ``$EMAIL_URL`` to 'smtps://user@domain.com:pass@smtp.gmail.com:587'.  Note that Gmail allows only approximately 100-150 emails per day to be sent from a remote email client such as your project installation.


Amazon S3 Setup
---------------

Heroku's dynos are not set up to store your user uploaded files permamently.  Therefore, you must set up a third-party storage solution or else your user uploaded files (instructor photos, receipt attachments for expenses, etc.) will be regularly deleted.

In order for Heroku to access S3, you must set all of the following environment variables:
- ``AWS_ACCESS_KEY_ID``
- ``AWS_SECRET_ACCESS_KEY``
- ``AWS_STORAGE_BUCKET_NAME``

Once these settings have been set, Amazon S3 upload of your files should be automatically enabled!
