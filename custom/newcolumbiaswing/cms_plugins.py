from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from danceschool.core.registries import plugin_templates_registry, PluginTemplateBase


class MailchimpSignupPlugin(CMSPluginBase):
    model = CMSPlugin
    name = _('MailChimp Mailing List Sign Up')
    render_template = "mailchimp/mailchimp_signup.html"
    cache = True
    module = 'Forms'

    def render(self, context, instance, placeholder):
        ''' Add the context to sign up to the correct mailing list '''
        context = super(MailchimpSignupPlugin,self).render(context, instance, placeholder)

        context.update({
            'mailchimp_api_key': getattr(settings,'MAILCHIMP_API_KEY',None),
            'mailchimp_list_id': getattr(settings,'MAILCHIMP_LIST_ID',None),
        })

        return context


@plugin_templates_registry.register
class NextDancePluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextdance.html'
    description = _('Next Dance Section for Front Page')


@plugin_templates_registry.register
class NextSocialPluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextsocial.html'
    description = _('Next Social Text for Front Page Cards')


@plugin_templates_registry.register
class NextSeriesPluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextseries.html'
    description = _('Next Series for Front Page Cards')


@plugin_templates_registry.register
class NextSeriesShortPluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextseries_compact.html'
    description = _('Next Series for Front Page Cards (compact)')


@plugin_templates_registry.register
class NextSpecialPluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextspecial.html'
    description = _('Next Special for Front Page Cards')


@plugin_templates_registry.register
class NextSeriesClassesPluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextseries_classespage.html'
    description = _('Next Series for Classes Page Cards')


@plugin_templates_registry.register
class NextSocialDancingPluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextsocial_dancingpage.html'
    description = _('Next Social Text for Dancing Page Cards')


@plugin_templates_registry.register
class NextSpecialDancingPluginTemplate(PluginTemplateBase):
    plugin = 'EventListPlugin'
    template_name = 'events/event_nextspecial_dancingpage.html'
    description = _('Next Special Text for Dancing Page Cards')


plugin_pool.register_plugin(MailchimpSignupPlugin)
