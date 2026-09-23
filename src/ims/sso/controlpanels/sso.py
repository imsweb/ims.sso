from plone.app.registry.browser import controlpanel
from plone.z3cform import layout
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from ims.sso.interfaces import ISSOSettings

from ..configs import _


class SettingsEditForm(controlpanel.RegistryEditForm):
    schema = ISSOSettings
    label = _("SSO Settings")


class ControlPanel(layout.FormWrapper):
    form = SettingsEditForm
    index = ViewPageTemplateFile("settings.pt")
    label = _("SSO Settings")


# ControlPanel = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
