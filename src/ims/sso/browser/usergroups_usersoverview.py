import json
from datetime import date, datetime

import plone.api
from Acquisition import aq_inner
from DateTime import DateTime
from plone.protect import CheckAuthenticator
from Products.CMFPlone.controlpanel.browser.usergroups_usersoverview import (
    UsersOverviewControlPanel as BaseUsersOverviewControlPanel,
)
from Products.CMFPlone.RegistrationTool import _checkEmail
from Products.PluggableAuthService.events import PropertiesUpdated
from zExceptions import Forbidden
from zope.component import getUtility
from zope.event import notify
from zope.schema.interfaces import IVocabularyFactory

from ..configs import (
    ACTIVE_STATUS,
    DISABLED_STATUS,
    INACTIVE_STATUS,
    LOGIN_DOT_GOV_DEV_IDP_DOMAIN,
    LOGIN_DOT_GOV_IDP_DOMAIN,
    _,
)
from ..errors import NoSSOMailTemplatesException
from ..events import UserRelinkedEvent
from ..interfaces import ISingleSignonUtility
from ..utility import notify_activated


class UsersOverviewControlPanel(BaseUsersOverviewControlPanel):
    def __call__(self):
        if not self.request.get("status"):
            self.request["status"] = "active"  # make the default state be active
        elif self.request.form.get("form.button.FindAll", None) is not None:
            self.request["status"] = "all"  # ignore form value and reset
        return super().__call__()

    @property
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def can_change_settings(self):
        return plone.api.user.has_permission("ims.sso: can change settings")

    def can_manage_sso(self):
        return plone.api.user.has_permission("ims.sso: manage control panel")

    def can_change_roles(self):
        if self.request.get("hide_roles", None) is not None:
            return False
        return plone.api.user.has_permission("ims.sso: can change roles")

    def uses_expiry(self):
        return self.sso.get_setting("user_account_expiry")

    def expiry_days(self):
        return self.sso.get_setting("user_account_expiry")

    def emails(self):
        form = self.request.form
        find_all = form.get("form.button.FindAll", None) is not None
        searchstring = (not find_all and form.get("searchstring", "")) or ""
        users = self.doSearch(searchstring)
        emails = set({u["email"] for u in users if u["email"]})
        return ";".join(emails)

    @property
    def portal_roles(self):
        base_roles = super().portal_roles
        try:
            from ims.groupspace.utils import group_role_names
        except ImportError:
            return base_roles
        else:
            _group_role_names = group_role_names()
            return [role for role in base_roles if role not in _group_role_names]

    def print_expiry(self, date):
        """get a text string of how many days until removal"""
        curr = datetime.now().date()

        try:
            days = self.expiry_days() - (curr - date).days
        except TypeError:  # date not set
            return " - creation date not set"
        plural = (days > 1 and "s") or ""
        if days > 0:
            return f" - {days} day{plural} until removal."
        else:
            return " and has expired"

    def doSearch(self, searchString):
        """append some more info to each usr dict"""
        form = self.request.form
        find_all = form.get("form.button.FindAll", None) is not None or self.request.get("status") == "all"
        no_search = (
            not self.request.get("active") and not self.request.get("inactive") and not self.request.get("disabled")
        )

        results = []
        if not searchString or len(searchString.split()) == 1:  # no search string or one word was provided
            results = super().doSearch(searchString)
        else:
            for substring in searchString.split():
                results += super().doSearch(substring)  # result of a search on every substring
            unique_dicts = {d["id"]: d for d in results}  # creating a dictionary with "id" as keys
            results = list(unique_dicts.values())

        curated = []
        for usr in results:
            user_account = plone.api.user.get(userid=usr["id"])
            if not find_all:
                if no_search:
                    # default to active
                    self.request.set("active", "active")
                    if self.request["active"] == user_account.getProperty("active"):
                        pass
                    else:
                        continue
                elif (
                    (self.request.get("active") and self.request["active"] == user_account.getProperty("active"))
                    or (self.request.get("inactive") and self.request["inactive"] == user_account.getProperty("active"))
                    or (self.request.get("disabled") and self.request["disabled"] == user_account.getProperty("active"))
                ):
                    pass
                else:
                    continue
            idp, login = self.sso.extract_idp_login(user_account.getUserName())
            usr["idp"] = self.sso.get_idp_from_domain(idp)
            usr["login"] = login
            if idp in [LOGIN_DOT_GOV_DEV_IDP_DOMAIN, LOGIN_DOT_GOV_IDP_DOMAIN]:
                usr["login"] = None
            usr["first_name"] = user_account.getProperty("first_name", "") or ""
            usr["last_name"] = user_account.getProperty("last_name", "") or ""
            usr["service"] = user_account.getProperty("service", False)
            if not usr["service"]:
                usr["sort_name"] = usr["last_name"] + usr["first_name"] + usr["id"]
            else:
                usr["sort_name"] = "zz" + usr["id"]
            usr["linked"] = idp != "not.linked"
            usr["can_deactivate"] = plone.api.user.has_permission("ims.sso: deactivate")
            if usr["roles"]["Manager"]["explicit"] or (
                usr["roles"]["Manager"]["inherited"] and not self.is_zope_manager
            ):
                usr["can_deactivate"] = False

            login_time = user_account.getProperty("login_time")
            if login_time == DateTime("2000/01/01"):
                usr["login_time"] = "never"
            else:
                usr["login_time"] = plone.api.portal.get_localized_time(login_time)

            # only display activation_date if different from login_time
            usr["activation_date"] = None
            if (
                login_time.asdatetime().date() != user_account.getProperty("activation_date")
                and usr["login_time"] != "never"
                and user_account.getProperty("active") == ACTIVE_STATUS
            ):
                usr["activation_date"] = plone.api.portal.get_localized_time(
                    user_account.getProperty("activation_date")
                )

            usr["login_time_sort"] = (
                login_time.asdatetime().isoformat() if isinstance(login_time, DateTime) else login_time
            )
            if not usr["linked"]:
                usr["expiry"] = self.print_expiry(user_account.getProperty("created_date"))
            try:
                usr["active"] = user_account.getProperty("active")
            except ValueError as err:
                plone.api.portal.show_message(message="You must run the upgrade step for ims.sso.", type="error")
                raise ValueError from err
            curated.append(usr)

        return curated

    def validate_emails(self, users):
        invalid_emails = []
        for user in users:
            validate_email, _null = _checkEmail(user["reset_email"])
            if not validate_email:
                invalid_emails.append(user["reset_email"])
        if invalid_emails:
            emails = ", ".join(invalid_emails)
            plone.api.portal.show_message(
                f"Invalid email address(es): {emails}. Registration emails were not sent. Please ensure all emails are "
                f'formatted correctly and select "Apply changes" again.',
                type="error",
            )
            return False
        return True

    def manageUser(self, users=(), resetpassword=(), delete=()):
        """unfortunately we need to override this to prevent role updates
        most of this is copy/pasted from Products/CMFPlone/controlpanel/browser/usergroups_usersoverview
        """
        CheckAuthenticator(self.request)

        if users:
            context = aq_inner(self.context)
            acl_users = plone.api.portal.get_tool("acl_users")
            registration = plone.api.portal.get_tool("portal_registration")

            utils = plone.api.portal.get_tool("plone_utils")
            active_change = False

            users_with_reset_passwords = []

            _valid = self.validate_emails(users)
            if not _valid:  # we are trying to set an email that is not valid
                return

            for user in users:
                # Don't bother if the user will be deleted anyway
                if user.id in delete:
                    continue

                member = plone.api.user.get(userid=user.id)
                active_status = user.get("active")
                can_deactivate = (
                    "Manager" not in member.getRoles() and plone.api.user.has_permission("ims.sso: deactivate")
                ) or self.is_zope_manager
                if active_status is not None and active_status != member.getProperty("active") and can_deactivate:
                    # active_status is None if the dropdown is disabled
                    props = {
                        "active": active_status,
                    }
                    if active_status == ACTIVE_STATUS:
                        now = date.today()
                        props["activation_date"] = now
                        notify_activated(member)
                    utils.setMemberProperties(member, REQUEST=context.REQUEST, **props)
                    notify(PropertiesUpdated(self, props))
                    active_change = True
                current_roles = member.getRoles()
                # If email address was changed, set the new one
                email = getattr(user, "email", None) or getattr(user, "reset_email", None)
                if email and email != member.getProperty("email"):
                    # If the email field was disabled (ie: non-writeable), the
                    # property might not exist.
                    utils.setMemberProperties(member, REQUEST=context.REQUEST, email=email)
                    plone.api.portal.show_message(_("Changes applied."), self.request, type="info")

                # If reset password has been checked email user a new password
                pw = None
                if hasattr(user, "resetpassword") and can_deactivate:
                    # for sso we don't really reset the password, we resend steps to link account
                    try:
                        plone.api.portal.get_tool("portal_registration")
                        registration.mailPassword(user.id, self.request)
                        notify(UserRelinkedEvent(user))
                        users_with_reset_passwords.append(member.getProperty("fullname") or user.id)
                    except NoSSOMailTemplatesException:
                        plone.api.portal.show_message(
                            _(
                                "Request was not sent. No single sign-on services are assigned for this "
                                "portal. Contact administrator."
                            ),
                            request=self.request,
                            type="error",
                        )
                        return

                if self.can_change_roles():
                    # if they can't change roles they should show up in the template
                    roles = user.get("roles", [])
                    if not self.is_zope_manager and ("Manager" in roles) != ("Manager" in current_roles):
                        # don't allow adding or removing the Manager role
                        raise Forbidden
                    acl_users.userFolderEditUser(user.id, pw, roles, member.getDomains(), REQUEST=context.REQUEST)

            if active_change:
                plone.api.portal.show_message(
                    _("User account activation status(es) changed"),
                    self.request,
                    type="info",
                )

            if delete:
                plone.api.portal.show_message(_("Selected users deleted"), self.request, type="info")
                self.deleteMembers(delete)
            if users_with_reset_passwords:
                reset_passwords_message = _(
                    "reset_passwords_msg",
                    default="The following users have been sent an e-mail with a link to relink their account: "
                    "${user_ids}",
                    mapping={
                        "user_ids": ", ".join(users_with_reset_passwords),
                    },
                )
                plone.api.portal.show_message(reset_passwords_message, self.request)

    def deleteMembers(self, member_ids):
        """Remove from groups as a precursor"""
        for member_id in member_ids:
            groups = plone.api.group.get_groups(member_id)
            for group in groups:
                if group.id == "AuthenticatedUsers":
                    continue
                plone.api.group.remove_user(group=group, username=member_id)
        return super().deleteMembers(member_ids)

    def active_status(self):
        return ACTIVE_STATUS

    def not_active(self, state):
        return state in (INACTIVE_STATUS, DISABLED_STATUS)

    def active_options(self):
        return getUtility(IVocabularyFactory, name="ims.sso.active_status")(self)

    def active_search_options(self):
        opts = []
        find_all = self.request.form.get("form.button.FindAll", None) is not None or self.request.get("status") == "all"
        no_search = (
            not self.request.get("active") and not self.request.get("inactive") and not self.request.get("disabled")
        )
        for opt in getUtility(IVocabularyFactory, name="ims.sso.active_status")(self):
            opts.append(
                {
                    "value": opt.value,
                    "title": opt.title,
                    "showAll": find_all,
                    "noSearch": no_search,
                    "selectActive": self.request.get("active") == opt.value and not find_all,
                    "selectInactive": self.request.get("inactive") == opt.value and not find_all,
                    "selectDisabled": self.request.get("disabled") == opt.value and not find_all,
                }
            )

        return opts

    def datatables(self):
        len_cols = 7  # I guess hard code this?
        if self.can_change_roles():
            len_cols += len(self.portal_roles)
        unsortable_cols = [len_cols - 3, len_cols - 1]
        if self.can_change_roles():
            unsortable_cols = list(range(3, len(self.portal_roles) + 3)) + unsortable_cols
        return json.dumps(
            {
                "searching": False,
                "info": False,
                "lengthMenu": [[25, 50, -1], [25, 50, "All"]],
                "pageLength": 25,
                "stateSave": True,
                "columnDefs": [{"orderable": False, "targets": unsortable_cols}],
            }
        )
