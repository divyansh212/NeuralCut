"""Factory selects mock vs live so the rest of the code never branches on mode."""

from ..config import settings


def get_providers():
    if settings.PROVIDER_MODE == "live":
        from . import live
        return live.ScriptLive(), live.ImageLive(), live.VoiceLive()
    from . import mock
    return mock.ScriptMock(), mock.ImageMock(), mock.VoiceMock()
