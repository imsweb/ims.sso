from plone.app.users.browser.passwordpanel import PasswordPanel
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class ChangePassword(PasswordPanel):
    """Raise 404"""

    cp_template = ViewPageTemplateFile("templates/change_password.pt")

    def __call__(self):
        return self.cp_template()
