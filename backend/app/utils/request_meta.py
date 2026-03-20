from fastapi import Request


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        first = forwarded_for.split(',')[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return request.client.host
    return 'unknown'


def is_https_request(request: Request) -> bool:
    forwarded_proto = request.headers.get('x-forwarded-proto')
    if forwarded_proto:
        first = forwarded_proto.split(',')[0].strip().lower()
        if first:
            return first == 'https'
    return request.url.scheme.lower() == 'https'

