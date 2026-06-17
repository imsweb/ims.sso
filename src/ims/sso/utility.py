import datetime
import hashlib
import logging
import warnings
from urllib.parse import urlparse

import DateTime
from persistent.mapping import PersistentMapping
from plone import api
from plone.uuid.interfaces import IUUIDGenerator
from Products.Five import BrowserView
from Products.PlonePAS.tools.memberdata import MemberData
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.globalrequest import getRequest
from ZPublisher.HTTPRequest import HTTPRequest

from .configs import ACTIVE_STATUS, APACHE_NULL, AUTHENTICATED_KEY, DISABLED_STATUS, INACTIVE_STATUS, NOT_LINKED
from .errors import NoSSOMailTemplatesException
from .interfaces import IMailTemplates, ISSOSettings

send_portal_link_msg = """Your account has been successfully updated on {}.

The portal address is: {}

Please bookmark or save this link for future access."""

DEFAULT_EXPIRY = 30


logger = logging.getLogger("ims.sso")


def registration_subject(portal_title):
    """standardize subject for registration emails"""
    return f"Site Registration for {portal_title}"


class SingleSignonUtility:
    """Single Sign On Utility"""

    @staticmethod
    def get_setting(name: str) -> str:
        """Helper method"""
        return api.portal.get_registry_record(interface=ISSOSettings, name=name)

    def is_plone_authenticated(self):
        """Both Plone and Shibboleth need to identify the user. We need methods for both"""
        return not api.user.is_anonymous()

    def is_shibboleth_authenticated(self, request):
        """Checks if Shibboleth session exists by looking for user header
        This does not check if user is anonymous to Plone nor does it check authorization
        """
        user_header = self.get_setting(name="shib_header_user")
        usr = request.environ.get(user_header)
        return usr and not is_null(usr)

    @property
    def pas(self):
        return api.portal.get_tool("acl_users")

    def initialize_login(self, user_id: str) -> None:
        """Create a randomized login name for the unlinked account

        Effectively, this account cannot be used until linked
        """
        login_name = hashlib.sha256(user_id.encode("utf-8")).hexdigest() + "@not.linked"  # nosec
        self.pas.updateLoginName(user_id, login_name)

    def get_login_from_request(self, request: HTTPRequest) -> str:
        """Generate the login name from the request headers"""
        idp_header = self.get_setting(name="shib_header_idp")
        user_header = self.get_setting(name="shib_header_user")
        domain = urlparse(request.environ.get(idp_header)).netloc or request.environ.get(idp_header)
        login = request.environ.get(user_header)
        if is_null(login):
            return ""
        return f"{login}@{domain}"

    def loginname_from_request(self, request: HTTPRequest) -> str:  # pragma: no cover
        warnings.warn("Use get_login_from_request", DeprecationWarning, stacklevel=2)
        return self.get_login_from_request(request)

    @property
    def idp_info(self) -> dict[str : dict[str:str]]:
        """Get supported IdPs"""
        idps = self.get_setting(name="idps") or []
        _idps = {}
        for idp in idps:
            idp = idp.copy()
            idp_id = idp.pop("domain")
            _idps[idp_id] = idp
        return _idps

    def get_idp_domain_from_login(self, login_name: str) -> tuple[str, str]:
        """If given wohnlice@adfs.omni.imsweb.com, return ["wohnlice", "adfs.omni.imsweb.com"]"""
        name = login_name.split("@")
        domain = name.pop()
        name = "@".join(name)
        if domain not in self.idp_info:
            return "unknown IDP", login_name

        return domain, name

    def extract_idp_login(self, login_name):
        warnings.warn("Use get_idp_domain_from_login", category=DeprecationWarning, stacklevel=2)
        return self.get_idp_domain_from_login(login_name)

    @staticmethod
    def generate_password(_string: str) -> str:
        """Generate a unique "password". User account must have a password field, even though we authenticate
        only with SSO."""
        return hashlib.sha256(_string.encode("utf-8")).hexdigest()

    def get_url_logout(self, request: HTTPRequest) -> str:
        """Get the logout URL. This will be determined by the REQUEST headers and IdP settings"""
        login_name = self.get_login_from_request(request)
        generic_logout = self.get_setting(name="generic_logout")
        try:
            idp, login_name = self.get_idp_domain_from_login(login_name)
        except TypeError:
            return generic_logout

        logout_url = self.idp_info[idp]["idp_logout"] if idp in self.idp_info else generic_logout

        return logout_url

    def get_url_linkaccount(self, link_key: str, userid: str) -> str:
        """Use the generated link key"""
        host = api.portal.get().absolute_url()
        return f"{host}/linkaccount/{link_key}/{userid}"

    def get_url_registration(self) -> str:
        """Optional - used in mail templates. Use this to direct a user to register with one of your IdPs"""
        return self.get_setting(name="registration_url")

    def get_idp_from_domain(self, domain: str) -> str:
        """Get all info (title, logout url) for the given domain"""
        return self.idp_info[domain]["name"] if domain in self.idp_info else domain

    def set_login_name(self, user_id: str, login_name: str) -> None:
        """Login name is a property of a user"""
        self.pas.updateLoginName(user_id, login_name)

    @staticmethod
    def send_portal_link(email: str = "") -> None:
        """Send email with instructions on how to link their account"""
        usr = api.user.get_current()
        user_email = email or usr.getProperty("email", None)
        portal_title = api.portal.get_registry_record("plone.site_title")
        portal = api.portal.get()
        if user_email:
            subj = f"Link to access {portal_title}"
            msg = send_portal_link_msg.format(portal_title, portal.absolute_url())
            fromname = api.portal.get_registry_record("plone.email_from_name")
            fromadd = api.portal.get_registry_record("plone.email_from_address")
            email_from = f"{fromname} <{fromadd}>"
            api.portal.send_email(
                sender=email_from,
                recipient=user_email,
                subject=subj,
                body=msg,
                immediate=False,
            )

    def notify_relinked(self, usr, email: str, plone_view: BrowserView):
        """Send a "success" email notification"""
        to_email = self.get_setting(name="notify_relinked")
        if to_email:
            portal_title = api.portal.get_registry_record("plone.site_title")
            domain = self.extract_idp_login(usr.getUserName())[0]
            idp = self.get_idp_from_domain(domain)
            subj = f"{portal_title} user has updated their account"
            msg = (
                f"The {portal_title} user {usr.getProperty('fullname')} linked their {usr.getId()} portal account "
                f"with a {idp} account using the email address {email} for their login credentials on "
                f"{plone_view.toLocalizedTime(DateTime.DateTime(), long_format=1)}."
            )
            fromname = api.portal.get_registry_record("plone.email_from_name")
            fromadd = api.portal.get_registry_record("plone.email_from_address")
            email_from = f"{fromname} <{fromadd}>"
            api.portal.send_email(
                sender=email_from,
                recipient=to_email,
                subject=subj,
                body=msg,
                immediate=False,
            )

    def purge_unlinked(self) -> None:
        """Users who have not been linked in X days are deleted"""
        expired = []
        deleted = []

        try:
            expiry = self.get_setting("user_account_expiry")
            if expiry is None:  # have to allow for 0, at least in theory
                expiry = DEFAULT_EXPIRY
        except api.exc.InvalidParameterException:  # not set
            expiry = DEFAULT_EXPIRY
        today = datetime.date.today()
        portal = api.portal.get()

        for usr in api.user.get_users():
            date = usr.getProperty("created_date")
            if not date or not isinstance(date, datetime.date):  # if date hadn't been set
                usr.setMemberProperties({"created_date": today})
                date = today

            if NOT_LINKED in usr.getUserName() and (today - date).days >= expiry:
                expired.append(usr.getProperty("email"))
                deleted.append(usr.getId())
                logger.info(
                    "deleted {portal}: {user_id}|{login_name}|{email}".format(
                        portal=portal.getId(),
                        user_id=usr.getId(),
                        login_name=usr.getUserName(),
                        email=usr.getProperty("email"),
                    )
                )
                api.user.delete(username=usr.getId())

        if deleted:
            logger.info(f"Expired users purged from {portal.getId()}: {expired}")

    def disable_user_accounts(self) -> None:
        """Update user account active status based on days since activation/login

        activation_date is a user property set on first activation, and updated on login through the
        IAuthenticateCredentials plugin

        exceptions:
        - User property `service` can be set to True to skip this check
        - Users with `Manager` role are never disabled
        """
        today = datetime.date.today()
        days_until_inactive = self.get_setting(name="days_until_inactive")
        days_until_disabled = self.get_setting(name="days_until_disabled")

        for usr in api.user.get_users():
            date = usr.getProperty("activation_date")
            if date == "":
                # one time fallback, if field was never set
                usr.setMemberProperties({"activation_date": today})
                date = today
            can_be_deactivated = "Manager" not in api.user.get_roles(username=usr.getId()) and not usr.getProperty(
                "service"
            )
            user_status = usr.getProperty("active")
            if (today - date).days >= days_until_disabled and can_be_deactivated:
                usr.setMemberProperties({"active": DISABLED_STATUS})
            elif (today - date).days >= days_until_inactive and can_be_deactivated and user_status != DISABLED_STATUS:
                usr.setMemberProperties({"active": INACTIVE_STATUS})

    def has_user_header(self, request):
        user_key = request.environ.get(self.get_setting(name="shib_header_user"))
        return user_key and not is_null(user_key)


