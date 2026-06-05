import logging
from urllib.parse import urlparse

import pytz
from AccessControl.class_init import InitializeClass
from DateTime import DateTime
from persistent.mapping import PersistentMapping
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins import (
    IAuthenticationPlugin,
    IChallengePlugin,
    IExtractionPlugin,
)
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface.declarations import alsoProvides, implementer

from .configs import (
    ACTIVE_STATUS,
    AUTHENTICATED_KEY,
    LOGIN_UPDATE_THRESHOLD,
)
from .interfaces import ISingleSignonUtility, ISSOSettings
from .utility import is_null

logger = logging.getLogger("ims.sso")


class Credentials(dict):
    username: str
    password: str
    idp: str
    first_name: str
    last_name: str
    email: str


@implementer(IExtractionPlugin, IChallengePlugin, IAuthenticationPlugin)
class ImsSsoPlugin(BasePlugin):
    meta_type = "IMS SSO Plugin"
    protocol = "http"

    def __init__(self, id, title=""):  # noqa: A002
        """Create a default user info updater plugin"""
        self.id = id
        self.title = title

    @staticmethod
    def login_url(current_url):
        return f"{api.portal.get().absolute_url()}/@@login?came_from={current_url}"

    def challenge(self, request, response):
        url = self.login_url(request.ACTUAL_URL)
        if url:
            response.redirect(url, lock=True)
            return True
        else:
            return False

    def authenticateCredentials(self, credentials: Credentials):
        """credentials keys: username, password, idp, first_name, last_name, email"""

        login = credentials.get("username")
        if login is None:
            return None
        else:
            user = self._getPAS().getUser(login)

            if user:
                mtool = api.portal.get_tool("portal_membership")
                user_id = user.getId()
                member = mtool.getMemberById(user_id)

                if member.getProperty("active") != ACTIVE_STATUS:
                    annotations = IAnnotations(getRequest())
                    if not annotations.get(AUTHENTICATED_KEY):
                        annotations[AUTHENTICATED_KEY] = PersistentMapping()
                    annotations[AUTHENTICATED_KEY] = user.getId()
                    return None

                mtool.createMemberArea(member_id=user_id)
                domain = urlparse(credentials["idp"]).netloc
                if domain not in api.portal.get_registry_record(interface=ISSOSettings, name="non_update_domains"):
                    self.update_user(
                        username=user_id,
                        first_name=credentials.get("first_name"),
                        last_name=credentials.get("last_name"),
                        email=credentials.get("email"),
                    )
                else:
                    self.update_user(
                        username=user_id,
                        first_name=credentials.get("first_name"),
                        last_name=credentials.get("last_name"),
                    )
                return user_id, login

    def update_user(self, username, first_name, last_name, email=None):
        """Only update if there is a change in fullname/first_name/last_name/email"""
        props = {}
        member = api.user.get(userid=username)
        now = DateTime()
        now_dt = now.asdatetime().date()

        default = DateTime("2000/01/01")
        login_time = member.getProperty("login_time", default)

        # set login time if older than some threshold
        if (
            not login_time
            or (
                now.asdatetime().replace(tzinfo=pytz.utc) - login_time.asdatetime().replace(tzinfo=pytz.utc)
            ).total_seconds()
            > LOGIN_UPDATE_THRESHOLD
        ):
            props.update({"login_time": now, "activation_date": now_dt})

        # update name and email fields if different than curr
        if not is_null(first_name) and not is_null(last_name):
            fullname = last_name + ", " + first_name
            if fullname != member.getProperty("fullname"):
                props["fullname"] = fullname
            if first_name != member.getProperty("first_name"):
                props["first_name"] = first_name
            if last_name != member.getProperty("last_name"):
                props["last_name"] = last_name
        elif not is_null(last_name):
            if last_name != member.getProperty("fullname"):
                props["fullname"] = last_name
            if last_name != member.getProperty("last_name"):
                props["last_name"] = last_name
        if email and not is_null(email) and email != member.getProperty("email"):
            props["email"] = email

        if props:
            logger.info(f"Update user account data for {member.getId()} - {props}")
            # disable CSRF because it's a write
            alsoProvides(getRequest(), IDisableCSRFProtection)
            member.setMemberProperties(props)

    @property
    def shib_header_first_name(self):
        return api.portal.get_registry_record(interface=ISSOSettings, name="shib_header_first_name")

    @property
    def shib_header_last_name(self):
        return api.portal.get_registry_record(interface=ISSOSettings, name="shib_header_last_name")

    @property
    def shib_header_email(self):
        return api.portal.get_registry_record(interface=ISSOSettings, name="shib_header_email")

    @property
    def shib_header_idp(self):
        return api.portal.get_registry_record(interface=ISSOSettings, name="shib_header_idp")

    def extractCredentials(self, request):

        sso = getUtility(ISingleSignonUtility)

        login = sso.get_login_from_request(request)
        if not login:
            return None

        first_name = request.environ.get(self.shib_header_first_name)
        last_name = request.environ.get(self.shib_header_last_name)
        return {
            "username": login,
            "first_name": first_name,
            "last_name": last_name,
            "email": request.environ.get(self.shib_header_email),
            "idp": request.environ.get(self.shib_header_idp),
        }


InitializeClass(ImsSsoPlugin)

manage_addImsSsoForm = PageTemplateFile("./browser/add.pt", globals())


def manage_addImsSso(self, id, title="", REQUEST=None):  # noqa: A002
    """Add an IMS SSO plugin to a Pluggable Authentication Service."""
    plugin = ImsSsoPlugin(id, title)
    self._setObject(plugin.getId(), plugin)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect(f"{self.absolute_url()}/manage_workspace?manage_tabs_message=ImsSsoPlugin+added.")
