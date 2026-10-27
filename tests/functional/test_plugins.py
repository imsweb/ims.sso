import pytest
import transaction
from plone import api
from plone.testing import zope

test_login = "guido"
test_user_id = "someCrazyUserIdForGuido"

CREDENTIALS = {
    "username": test_login + "@foo.bar",
    "idp": "https://foo.bar",
    "first_name": "Eric",
    "last_name": "Wohnlich",
    "email": "noreply@imsweb.com",
}


class TestPlugins:
    @pytest.fixture
    def setup_user(self, sso):
        usr = api.user.create(username=test_login, email="null@imsweb.com")
        sso.set_login_name(test_login, f"{test_login}@foo.bar")
        return usr

    @pytest.fixture
    def page(self, portal):
        pg = api.content.create(type="Document", container=portal, id="page1", title="My Page")
        transaction.commit()
        return pg

    def test_authenticate_plugin(self, plugin):
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        assert plugin.authenticateCredentials(CREDENTIALS) == (
            test_user_id,
            test_login + "@foo.bar",
        )

    def test_challenge_plugin(self, plugin, portal, http_request):
        zope.logout()
        url = http_request.ACTUAL_URL
        plugin.challenge(http_request, http_request.response)

        assert http_request.response.status == 302
        assert http_request.response.headers["location"] == f"{portal.absolute_url()}/@@login?came_from={url}"

    def test_extraction_plugin(
        self,
        http_request,
        plugin,
        shib_header_user,
        shib_header_first_name,
        shib_header_last_name,
        shib_header_email,
        shib_header_idp,
    ):
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        http_request.environ[shib_header_user] = test_login
        http_request.environ[shib_header_first_name] = "guido"
        http_request.environ[shib_header_last_name] = "van rossum"
        http_request.environ[shib_header_email] = "noreply@imsweb.com"
        http_request.environ[shib_header_idp] = "https://imsweb.com/ims-external"
        assert plugin.extractCredentials(http_request) == {
            "username": "guido@imsweb.com",
            "first_name": "guido",
            "last_name": "van rossum",
            "email": "noreply@imsweb.com",
            "idp": "https://imsweb.com/ims-external",
        }

    def test_update_user(self, plugin, fake_idp):
        usr = api.user.get(username=test_user_id)
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        # control
        assert usr.getProperty("first_name") != "Eric"
        assert usr.getProperty("last_name") != "Wohnlich"
        assert usr.getProperty("email") != "noreply@imsweb.com"

        plugin.authenticateCredentials(CREDENTIALS)
        transaction.commit()
        usr = api.user.get(username=test_user_id)
        assert usr.getProperty("first_name") == "Eric"
        assert usr.getProperty("last_name") == "Wohnlich"
        assert usr.getProperty("email") == "noreply@imsweb.com"

    def test_update_user_lname_only(self, plugin, fake_idp):
        """Test the condition where we only have last_name. This only matters for fullname"""
        usr = api.user.get(username=test_user_id)
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        # control
        assert usr.getProperty("last_name") != "Wohnlich"
        assert usr.getProperty("email") != "noreply@imsweb.com"
        creds = CREDENTIALS.copy()
        del creds["first_name"]

        plugin.authenticateCredentials(creds)
        transaction.commit()
        usr = api.user.get(username=test_user_id)
        assert usr.getProperty("last_name") == "Wohnlich"
        assert usr.getProperty("fullname") == "Wohnlich"
        assert usr.getProperty("email") == "noreply@imsweb.com"

    def test_idp_registration(self, fake_idp, fake_idp_no_update):
        assert fake_idp.update_email
        assert not fake_idp_no_update.update_email

    def test_update_user_non_update(self, plugin, fake_idp_no_update):
        usr = api.user.get(username=test_user_id)
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        # control
        assert usr.getProperty("email") != "noreply@imsweb.com"

        plugin.authenticateCredentials(CREDENTIALS)
        transaction.commit()
        usr = api.user.get(username=test_user_id)
        # always update this
        assert usr.getProperty("first_name") == "Eric"
        assert usr.getProperty("last_name") == "Wohnlich"
        # but not this
        assert usr.getProperty("email") != "noreply@imsweb.com"

    def test_no_update_inactive(self, plugin):
        usr = api.user.get(username=test_user_id)
        api.user.get(username=test_user_id).setMemberProperties({"active": "inactive"})
        # control

        plugin.authenticateCredentials(CREDENTIALS)
        transaction.commit()
        usr = api.user.get(username=test_user_id)
        assert usr.getProperty("first_name") != "Eric"
