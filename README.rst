************************************************
Docker/Heroku Integration of Django Dance School
************************************************

**Note:** If you are setting up a Docker or Heroku project for the first time,
it is recommended that you find someone with a background in the use of these
systems to ensure that your deployment goes as smoothly as possible.  If you
encounter errors or missing functionality in setting up this template, please
submit an issue to the issue tracker, or email `django.danceschool@gmail.com
<mailto:django.danceschool@gmail.com>`_.

Introduction
============

The `Django Dance School <http://django-danceschool.org/>`_ project is designed
to be exceptionally flexible and modular, and it can be run locally as well as
on any server system that supports Django.  However, you probably want to get
your school operational as quickly as possible.  That's why we've created this
template.  By using this template, you can quickly set up your school to work
with `Heroku <https://www.heroku.com/>`_ and `Amazon S3
<https://aws.amazon.com/s3/>`_ to handle everything and begin operating as
quickly as possible.

A key feature of this template is that it is designed to load most credentials
and settings from environment variables, rather than directly from your settings.

Using this template and following the manual method installation instructions
below also makes it easy for you to begin adding custom templates, custom
plugins, and any other custom functionality that goes beyond the basic functions
of the project.

Installation
============

For more details, see the Django Dance School `documentation
<https://django-danceschool.readthedocs.io/en/latest/installation_production.html>`_.

Docker Deployment
^^^^^^^^^^^^^^^^^

You Will Need:
- Docker >= 17.12.0
- Docker Compose >= 1.14.0
- Environment that can run Bash scripts (Linux, MacOS, or 
  `Windows 10 WSL
  <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_)

**Note** These steps assume that you are using the included LetsEncrypt
capabilities for SSL. If you are planning to provide your own SSL certificate,
or you need to use OpenSSL because you are testing on a server that is not
associated with any domain name, you will be prompted for that when you run
the Bash script.

1. Clone this repository:

   ::
      
      git clone https://github.com/django-danceschool/production-template.git

2. Edit the file ``env.web`` to insert value for the following environment variables:
   - ``ALLOWED_HOST``: Your site's domain name (e.g. mydanceschool.com)
   - ``VIRTUAL_HOST``: Your site's domain name
   - ``LETSENCRYPT_HOST``: Your site's domain name
   - ``LETSENCRYPT_EMAIL``: Your email address at which you want to receive error
     notices related to LetsEncrypt.

3. Run the included Docker ``setup-stack.sh`` Bash script.  You will be prompted
   to provide a range of pieces of information that are needed for setup. And,
   as part of the script, you will also be prompted to take the usual steps needed
   for a Django deployment of the project (running initial migrations, collecting
   static files, creating a superuser, and running the ``setupschool`` command to
   initialize the database).

   ::
      
      cd production-template
      docker/setup_stack.sh

4. Use the ``docker`` command to deploy your stack!

   ::

      docker stack deploy -c docker-compose.yml school

Button-Based Heroku deployment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://www.herokucdn.com/deploy/button.svg
   :target: https://heroku.com/deploy


1. Click the button above and follow the instructions to deploy your app.  This
   will take several minutes.
2. When the initial deployment has finished, click on "Manage App" to open your
   app in the Heroku dashboard.  From there, click the button at the top right
   labeled "More" and select "Run console."  In the field that pops up, type in
   "bash" to access a command line console for your app.
3. At the command-line console, run the following, and follow the prompts at the
   command line to create a superuser and perform your school's initial setup:
   - Create a superuser: ``python manage.py createsuperuser``
   - Setup the school with initial pages and sensible defaults: ``python manage.py setupschool``
4. Type ``exit`` to close the command line process, close out of the console,
   navigate to https://<your-app>.herokuapp.com/ and enjoy!

Manual Heroku Deployment (recommended for customization)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You will need:
- A command line Git client installed (you can install one from `here <https://git-scm.com/>`_).
- The Heroku command line client (get it `here <https://devcenter.heroku.com/articles/heroku-cli>`_).
- A Heroku account
- An Amazon AWS account (Heroku dynos cannot store user uploaded files such as instructor photos locally)
- An email address or other method for your site to send emails
- An account with one or more payment processors that you wish to use (Paypal, Square, and Stripe are all supported by default)

1. Open a command line in the location where you would like the local copy of your installation to live.
   Clone this repository to your local folder:

   ``git clone https://github.com/django-danceschool/production-template.git``

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
