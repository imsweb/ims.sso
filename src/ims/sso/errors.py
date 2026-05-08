class IMSSSOException(Exception):
    """General Exception class"""


class NoSSOMailTemplatesException(IMSSSOException):
    """No mailing templates defined"""
