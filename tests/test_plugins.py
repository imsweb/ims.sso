from plone import api

test_login = "guido"
test_user_id = "someCrazyUserIdForGuido"


class TestPlugins:
    def test_find_user_by_plugin(self, plugin):
        api.user.get(username=test_user_id).setMemberProperties({"active": "active"})
        assert plugin.authenticateCredentials({
            "username": test_login + "@adfs.imsweb.com",
            "idp": "https://www.okta.com",
        }) == (test_user_id, test_login + "@adfs.imsweb.com")

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

    def test_get_user_by_id(self, http_request, shib_header_user):
        http_request.environ[shib_header_user] = "fred"
        api.user.get(username=test_user_id)
