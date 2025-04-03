from __future__ import annotations

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def resolve_transaction_name(uri: str) -> str:
    try:
        parsed_uri = urlparse(uri)
        if parsed_uri.path:
            path = parsed_uri.path
            segments = path.strip("/").split("/")
            max_supported_segments = min(2, len(segments))
            before_join = "/".join(segments[:max_supported_segments])
            ans = "/" + before_join
        else:
            ans = "/"
        return ans
    except (AttributeError, TypeError, ValueError) as exc:
        logger.warning(
            "Failed to resolve transaction name from url %s", uri, exc_info=exc
        )
        return "unknown"
