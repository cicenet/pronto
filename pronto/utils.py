# coding: utf-8
"""
pronto.utils
============

This module contains some functions that are used in different parts
of the pronto library, as well as the definition of ProntoWarning.

Todo:
    * Maybe add a ProntoError class ?
"""


#def memoize(obj):
#    cache = obj.cache = {}
#
#    @functools.wraps(obj)
#    def memoizer(*args, **kwargs):
#        if args not in cache:
#            cache[args] = obj(*args, **kwargs)
#        return cache[args]
#
#    return memoizer



import functools
import itertools
import errno
import os
import signal
import atexit

try:
    itertools.filterfalse = itertools.ifilterfalse
except AttributeError:
    pass


class TimeoutError(IOError):
    pass

# def timeout(seconds=60, error_message=os.strerror(errno.ETIME)):

#     def decorator(func):

#         def _handle_timeout(signum, frame):
#             raise TimeoutError(error_message)

#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):

#             try:
#                 signal.signal(signal.SIGALRM, _handle_timeout)
#                 signal.alarm(seconds)
#             except ValueError:
#                 pass
#             try:
#                 result = func(*args, **kwargs)
#             finally:
#                 signal.alarm(0)
#             return result
#         return wrapper

#     return decorator

class classproperty(object):
    """
    A decorator that allows to set properties on class level.

    """

    def __init__(self, fget):
        self.__doc__ = fget.__doc__
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)

class ProntoWarning(Warning):
    """A warning raised by pronto.

    Example:
        >>> from pronto import Ontology
        >>> import warnings
        >>> with warnings.catch_warnings(record=True) as w:
        ...    # the following ontology always has import issues (no URI in imports)
        ...    ims = Ontology('https://raw.githubusercontent.com/beny/imzml/master/data/imagingMS.obo')
        >>> print(w[-1].category)
        <class 'pronto.utils.ProntoWarning'>

    """

    def __init__(self, *args, **kwargs):

        super(ProntoWarning, self).__init__(*args, **kwargs)
        #self.__suppress_context__ = True

def explicit_namespace(attr, nsmap):
    """Explicits the namespace in an attribute name.

    Parameters
        attr (str): the attribute with its abbreviated namespace
        nsmap (dict): the namespace map

    Example:
        >>> from pronto.utils import explicit_namespace
        >>> ns = {'owl':'http://www.w3.org/2002/07/owl#'}
        >>> explicit_namespace('owl:Class', ns)
        '{http://www.w3.org/2002/07/owl#}Class'

    """
    prefix, term = attr.split(':', 1)
    return "".join(['{', nsmap[prefix], '}', term])

def format_accession(accession, nsmap=None):
    """Formats an accession URI/string to the YY:XXXXXXX token format.

    Parameters:
        accession (str): the URI to be formatted
        nsmap (dict): namespaces that can be found at the beginning of the
            accession that we want to get rid of.

    Example:
        >>> from pronto.utils import format_accession
        >>> format_accession('UO_1000003')
        'UO:1000003'
        >>> ns = {'obo':'http://purl.obolibrary.org/obo/'}
        >>> format_accession('http://purl.obolibrary.org/obo/IAO_0000601', ns)
        'IAO:0000601'

    """

    if nsmap is not None:
        for v in nsmap.values():
            accession = accession.replace(v, '')

    if not accession.startswith('_'):
        accession = accession.replace('_', ':')

    return accession

def unique_everseen(iterable):
    """List unique elements, preserving order. Remember all elements ever seen."""
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add

    for element in itertools.filterfalse(seen.__contains__, iterable):
        seen_add(element)
        yield element




import multiprocessing
import multiprocessing.pool
import atexit


class _NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

class ProntoPool(multiprocessing.pool.Pool):
    """A non-daemonized pool provided for convenience.

    Allows to perform ontology parsing through a pool of non-daemonized
    pool of workers while inheriting all methods and attributes of
    multiprocessing.pool.Pool.

    Example:

        >>> from pronto import Ontology
        >>> from pronto.utils import ProntoPool
        >>> enm = [ #ontologies from the eNanoMapper project
        ... "http://purl.enanomapper.net/onto/external/chebi-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/bao-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/bfo-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/ccont-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/cheminf-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/chmo-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/efo-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/envo-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/go-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/hupson-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/iao-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/ncit-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/npo-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/oae-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/obcs-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/obi-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/pato-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/sio-slim.owl",
        ... "http://purl.enanomapper.org/onto/external/uo-slim.owl"]
        >>> pool = ProntoPool()
        >>> enm_onto = pool.map(Ontology, enm)
        >>> pool.close()



    """
    _instances = []
    Process = _NoDaemonProcess

    def __init__(self, *args, **kwargs):
        super(ProntoPool, self).__init__(*args, **kwargs)
        self._instances.append(self)

    @classmethod
    def _close_all(cls):
        for pool in cls._instances:
            pool.close()

        for pool in cls._instances:
            pool.join()

atexit.register(ProntoPool._close_all)
