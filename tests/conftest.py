import pytest
from ims.sso.interfaces import ISingleSignonUtility, ISSOSettings
from ims.sso.testing import FUNCTIONAL_TESTING, INTEGRATION_TESTING
from plone import api
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from pytest_plone import fixtures_factory
from zope.component import getUtility

PACKAGE_NAME = "ims.sso"
test_login = "guido"
test_user_id = "someCrazyUserIdForGuido"

pytest_plugins = ["pytest_plone"]

globals().update(
    fixtures_factory(
        (
            (FUNCTIONAL_TESTING, "functional"),
            (INTEGRATION_TESTING, "integration"),
        )
    )
)


@pytest.fixture
def package_name():
    return PACKAGE_NAME


@pytest.fixture
def pas(portal):
    return api.portal.get_tool("acl_users")


@pytest.fixture
def sso(portal):
    return getUtility(ISingleSignonUtility)


@pytest.fixture
def plugin(pas):
    pas.source_users.addUser(test_user_id, test_login + "@adfs.imsweb.com", "password")
    return pas.ims_sso_plugin


@pytest.fixture
def get_setting(portal):
    def get_setting(name):
        return api.portal.get_registry_record(interface=ISSOSettings, name=name)

    return get_setting


@pytest.fixture
def shib_header_user(get_setting):
    return get_setting("shib_header_user")


@pytest.fixture
def shib_header_first_name(get_setting):
    return get_setting("shib_header_first_name")


@pytest.fixture
def shib_header_last_name(get_setting):
    return get_setting("shib_header_last_name")


@pytest.fixture
def shib_header_email(get_setting):
    return get_setting("shib_header_email")


@pytest.fixture
def shib_header_idp(get_setting):
    return get_setting("shib_header_idp")


@pytest.fixture
def shib_header_null(get_setting):
    return get_setting("shib_header_null")


@pytest.fixture
def mock_mail(portal):
    mockmailhost = MockMailHost("MailHost")

    if not getattr(mockmailhost, "smtp_host", None):
        mockmailhost.smtp_host = "localhost"

    portal.MailHost = mockmailhost
    sm = portal.getSiteManager()
    sm.registerUtility(component=mockmailhost, provided=IMailHost)

    mailhost = api.portal.get_tool("MailHost")
    api.portal.set_registry_record(
        "plone.email_from_name",
        "Portal Owner",
    )
    api.portal.set_registry_record(
        "plone.email_from_address",
        "sender@example.org",
    )
    return mailhost
