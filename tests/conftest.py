import pytest
from plone import api
from pytest_plone import fixtures_factory
from zope.component import getUtility

from ims.users.interfaces import ISingleSignonUtility
from ims.users.testing import FUNCTIONAL_TESTING
from ims.users.testing import INTEGRATION_TESTING

PACKAGE_NAME = "ims.users"
test_login = "guido"
test_user_id = "someCrazyUserIdForGuido"

pytest_plugins = ["pytest_plone"]

globals().update(
    fixtures_factory((
        (FUNCTIONAL_TESTING, "functional"),
        (INTEGRATION_TESTING, "integration"),
    ))
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
