from plone import api


class TestVocabulary:
    def test_active_status(self, portal):
        vocab = api.portal.get_vocabulary(name="ims.sso.active_status")
        assert len(vocab) == 3
        assert "active" in vocab
        assert "inactive" in vocab
        assert "disabled" in vocab
        assert "foobar" not in vocab
