from urllib.parse import urlparse

def resolve_transaction_name(transaction: str, domain: str, uri: str) -> str:
    ans = ""
    if transaction:
        ans = transaction
    elif uri:
        try:
            parsed_uri = urlparse(uri)
            if parsed_uri.path:
                path = parsed_uri.path
                segments = path.strip('/').split('/')
                max_supported_segments = min(2, len(segments))
                before_join = '/'.join(segments[:max_supported_segments])
                ans = '/' + before_join
            else:
                ans = "/"
        except Exception as e:
            pass

    if domain:
        if ans.startswith('/'):
            ans = ans[1:]
        ans = domain + "/" + ans

    if not ans:
        return "unknown"

    if len(ans) > 255:
        return ans[:255]

    return ans
