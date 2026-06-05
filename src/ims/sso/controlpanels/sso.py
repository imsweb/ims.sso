from ims.sso.interfaces import ISSOSettings
from plone.app.registry.browser import controlpanel
from plone.z3cform import layout
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import form

from ..configs import _


class SettingsEditForm(controlpanel.RegistryEditForm):
    form.extends(controlpanel.RegistryEditForm)
    schema = ISSOSettings
    label = _("SSO Settings")


class ControlPanel(layout.FormWrapper):
    form = SettingsEditForm
    index = ViewPageTemplateFile("settings.pt")
    label = _("SSO Settings")


SsoSettingsControlPanelView = layout.wrap_form(SettingsEditForm, ControlPanel)
