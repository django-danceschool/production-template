'''
This file defines a variety of preferences that must be set in the DB,
but can be changed dynamically.
'''
from django.forms import HiddenInput
from django.utils.translation import ugettext_lazy as _

from dynamic_preferences.types import BooleanPreference, IntegerPreference, Section
from dynamic_preferences.registries import global_preferences_registry


# we create some section objects to link related preferences together
promotions = Section('promotions',_('NCS Promotions'))


##############################
# Referral Program Preferences
#
@global_preferences_registry.register
class Lindy1EmailEnabled(BooleanPreference):
    section = promotions
    name = 'enableLindy1PromotionEmail'
    verbose_name = _('Enable Post-Lindy 1 Promotional Email')
    help_text = _('The script automatically sends the post-Lindy 1 promotion email with voucher codes using the associated email template.')
    default = False


@global_preferences_registry.register
class Lindy1EmailTemplate(IntegerPreference):
    section = promotions
    name = 'lindy1TemplateID'
    help_text = _('The ID of the Email Template used to send Post-Lindy 1 Promotional Emails.')
    widget = HiddenInput

    # This is automatically updated by apps.py
    default = 0
