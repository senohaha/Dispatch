import sys
import os

from subprocess import Popen, PIPE
import six
from six import iteritems
from six.moves.configparser import NoSectionError
import json
from twisted.web import resource


from scrapyd.config import Config


class JsonResource(resource.Resource):

    json_encoder = json.JSONEncoder()

    def render(self, txrequest):
        r = resource.Resource.render(self, txrequest)
        return self.render_object(r, txrequest)

    def render_object(self, obj, txrequest):
        r = self.json_encoder.encode(obj) + "\n"
        txrequest.setHeader('Content-Type', 'application/json')
        txrequest.setHeader('Access-Control-Allow-Origin', '*')
        txrequest.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, PUT, DELETE')
        txrequest.setHeader('Access-Control-Allow-Headers',' X-Requested-With')
        txrequest.setHeader('Content-Length', len(r))
        return r


def native_stringify_dict(dct_or_tuples, encoding='utf-8', keys_only=True):
    """Return a (new) dict with unicode keys (and values when "keys_only" is
    False) of the given dict converted to strings. `dct_or_tuples` can be a
    dict or a list of tuples, like any dict constructor supports.
    """
    d = {}
    for k, v in iteritems(dict(dct_or_tuples)):
        k = _to_native_str(k, encoding)
        if not keys_only:
            if isinstance(v, dict):
                v = native_stringify_dict(v, encoding=encoding, keys_only=keys_only)
            elif isinstance(v, list):
                v = [_to_native_str(e, encoding) for e in v]
            else:
                v = _to_native_str(v, encoding)
        d[k] = v
    return d
def _to_native_str(text, encoding='utf-8', errors='strict'):
    if isinstance(text, str):
        return text
    if not isinstance(text, (bytes, six.text_type)):
        raise TypeError('_to_native_str must receive a bytes, str or unicode '
                        'object, got %s' % type(text).__name__)
    if six.PY2:
        return text.encode(encoding, errors)
    else:
        return text.decode(encoding, errors)
