import pytest
from plone import api

test_login = "guido"
test_user_id = "someCrazyUserIdForGuido"


class TestPlugins:
    @pytest.fixture(autouse=True)
    def setup_users(self, sso):
        self.email_params = {
            "link_url": sso.get_url_linkaccount(link_key="froggy", userid="foobar"),
            "registration_email": sso.get_url_registration(),
            "portal_title": "Super site!",
            "to_name": "wohnlice@imsweb.com",
            "from_name": "wohnlice@imsweb.com",
            "subject": "mail",
            "timeout": "",
            "timeout_d": "",
        }

    def test_null_shibb_name(self, portal, sso, shib_header_user, shib_header_idp, shib_header_null):
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login({"user_id": new_member_id})
        initial_login = api.user.get(username=new_member_id).getUserName()

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {shib_header_idp: "", shib_header_user: shib_header_null}
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        view()
        assert api.user.get(username=new_member_id).getUserName() == initial_login

    def test_linkaccount_name(self, portal, sso, shib_header_user, shib_header_idp, shib_header_email):
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login({"user_id": new_member_id})

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_email: "wohnlice@imsweb.com",
            shib_header_user: "wohnlice",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        view()
        assert api.user.get(username=new_member_id).getUserName() == "wohnlice@adfs.omni.imsweb.com"

    def test_linkaccount_name_require_email(self, portal, sso, shib_header_idp, shib_header_user):
        pwrt = api.portal.get_tool("portal_password_reset")
        new_member_id = "userX"
        api.user.create(email="noreply@imsweb.com", username=new_member_id)
        sso.initialize_login({"user_id": new_member_id})

        reset = pwrt.requestReset(new_member_id)
        view = api.content.get_view("linkaccount", context=portal)
        view.request.environ = {
            shib_header_idp: "https://adfs.omni.imsweb.com/loginfoobar",
            shib_header_user: "wohnlice",
        }
        view.publishTraverse(view.request, reset["randomstring"])
        view.publishTraverse(view.request, new_member_id)
        view()
        assert "not.linked" in api.user.get(username=new_member_id).getUserName()
