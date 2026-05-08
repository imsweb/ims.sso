from ims.users.ned import get_dceg_users
from ims.users.ned import get_users_by_sac


class TestNed:
    def test_dceg(self, integration):
        dceg = get_dceg_users()
        assert dceg.keys() is not None

    def test_dcp(self, integration):
        queries = [{"SAC": "HNC4"}, {"SAC": "HNC17L"}]
        dcp = get_users_by_sac({}, queries)
        assert dcp.keys() is not None
