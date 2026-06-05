import plone.api
from Products.Five import BrowserView


class Unauthorized(BrowserView):
    def email_from_address(self):
        return plone.api.portal.get_registry_record("plone.email_from_address")
