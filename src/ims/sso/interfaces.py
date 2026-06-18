import json

from plone.autoform import directives
from plone.schema import JSONField
from plone.supermodel import model
from plone.theme.interfaces import IDefaultPloneLayer
from zope import schema
from zope.interface.interface import Interface

from .configs import _


class IBrowserLayer(IDefaultPloneLayer):
    """browser layer"""


class ISSOSettings(model.Schema):
    directives.write_permission(shib_header_user="ims.sso.AdvancedSettings")
    shib_header_user = schema.TextLine(
        title="Shibboleth Header - User Name",
        default="HTTP_SHIBUSERNAME",
        required=True,
    )
    directives.write_permission(shib_header_first_name="ims.sso.AdvancedSettings")
    shib_header_first_name = schema.TextLine(
        title="Shibboleth Header - First Name",
        default="HTTP_SHIBFIRSTNAME",
        required=False,
    )
    directives.write_permission(shib_header_last_name="ims.sso.AdvancedSettings")
    shib_header_last_name = schema.TextLine(
        title="Shibboleth Header - LAST Name",
        default="HTTP_SHIBLASTNAME",
        required=False,
    )
    directives.write_permission(shib_header_email="ims.sso.AdvancedSettings")
    shib_header_email = schema.TextLine(title="Shibboleth Header - Email", default="HTTP_SHIBEMAIL", required=False)
    directives.write_permission(shib_header_idp="ims.sso.AdvancedSettings")
    shib_header_idp = schema.TextLine(title="Shibboleth Header - IDP", default="HTTP_SHIBIDP", required=True)
    directives.write_permission(shib_header_null="ims.sso.AdvancedSettings")
    shib_header_null = schema.TextLine(
        title="Shibboleth Header - null header",
        description="Special value for null user returned by Apache",
        default="HTTP_IMSSSONULLCHECK",
        required=False,
    )
    directives.write_permission(user_account_expiry="ims.sso.BasicSettings")
    user_account_expiry = schema.Int(
        title=_("Unlinked account expiration"),
        description=_("Days until unlinked accounts will expire"),
        default=90,
    )
    directives.write_permission(mail_format="ims.sso.BasicSettings")
    mail_format = schema.Choice(
        title=_("Mail Templates"),
        description=_("Registration and relink templates to use for emails"),
        vocabulary="ims.sso.mail_idps",
    )
    directives.write_permission(notify_on_activation="ims.sso.NotificationSettings")
    notify_on_activation = schema.Bool(
        title="Send success notification to user when they activate",
        required=False,
    )
    directives.write_permission(notify_relinked="ims.sso.NotificationSettings")
    notify_relinked = schema.TextLine(
        title="Send notification of successful relinks to this email address.",
        required=False,
    )
    directives.write_permission(show_auth_unauth="ims.sso.BasicSettings")
    show_auth_unauth = schema.Bool(
        title="Show warning when user is authenticated but unauthorized",
        description="You may want to leave this off if the site is public and users will be authenticated from "
        "elsewhere on the domain",
        required=False,
    )
    directives.write_permission(days_until_inactive="ims.sso.BasicSettings")
    days_until_inactive = schema.Int(
        title="Days Until Inactive",
        description="Requires a call to @@sso-tasks to enforce",
        default=90,
    )
    directives.write_permission(days_until_disabled="ims.sso.BasicSettings")
    days_until_disabled = schema.Int(
        title="Days Until Disabled",
        description="Requires a call to @@sso-tasks to enforce",
        default=730,
    )
    directives.write_permission(unauth_ignored_views="ims.sso.AdvancedSettings")
    unauth_ignored_views = schema.List(
        title="Views to ignore use of Auth/Unauth warning",
        value_type=schema.TextLine(),
        description="Don't display the viewlet on these pages. "
        "Generally these are views that you expect to be ok to use anonymously",
        default=["linkaccount", "reactivate_user", "reactivation", "contact-info"],
    )
    directives.write_permission(idps="ims.sso.AdvancedSettings")
    idps = JSONField(
        title="IdPs",
        description='See schema for details. ex: [{"domain": "", "name": "", "idp_logout":""}]',
        schema=json.dumps({
            "type": "array",
            "items": {
                "title": "IdPs",
                "type": "object",
                "properties": {
                    "domain": {"description": "Domain", "type": "string"},
                    "name": {"description": "Name", "type": "string"},
                    "idp_logout": {"description": "IdP Logout", "type": "string"},
                },
                "required": ["domain", "name"],
            },
        }),
    )
    directives.write_permission(generic_logout="ims.sso.BasicSettings")
    generic_logout = schema.TextLine(
        title="Generic Logout URL",
        description="Logout to use if no IdP specific logout",
        default="/Shibboleth.sso/Logout?return=https://help.loginservice.imsweb.com/logout",
    )
    directives.write_permission(registration_url="ims.sso.BasicSettings")
    registration_url = schema.TextLine(
        title="Registration URL",
        description="Link to a registration page for one of the supported IdPs",
        default="https://login.gov/create-an-account/",
    )
    directives.write_permission(idps="ims.sso.AdvancedSettings")
    non_updating_idps = schema.List(
        title="Non-updating IdPs",
        description="Blacklist of IdP domain names where user email and name will not be updated.",
        value_type=schema.TextLine(),
        default=[],
    )
    undisplayed_loginname_idps = schema.List(
        title="Don't display Login Name for these Idps",
        description="Login names from these domains will not be displayed on the users overview page.",
        value_type=schema.TextLine(),
        default=[],
    )


class ISingleSignonUtility(Interface):
    """Global utility"""


class IMassRelink(model.Schema):
    """Marker interface"""


class IMailTemplatesUtility(Interface):
    """Marker interface"""


class IReactivationUtility(Interface):
    """Marker interface"""


class IMailTemplates(Interface):
    """An interface for email forms"""

    def registered_notify(self):
        pass  # pragma: no cover

    def mail_relink(self):
        pass  # pragma: no cover


class IUserExpiryUtility(Interface):
    """global utility"""
