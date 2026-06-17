import datetime

import plone.api as api
from AccessControl import getSecurityManager
from plone.app.users.browser.register import AddUserForm as BaseAddUserForm
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from zExceptions import Forbidden
from zope.component import getUtility

from ..configs import _
from ..interfaces import IMailTemplatesUtility, ISingleSignonUtility


class AddUserForm(BaseAddUserForm):
    template = ViewPageTemplateFile("templates/newuser_form.pt")
    enable_unload_protection = False  # we have two forms
    confirmation_required = False
    confirmation_user = ""

    @property
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def sso_configured(self):
        return self.sso.get_setting("mail_format")

    def updateFields(self):
        """override - hide some fields we want to generate (eg fullname) or require (mail_me)"""
        super().updateFields()
        if not self.sso_configured():
            api.portal.show_message(
                _("SSO not properly configured. Consult administrator."),
                self.request,
                type="error",
            )
            return self.request.response.redirect(f"{api.portal.get().absolute_url()}/@@usergroup-userprefs")
        del self.fields["fullname"]
        del self.fields["password"]
        del self.fields["password_ctl"]
        if "mail_me" in self.fields:
            del self.fields["mail_me"]
        del self.fields["username"]

    def updateWidgets(self):
        super().updateWidgets()

        # technically these are customizable fields, so we should check that they
        #   exist on the registration form
        requested_fields = ("first_name", "last_name", "email")
        for requested_field in requested_fields:
            if requested_field in self.widgets and requested_field in self.request:
                self.widgets[requested_field].value = self.request[requested_field]

    def updateActions(self):
        super().updateActions()
        classes = self.actions["register"].klass
        if "btn-secondary" in classes:
            classes = classes.replace("btn-secondary", "")  # already has the primary class
        self.actions["register"].klass = classes

    def generate_user_id(self, data):
        """we hide fullname and usernames, generate them"""
        data["fullname"] = data.get("last_name") or ""
        if data.get("first_name"):
            data["fullname"] += ", " + data.get("first_name")
        super().generate_user_id(data)
        data["username"] = data["user_id"]
        return data["user_id"]

    def handle_join_success(self, data):
        """always email the new user
        update login name
        """

        data["mail_me"] = True
        base_method = super().handle_join_success

        getUtility(IMailTemplatesUtility).get_mailer()
        data["fullname"] = data["last_name"]
        if data.get("first_name"):
            data["fullname"] += ", " + data["first_name"]
        base_method(data)
        self.sso.initialize_login(data["user_id"])

        member = api.user.get(userid=data["user_id"])
        member.setMemberProperties({
            "created_date": datetime.date.today(),
            "activation_date": datetime.date.today(),
            "active": "active",
        })

    def applyProperties(self, userid, data):
        """we needed to add fullname but now we have to remove it or applyProperties fails
        this is because applyProperties assumes every key in data is a key of self.fields
           except for ['login_name', 'user_id'] and getFieldNames(IRegisterSchema) + getFieldNames(IAddUserSchema)
        we'll set this manually afterwards
        """
        fullname = data["fullname"]
        del data["fullname"]
        super().applyProperties(userid, data)
        member = api.user.get(userid=userid)
        member.setMemberProperties({"fullname": fullname})

    @button.buttonAndHandler(_("label_register", default="Register"), name="register")
    def action_join(self, action):
        # we overwrite the super action_join so it doesn't redirect with search string
        # TODO - move this to ims.users, it is not sso related

        data, _errors = self.extractData()
        # extra password validation
        self.validate_registration(action, data)

        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return

        match = api.portal.get_tool("acl_users").searchUsers(email=data["email"])
        if match and not self.request.get("form.widgets.allow_match"):
            self.confirmation_required = True

            def wrap_name(name, match):
                if len(match) > 1 and match[-1]["title"] == name:
                    return f' and "{name}"'
                return f'"{name}"'

            joiner = ", " if len(match) > 2 else " "
            self.confirmation_user = joiner.join([wrap_name(m["title"], match) for m in match])

            return

        self.handle_join_success(data)

        if not self._finishedRegister:
            return

        portal_groups = getToolByName(self.context, "portal_groups")
        user_id = data["user_id"]
        is_zope_manager = getSecurityManager().checkPermission(
            ManagePortal,
            self.context,
        )
        try:
            # Add user to the selected group(s)
            if data.get("groups", None) is not None:
                for groupname in data["groups"]:
                    group = portal_groups.getGroupById(groupname)
                    if "Manager" in group.getRoles() and not is_zope_manager:
                        raise Forbidden
                    portal_groups.addPrincipalToGroup(user_id, groupname, self.request)
        except (AttributeError, ValueError) as err:
            api.portal.show_message(err, type="error")
            return
        api.portal.show_message("User added.")
        self.request.response.redirect(self.context.absolute_url() + "/@@usergroup-userprefs")

    @button.buttonAndHandler("Cancel", name="cancel")
    def handleCancel(self, action):
        api.portal.show_message("User registration cancelled.")
        self.request.response.redirect(self.context.absolute_url() + "/@@usergroup-userprefs")