class MailTemplatesUtility:
    @staticmethod
    def get_setting(name: str) -> str:
        """Helper method"""
        return api.portal.get_registry_record(interface=ISSOSettings, name=name)

    subject = "\n".join((
        "From: {from_name}",
        "To: {to_name}",
        "Subject: {subject}",
        "Precedence: bulk",
        "",
        "",
    ))
    expiry = "\n".join((
        "",
        "",
        "This link will expire in {timeout} days (by {timeout_d}).",
        "If {timeout} days have elapsed, please reply to this e-mail and request another link.",
    ))

    def get_mailer(self):
        """Get the mail templater"""
        mail_format = self.get_setting(name="mail_format")
        if not mail_format:
            raise NoSSOMailTemplatesException("No mail templates configured")

        return getUtility(IMailTemplates, name=mail_format)

    def registered_notify(self) -> str:
        """Send notification email of registration"""
        mailer = self.get_mailer()
        return mailer.registered_notify()

    def mail_relink(self) -> str:
        """Send account relink email"""
        mailer = self.get_mailer()
        return mailer.mail_relink()

    def mail_form(self, template: str, params: dict):
        return (self.subject + template + self.expiry).format(**params)


class ReactivationUtility:
    """This utility allows users to auto reactivate themselves when they have an inactive account. For
    this to happen we need to consider that these users will be anonymous to Plone, because the
    IAuthenticationCredentials plugin has rejected them due to their `status`.

    Steps to take:
    1. Identify the user by id@domain from the Shibboleth headers
    2. Generate a unique key for this user and register it with the portal annotations. Set an expiration date
    3. Send the user a link to the reactivation view that contains the unique key
    4. Validate the key matches the user and is not expired and has not since become disabled
    5. Update the user's `status` to `active`

    """

    annotation_key = "ReactivationUtility"

    @property
    def portal(self):
        return api.portal.get()

    @property
    def user_id(self) -> str:
        """The annotation value here is the id@domain login name we get from Shibboleth headers"""
        annotations = IAnnotations(getRequest())
        try:
            if usr_id := annotations[AUTHENTICATED_KEY]:
                return usr_id
        except KeyError:
            return ""

    def request_reactivation(self) -> tuple[str, datetime.datetime]:
        """Request to reactivate, generates a unique str with expiration time for this user"""
        uuid_generator = getUtility(IUUIDGenerator)
        randomstring = uuid_generator()

        if self.user_id:
            expiry = self.set_activation_key(activation_key=randomstring)
            return randomstring, expiry

    def _expired(self, expiry: datetime) -> bool:
        """Check that key has not expired"""
        try:
            return datetime.datetime.now() >= expiry
        except TypeError:
            return datetime.datetime.now(datetime.UTC) >= expiry

    def _validate(self, activation_key: str) -> bool:
        """Check that:
        1. We have an activation key for this user in the annotations
        2. The key has not expired
        3. The user has not since been disabled
        """
        annotations = IAnnotations(self.portal)
        try:
            rec = annotations[self.annotation_key][self.user_id]
        except KeyError:  # no user key - fake link, old link, or wrong user
            return False
        _key = rec["activation_key"]
        expired = rec["expiry"]
        usr = api.user.get(userid=self.user_id)
        disabled = usr.getProperty("active") == DISABLED_STATUS
        return activation_key == _key and not self._expired(expired) and not disabled

    def set_activation_key(self, activation_key: str) -> datetime.datetime | None:
        """Register the activation key for this user in the portal annotations. Set an expiration date"""
        if not self.user_id:
            return
        annotations = IAnnotations(self.portal)
        if not annotations.get(self.annotation_key):
            annotations[self.annotation_key] = PersistentMapping()
        expiry = datetime.datetime.now() + datetime.timedelta(days=1)
        annotations[self.annotation_key][self.user_id] = {
            "activation_key": activation_key,
            "expiry": expiry,
        }
        return expiry

    def get_activation_key(self) -> str | None:
        """Get the key from annotations"""
        if not self.user_id:
            return
        annotations = IAnnotations(self.portal)
        if not annotations.get(self.annotation_key):
            return None
        return annotations[self.annotation_key][self.user_id]

    def reactivate_user(self, activation_key: str) -> bool:
        """Reactive user if their activation key is valid"""
        annotations = IAnnotations(self.portal)
        if self.user_id and self._validate(activation_key):
            # change status
            usr = api.user.get(userid=self.user_id)
            usr.setMemberProperties({"active": ACTIVE_STATUS})

            # remove activation key
            del annotations[self.annotation_key][self.user_id]
            return True
        return False

    def purge_activation_keys(self) -> None:
        """Remove expired activation keys"""
        annotations = IAnnotations(self.portal)
        try:
            rec = annotations[self.annotation_key]
        except KeyError:
            pass
        else:
            to_del = []
            for userid in rec:
                reactiv = rec[userid]
                try:
                    if reactiv["expiry"] < datetime.datetime.now():  # offset-naive
                        to_del.append(userid)
                except TypeError:
                    if reactiv["expiry"] < datetime.datetime.now(datetime.UTC):  # offset-aware
                        to_del.append(userid)
            for userid in to_del:
                del rec[userid]

    def current_user_status(self):
        """Get the `active` value for the user using the user id in annotations."""
        annotations = IAnnotations(getRequest())
        if AUTHENTICATED_KEY in annotations:
            userid = annotations[AUTHENTICATED_KEY]
            user = api.user.get(userid)
            return user.getProperty("active")
        return "unknown"


def notify_activated(user: MemberData) -> None:
    """Notify a user that has been reactivated"""
    user_email = user.getProperty("email", None)
    portal_title = api.portal.get_registry_record("plone.site_title")
    _notify_activated = api.portal.get_registry_record(name="notify_on_activation", interface=ISSOSettings)
    portal = api.portal.get()
    if user_email and _notify_activated:
        subj = f"Account Reactivation for {portal_title}"
        msg = f"Your account on {portal_title} has been reactivated. You may login at {portal.absolute_url()}."
        fromname = api.portal.get_registry_record("plone.email_from_name")
        fromadd = api.portal.get_registry_record("plone.email_from_address")
        email_from = f"{fromname} <{fromadd}>"
        api.portal.send_email(
            sender=email_from,
            recipient=user_email,
            subject=subj,
            body=msg,
            immediate=False,
        )


def is_null(value: str, request: HTTPRequest = None) -> bool:
    """user is null value in Shibboleth"""
    null_header = api.portal.get_registry_record(interface=ISSOSettings, name="shib_header_null")
    if value is None:
        return True
    if not request:
        request = getRequest()
    return value in (APACHE_NULL, request.get(null_header))
