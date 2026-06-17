from email import message_from_bytes
from email.header import decode_header

import pytest
from ims.sso.interfaces import ISSOSettings
from plone import api
from plone.testing import zope

test_login = "guido"
test_user_id = "someCrazyUserIdForGuido"


def get_decoded_subject(msg):
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        # If there's an encoding, decode the bytes
        return subject.decode(encoding or "utf-8")
    return subject


class TestPlugins:
    @pytest.fixture(autouse=True)
    def setup_users(self, sso):
        self.email_params = {
            "link_url": sso.get_url_linkaccount(link_key="froggy", userid="foobar"),
            "registration_email": sso.get_url_registration(),
            "portal_title": "Super site!",
            "to_name": "wohnliche@imsweb.com",
            "from_name": "wohnliche@imsweb.com",
            "subject": "mail",
            "timeout": "",
            "timeout_d": "",
        }

    @pytest.fixture(autouse=True)
    def set_settings(self, sso):
        api.portal.set_registry_record(interface=ISSOSettings, name="notify_relinked", value="foo@bar.com")

    def test_null_shibb_name(self, portal, sso, shib_header_user, shib_header_idp, shib_header_null):
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)
        initial_login = api.user.get(username=new_member_id).getUserName()

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {shib_header_idp: "", shib_header_user: shib_header_null}
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        view()
        assert api.user.get(username=new_member_id).getUserName() == initial_login

    def test_linkaccount_name(self, portal, sso, shib_header_user, shib_header_idp, shib_header_email, mock_mail):
        zope.logout()
        pwrt = api.portal.get_tool("portal_password_reset")

        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnliche@imsweb.com",
            shib_header_user: "wohnliche",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        mock_mail.reset()
        view()
        assert api.user.get(username=new_member_id).getUserName() == "wohnliche@adfs.omni.imsweb.com"
        msg = message_from_bytes(mock_mail.messages[-1])

        # relink email
        assert "user has updated their account" not in get_decoded_subject(msg)

    def test_linkaccount_relink(self, portal, sso, shib_header_user, shib_header_idp, shib_header_email, mock_mail):
        zope.logout()
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)
        sso.set_login_name(new_member_id, "userx@foobar.com")  # start as linked

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnliche@imsweb.com",
            shib_header_user: "wohnliche",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        mock_mail.reset()
        view()
        assert api.user.get(username=new_member_id).getUserName() == "wohnliche@adfs.omni.imsweb.com"

        msg = message_from_bytes(mock_mail.messages[-1])
        assert "user has updated their account" in get_decoded_subject(msg)

    def test_linkaccount_duplicate_login_name(
        self, portal, sso, shib_header_user, shib_header_idp, shib_header_email, mock_mail
    ):
        """Linkaccount should fail if the resulting login name matches one that already exists for another user"""
        zope.logout()
        pwrt = api.portal.get_tool("portal_password_reset")

        api.user.create(email="noreply@imwweb.com", username="dup")
        sso.set_login_name(user_id="dup", login_name="wohnliche@adfs.omni.imsweb.com")

        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnliche@imsweb.com",
            shib_header_user: "wohnliche",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        mock_mail.reset()
        view()
        assert api.user.get(username=new_member_id).getUserName() != "wohnliche@adfs.omni.imsweb.com"

        assert not mock_mail.messages

    def test_linkaccount_name_require_email(self, portal, sso, shib_header_idp, shib_header_user, mock_mail):
        zope.logout()
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_user: "wohnliche",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        view()
        assert "not.linked" in api.user.get(username=new_member_id).getUserName()

    def test_linkaccount_missing_userid(
        self, portal, sso, shib_header_idp, shib_header_email, shib_header_user, mock_mail
    ):
        zope.logout()
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnliche@imsweb.com",
            shib_header_user: "wohnliche",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        # no second publishTraverse to get user id
        view()
        assert "not.linked" in api.user.get(username=new_member_id).getUserName()

        # and now fix it
        view.publishTraverse(view.request, new_member_id)
        view()
        assert api.user.get(username=new_member_id).getUserName() == "wohnliche@adfs.omni.imsweb.com"

    def test_linkaccount_invalid_key(
        self, portal, mock_mail, sso, shib_header_user, shib_header_idp, shib_header_email
    ):
        zope.logout()
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        shib_environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnliche@imsweb.com",
            shib_header_user: "wohnliche",
        }
        view.request.environ = shib_environ
        view.publishTraverse(view.request, reset["randomstring"] + "foobar")
        view.publishTraverse(view.request, new_member_id)
        view()
        assert "not.linked" in api.user.get(username=new_member_id).getUserName()

        # fix it
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = shib_environ
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        view()
        assert "not.linked" not in api.user.get(username=new_member_id).getUserName()

    def test_linkaccount_already_logged_in(
        self, portal, mock_mail, sso, shib_header_user, shib_header_idp, shib_header_email
    ):
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        shib_environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnliche@imsweb.com",
            shib_header_user: "wohnliche",
        }
        view.request.environ = shib_environ
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        assert "not.linked" in api.user.get(username=new_member_id).getUserName()

    def test_linkaccount_duplicate(self, portal, mock_mail, sso, shib_header_user, shib_header_idp, shib_header_email):
        pwrt = api.portal.get_tool("portal_password_reset")

        existing_member_id = "existing"
        api.user.create(email="noreply@imsweb.com", username=existing_member_id)
        sso.set_login_name(existing_member_id, "wohnliche@adfs.omni.imsweb.com")

        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login(new_member_id)

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnliche@imsweb.com",
            shib_header_user: "wohnliche",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        view()

        domain, _loginname = sso.get_idp_domain_from_login(api.user.get(userid=new_member_id).getUserName())
        assert domain == "not.linked"
