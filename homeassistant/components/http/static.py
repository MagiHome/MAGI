"""Static file handling for HTTP component."""
import asyncio
import re

from aiohttp import hdrs
from aiohttp.web import FileResponse
from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_urldispatcher import StaticResource
from yarl import unquote

from .const import KEY_DEVELOPMENT

_FINGERPRINT = re.compile(r'^(.+)-[a-z0-9]{32}\.(\w+)$', re.IGNORECASE)


class CachingStaticResource(StaticResource):
    """Static Resource handler that will add cache headers."""

    @asyncio.coroutine
    def _handle(self, request):
        filename = unquote(request.match_info['filename'])
        try:
            # PyLint is wrong about resolve not being a member.
            # pylint: disable=no-member
            filepath = self._directory.joinpath(filename).resolve()
            if not self._follow_symlinks:
                filepath.relative_to(self._directory)
        except (ValueError, FileNotFoundError) as error:
            # relatively safe
            raise HTTPNotFound() from error
        except Exception as error:
            # perm error or other kind!
            request.app.logger.exception(error)
            raise HTTPNotFound() from error

        if filepath.is_dir():
            return (yield from super()._handle(request))
        elif filepath.is_file():
            return CachingFileResponse(filepath, chunk_size=self._chunk_size)
        else:
            raise HTTPNotFound


class CachingFileResponse(FileResponse):
    """FileSender class that caches output if not in dev mode."""

    def __init__(self, *args, **kwargs):
        """Initialize the hass file sender."""
        super().__init__(*args, **kwargs)

        orig_sendfile = self._sendfile

        @asyncio.coroutine
        def sendfile(request, fobj, count):
            """Sendfile that includes a cache header."""
            if not request.app[KEY_DEVELOPMENT]:
                cache_time = 31 * 86400  # = 1 month
                self.headers[hdrs.CACHE_CONTROL] = "public, max-age={}".format(
                    cache_time)

            yield from orig_sendfile(request, fobj, count)

        # Overwriting like this because __init__ can change implementation.
        self._sendfile = sendfile


@asyncio.coroutine
def staticresource_middleware(app, handler):
    """Middleware to strip out fingerprint from fingerprinted assets."""
    @asyncio.coroutine
    def static_middleware_handler(request):
        """Strip out fingerprints from resource names."""
        if not request.path.startswith('/static/'):
            return handler(request)

        fingerprinted = _FINGERPRINT.match(request.match_info['filename'])

        if fingerprinted:
            request.match_info['filename'] = \
                '{}.{}'.format(*fingerprinted.groups())

        return handler(request)

    return static_middleware_handler
