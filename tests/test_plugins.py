from ims.users.configs import (
    CHALLENGE_HEADER_KEY,
    EMAIL_KEY,
    FIRST_NAME_KEY,
    IDP_KEY,
    LAST_NAME_KEY,
)
from plone import api

test_login = "guido"
test_user_id = "someCrazyUserIdForGuido"


class TestPlugins:
    def test_find_user_by_plugin(self, plugin):
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        assert plugin.authenticateCredentials(
            {
                "username": test_login + "@adfs.imsweb.com",
                "idp": "https://www.okta.com",
            }
        ) == (test_user_id, test_login + "@adfs.imsweb.com")

    def test_extraction_plugin(self, http_request, plugin):
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        http_request.environ[CHALLENGE_HEADER_KEY] = test_login
        http_request.environ[FIRST_NAME_KEY] = "guido"
        http_request.environ[LAST_NAME_KEY] = "van rossum"
        http_request.environ[EMAIL_KEY] = "noreply@imsweb.com"
        http_request.environ[IDP_KEY] = "https://imsweb.com/ims-external"
        assert plugin.extractCredentials(http_request) == {
            "username": "guido@imsweb.com",
            "first_name": "guido",
            "last_name": "van rossum",
            "email": "noreply@imsweb.com",
            "idp": "https://imsweb.com/ims-external",
        }

    def test_get_user_by_id(self, http_request):
        http_request.environ[CHALLENGE_HEADER_KEY] = "fred"
        api.user.get(username=test_user_id)
