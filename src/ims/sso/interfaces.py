from plone.autoform import directives
from plone.supermodel import model
from plone.theme.interfaces import IDefaultPloneLayer
from zope import schema
from zope.component import getUtilitiesFor
from zope.interface.declarations import provider
from zope.interface.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from .configs import ACTIVE_STATUS, DISABLED_STATUS, INACTIVE_STATUS, _


class IBrowserLayer(IDefaultPloneLayer):
    """browser layer"""


class ISingleSignonUtility(Interface):
    """marker interface"""


class IMassRelink(model.Schema):
    """empty"""


class IMailTemplatesUtility(Interface):
    """Marker interface"""

    """ empty """


class IReactivationUtility(Interface):
    """Marker interface"""


class IMailTemplates(Interface):
    """An interface for email forms"""

    def registered_notify(self):
        pass

    def mail_relink(self):
        pass


@provider(IVocabularyFactory)
def mail_idps(context):
    utilities = getUtilitiesFor(IMailTemplates)
    return SimpleVocabulary([SimpleTerm(value=util_id, title=util.title) for util_id, util in utilities])


class ISettings(model.Schema):
    directives.write_permission(user_account_expiry="ims.sso.AdvancedSettings")
    user_account_expiry = schema.Int(
        title=_("Unlinked account expiration"),
        description=_("Days until unlinked accounts will expire"),
    )
    directives.write_permission(mail_format="ims.sso.AdvancedSettings")
    mail_format = schema.Choice(
        title=_("Mail Templates"),
        description=_("Handles email templates to be used"),
        vocabulary="ims.sso.mail_idps",
    )
    directives.write_permission(notify_on_activation="ims.sso.AdvancedSettings")
    notify_on_activation = schema.Bool(
        title="Notify user on activation",
        description="Disable this on development",
        required=False,
    )
    directives.write_permission(notify_relinked="ims.sso.BasicSettings")
    notify_relinked = schema.TextLine(
        title="Email to send notification when users relink their account.",
        required=False,
    )
    directives.write_permission(show_auth_unauth="ims.sso.AdvancedSettings")
    show_auth_unauth = schema.Bool(
        title="Show warning when user is authenticated but unauthorized",
        description="You may want to leave this off if the site is public and users will be authenticated from "
        "elsewhere on the domain",
        required=False,
    )
    directives.write_permission(show_auth_unauth="ims.sso.AdvancedSettings")
    shib_header_user = schema.TextLine(
        title="Shibboleth Header - User Name", default="HTTP_SHIBUSERNAME", required=True
    )
    shib_header_first_name = schema.TextLine(
        title="Shibboleth Header - First Name", default="HTTP_SHIBFIRSTNAME", required=False
    )
    shib_header_last_name = schema.TextLine(
        title="Shibboleth Header - LAST Name", default="HTTP_SHIBLASTNAME", required=False
    )
    shib_header_email = schema.TextLine(title="Shibboleth Header - Email", default="HTTP_SHIBEMAIL", required=False)
    shib_header_idp = schema.TextLine(title="Shibboleth Header - IDP", default="HTTP_SHIBIDP", required=True)
    shib_header_null = schema.TextLine(
        title="Shibboleth Header - null header",
        description="Special value for null user returned by Apache",
        default="HTTP_IMSSSONULLCHECK",
        required=False,
    )
    days_until_inactive = schema.Int(
        title="Days Until Inactive", description="Requires a call to @@sso-tasks", default=90
    )
    days_until_disabled = schema.Int(
        title="Days Until Disabled", description="Requires a call to @@sso-tasks", default=730
    )
    unauth_ignored_views = schema.List(
        title="Views to ignore use of Auth/Unauth warning",
        value_type=schema.TextLine(),
        description="Don't display the viewlet on these pages. Generally these are views that you expect to be ok to use anonymously",
        default=["linkaccount", "reactivate_user", "reactivation", "contact-info"],
    )
    idps = schema.List(
        title="IdPs",
        value_type=schema.TextLine(),
        description="Format is domain|friendly-name|logout-url",
        default=[
            "not.linked|Not Linked|",
            "adfs.omni.imsweb.com|IMS Employee Login|/Shibboleth.sso/Logout?return=https://adfs.omni.imsweb.com/adfs/ls/IdpInitiatedSignon.aspx",
            "auth.nih.gov|NIH|/Shibboleth.sso/Logout?return=https://auth.nih.gov/advancedlogin/logout.asp ",
            "authdev.nih.gov|NIH (dev)|/Shibboleth.sso/Logout?return=https://authdev.nih.gov/advancedlogin/logout.asp",
            "iapps-ctep-.nci.nih.gov|CTEP|",
            "auth.ncats.nih.gov|Login.gov|/Shibboleth.sso/Logout?return=https://secure.login.gov/api/saml/logout2024",
            "a-ci.ncats.io|Login.gov (dev)|/Shibboleth.sso/Logout?return=https://secure.login.gov/api/saml/logout2024",
        ],
    )
    generic_logout = schema.TextLine(
        title="Generic Logout URL",
        description="Logout to use if no IdP specific logout",
        default="/Shibboleth.sso/Logout?return=https://help.loginservice.imsweb.com/logout",
    )
    registration_url = schema.TextLine(
        title="Registration URL",
        description="Link to a registration page for one of the supported IdPs",
        default="https://login.gov/create-an-account/",
    )
    non_update_domains = schema.List(
        title="Non-updating IdPs",
        description="Domain names for IdPs where email/name to exclude from user updates.",
        value_type=schema.TextLine(),
        default=["auth.ncats.nih.gov", "a-ci.ncats.io"],
    )


class IUserExpiryUtility(Interface):
    """global utility"""


@provider(IVocabularyFactory)
def active_status(context):
    return SimpleVocabulary(
        [
            SimpleTerm(value=ACTIVE_STATUS, title="Active"),
            SimpleTerm(value=INACTIVE_STATUS, title="Inactive"),
            SimpleTerm(value=DISABLED_STATUS, title="Disabled"),
        ]
    )
