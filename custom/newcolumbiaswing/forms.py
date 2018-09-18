from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.layout import Layout, Div, HTML
from crispy_forms.bootstrap import Alert
from datetime import timedelta

from danceschool.core.forms import RegistrationContactForm
from danceschool.core.constants import getConstant, REG_VALIDATION_STR
from danceschool.core.models import Event, PublicEvent

from .constants import HOW_HEARD_CHOICES
from .models import DatabaseQuery
from .helpers import get_model_choices


class NCSContactForm(RegistrationContactForm):
    '''
    This is the BLH-specific form that customers use to fill out their contact info.
    It inherits from the danceschool app's basic form.
    '''

    agreeToPolicies = forms.BooleanField(
        required=True,
        label='<strong>I agree to the Code of Conduct, and I have read and agree to the Waiver and Release of Liability (required)</strong>',
        help_text='By checking, you agree to abide by all <a href="/policies/" target="_blank">Policies</a>, including the <a href="/conduct/" target="_blank">Code of Conduct</a>.  You also certify that you have read and agree to the <a href="/policies/waiver/" target="_blank">Waiver and Release of Liability</a>.'
    )
    mailList = forms.BooleanField(required=False,label='Add me to the New Columbia Swing mailing list', help_text='Get occasional updates. We make sure that it\'s easy to unsubscribe if you change your mind.')
    isMinor = forms.BooleanField(required=False,label='I am less than 18 years of age')
    gift = forms.CharField(required=False,label='Voucher/Gift Certificate ID')
    howHeardAboutUs = forms.ChoiceField(choices=HOW_HEARD_CHOICES,required=False,label='How did you hear about us?',help_text='Optional')

    def get_mid_layout(self):
        mid_layout = Layout(
            Div(
                'agreeToPolicies',
                'student',
                'mailList',
                Div('isMinor',data_toggle="collapse",data_target="#minorAlert"),
                Alert('Before attending classes, we require all individuals under the age of 18 to have a waiver signed by their guardian. We may also require a guardian to be present. We do not currently offer classes for students under the age of 12.',css_id='minorAlert',css_class="alert-info collapse"),
                css_class='well'),
        )
        return mid_layout
