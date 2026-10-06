from django.utils.http import url_has_allowed_host_and_scheme


def safe_next_url(request, candidate, default):
    """Return `candidate` only if it points at this site; otherwise `default`.

    Prevents open-redirect attacks via ?next= / hidden "next" inputs.
    """
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return default
