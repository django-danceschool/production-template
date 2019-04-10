from django.dispatch import receiver

import logging

from danceschool.core.signals import post_registration
from .tasks import addCustomerToMailingList

# Define logger for this file
logger = logging.getLogger(__name__)


@receiver(post_registration)
def checkForMailingList(sender, **kwargs):
    registration = kwargs.get('registration',None)

    if (
        hasattr(registration,'data') and
        isinstance(registration.data,dict) and
        registration.data.get('mailList',None)
    ):
        logger.info('Adding customer to mailing list as requested.')
        addCustomerToMailingList(registration.customer)
