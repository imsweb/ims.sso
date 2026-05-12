import datetime
import hashlib
import logging
import warnings
from urllib.parse import urlparse

import DateTime
from persistent.mapping import PersistentMapping
from plone import api
from plone.uuid.interfaces import IUUIDGenerator
from Products.PlonePAS.tools.memberdata import MemberData
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility, queryUtility
from zope.globalrequest import getRequest
from ZPublisher.HTTPRequest import HTTPRequest

from .configs import ACTIVE_STATUS, APACHE_NULL, AUTHENTICATED_KEY, DISABLED_STATUS, INACTIVE_STATUS, NOT_LINKED
from .errors import NoSSOMailTemplatesException
from .interfaces import IMailTemplates, ISettings

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
    def initialize_login(data: dict) -> None:
        """Create a randomized login name for the unlinked account

        Effectively, this account cannot be used until linked
        """
        pas = api.portal.get_tool("acl_users")
        login_name = hashlib.sha256(data["user_id"].encode("utf-8")).hexdigest() + "@not.linked"  # nosec
        pas.updateLoginName(data["user_id"], login_name)

    @staticmethod
    def get_login_from_request(request: HTTPRequest) -> str:
        """Generate the login name from the request headers"""
        idp_header = api.portal.get_registry_record(interface=ISettings, name="shib_header_idp")
        user_header = api.portal.get_registry_record(interface=ISettings, name="shib_header_user")
        domain = urlparse(request.environ.get(idp_header)).netloc
        login = request.environ.get(user_header)
        if is_null(login):
            return ""
        return f"{login}@{domain}"

    # TODO - remove
    def loginname_from_request(self, request: HTTPRequest) -> str:
        warnings.warn("Use get_login_from_request", DeprecationWarning, stacklevel=2)
        return self.get_login_from_request(request)

    @property
    def idp_info(self) -> dict[str : dict[str:str]]:
        """Get supported IdPs"""
        idps = api.portal.get_registry_record(interface=ISettings, name="idps")
        _idps = {}
        for idp in idps:
            idp_id, name, logout = idp.split("|")
            _idps[idp_id] = {"title": name, "logout": logout}
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
    def generate_key(_string: str) -> str:
        """Generate a unique key. Used for linking user account to IdP account

        Idea borrowed from portal_registration"""
        return hashlib.sha256(_string.encode("utf-8")).hexdigest()

    @staticmethod
    def get_setting(field: str) -> str:
        """Helper method"""
        return api.portal.get_registry_record(interface=ISettings, name=field)

    def get_url_logout(self, request: HTTPRequest) -> str:
        """Get the logout URL. This will be determined by the REQUEST headers and IdP settings"""
        login_name = self.get_login_from_request(request)
        generic_logout = api.portal.get_registry_record(interface=ISettings, name="generic_logout")
        try:
            idp, login_name = self.get_idp_domain_from_login(login_name)
        except TypeError:
            return generic_logout

        logout_url = self.idp_info[idp]["logout"] if idp in self.idp_info else generic_logout

        return logout_url

    def get_url_linkaccount(self, link_key: str, userid: str) -> str:
        """Use the generated link key"""
        host = api.portal.get().absolute_url()
        return f"{host}/linkaccount/{link_key}/{userid}"

    def get_url_registration(self) -> str:
        """Optional - used in mail templates. Use this to direct a user to register with one of your IdPs"""
        return api.portal.get_registry_record(interface=ISettings, name="registration_url")

    def get_idp_from_domain(self, domain: str) -> str:
        """Get all info (title, logout url) for the given domain"""
        return self.idp_info[domain]["title"] if domain in self.idp_info else domain

    @staticmethod
    def set_login_name(user_id: str, login_name: str) -> None:
        """also set the email if we get it"""
        pas = api.portal.get_tool("acl_users")
        pas.updateLoginName(user_id, login_name)

    @staticmethod
    def send_portal_link(email: str = "") -> None:
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

    def notify_relinked(self, usr, email, plone_view):
        to_email = api.portal.get_registry_record(interface=ISettings, name="notify_relinked")
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

    def purge_expired(self) -> None:
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

            if f"{NOT_LINKED}" in usr.getUserName() and (today - date).days >= expiry:
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

    @staticmethod
    def disable_user_accounts() -> None:
        today = datetime.date.today()
        days_until_inactive = api.portal.get_registry_record(interface=ISettings, name="days_until_inactive")
        days_until_disabled = api.portal.get_registry_record(interface=ISettings, name="days_until_disabled")

        for usr in api.user.get_users():
            date = usr.getProperty("activation_date")
            if date == "":
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

    def no_challenge_header(self, request):
        user_header = api.portal.get_registry_record(interface=ISettings, name="shib_header_user")
        challenge_key = request.environ.get(user_header)
        return challenge_key and not is_null(challenge_key)


class MailTemplatesUtility:
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

    @staticmethod
    def get_format():
        try:
            mail_format = api.portal.get_registry_record(interface=ISettings, name="mail_format")
        except api.exc.InvalidParameterException as err:
            raise NoSSOMailTemplatesException(
                "No single sign mailing formats have been defined for this portal."
            ) from err
        else:
            mail_format = "ims.sso.idp.nosso"

        return queryUtility(IMailTemplates, name=mail_format)

    def registered_notify(self) -> str:
        mailer = self.get_format()
        return mailer.registered_notify()

    def mail_relink(self) -> str:
        mailer = self.get_format()
        return mailer.mail_relink()

    def mail_form(self, template: str, params: dict):
        return (self.subject + template + self.expiry).format(**params)


class ReactivationUtility:
    annotation_key = "ReactivationUtility"

    @property
    def portal(self):
        return api.portal.get()

    @property
    def user_id(self) -> str:
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
        now = datetime.datetime.utcnow()
        return now >= expiry

    def _validate(self, activation_key: str) -> bool:
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

    def purge_annotations(self) -> None:
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


def notify_activated(user: MemberData) -> None:
    """Notify a user that has been reactivated"""
    user_email = user.getProperty("email", None)
    portal_title = api.portal.get_registry_record("plone.site_title")
    _notify_activated = api.portal.get_registry_record(name="notify_on_activation", interface=ISettings)
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
    null_header = api.portal.get_registry_record(interface=ISettings, name="shib_header_null")
    if value is None:
        return True
    if not request:
        request = getRequest()
    return value in (APACHE_NULL, request.get(null_header))
