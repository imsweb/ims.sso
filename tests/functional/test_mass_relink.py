from email import message_from_bytes

import pytest
from ims.sso.interfaces import ISSOSettings
from plone import api
from transaction import commit


class TestMassRelink:
    def test_mass_relink(self, portal, browser, mock_mail, sso):
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        api.user.create(username="user1", email="noreply@imsweb.com")
        sso.set_login_name(user_id="user1", login_name="1234@not.linked")
        commit()

        browser.open(f"{api.portal.get().absolute_url()}/mass_relink")
        ctrl = browser.getControl
        ctrl(name="form.buttons.send").click()

        assert len(mock_mail.messages) == 1
        msg = message_from_bytes(mock_mail.messages[0])
        assert "This link will expire" in msg.get_payload()

    def test_duplicates(self, portal, browser, sso):
        """This should hide the send button"""
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        api.user.create(username="user1", email="noreply@imsweb.com")
        sso.set_login_name(user_id="user1", login_name="1@not.linked")
        api.user.create(username="user2", email="noreply@imsweb.com")
        sso.set_login_name(user_id="user2", login_name="2@not.linked")
        commit()

        browser.open(f"{api.portal.get().absolute_url()}/mass_relink")
        ctrl = browser.getControl
        with pytest.raises(LookupError):
            ctrl(name="form.buttons.send").click()
