"""
MBTA API SSL Fix

This module provides a modified version of the pymbta3 library that handles SSL issues
by either using curl_cffi or disabling SSL verification in requests.
"""

import os
from functools import wraps
import inspect
from typing import Union, Optional, Dict, Any

# Option 1: Using curl_cffi
try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

# Option 2: Using standard requests with verification disabled
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)


class PyMBTA3SSL(object):
    """
    Modified version of PyMBTA3 class that handles SSL issues.
    """
    _MBTA_V3_API_URL = 'https://api-v3.mbta.com'

    def __init__(self, key: str = None, use_curl_cffi: bool = True):
        """ Initialize the class
        Keyword Arguments:
            key: MBTA v3 api key
            use_curl_cffi: Whether to use curl_cffi (if available) or requests with SSL verification disabled
        """
        if key is None:
            key = os.getenv('MBTA_API_KEY')
        if not key or not isinstance(key, str):
            raise ValueError('The MBTA-V3 API key must be provided either through the key parameter or '
                             'through the environment variable MBTA_API_KEY. Get a free key '
                             'from the MBTA website: https://api-v3.mbta.com/')

        self.key = key
        self.use_curl_cffi = use_curl_cffi and CURL_CFFI_AVAILABLE

        if self.use_curl_cffi:
            print("Using curl_cffi for MBTA API requests with SSL verification disabled")
            self.session = curl_requests.Session(impersonate="chrome", verify=False)
        else:
            print("Using requests for MBTA API requests with SSL verification disabled")
            self.session = requests.Session()

        self.headers = {"X-API-Key": self.key, "accept": 'application/vnd.api+json'}

    @classmethod
    def _call_api_on_func(cls, func):
        """
        Decorator for forming the api call with the arguments of the function, it works by taking the arguments
        given to the function and building the url to call the api on it
        Keyword Arguments:
            func:  The function to be decorated
        """
        # Argument Handling
        argspec = inspect.getfullargspec(func)
        try:
            # Assume most of the cases have a mixed between args and named args
            positional_count = len(argspec.args) - len(argspec.defaults)
            defaults = dict(zip(argspec.args[positional_count:], argspec.defaults))
        except TypeError:
            if argspec.args:
                # No defaults
                positional_count = len(argspec.args)
                defaults = {}
            elif argspec.defaults:
                # Only defaults
                positional_count = 0
                defaults = argspec.defaults

        # Actual decorating
        @wraps(func)
        def _call_wrapper(self, *args, **kwargs):
            used_kwargs = kwargs.copy()

            # Get the used positional arguments given to the function
            used_kwargs.update(zip(argspec.args[positional_count:], args[positional_count:]))

            # Update the dictionary to include the default parameters from the function
            used_kwargs.update({k: used_kwargs.get(k, d) for k, d in defaults.items()})

            # Form the base url, the original function called must return the function name defined in the MBTA api
            function_name = func(self, *args, **kwargs)
            url = f'{PyMBTA3SSL._MBTA_V3_API_URL}/{function_name}'
            for idx, arg_name in enumerate(argspec.args[1:]):
                try:
                    arg_value = args[idx]
                except IndexError:
                    arg_value = used_kwargs[arg_name]

                if arg_value:
                    if arg_name == 'include':
                        if isinstance(arg_value, tuple) or isinstance(arg_value, list):
                            # If the argument is given as list, then we have to format it, you gotta format it nicely
                            arg_value = ','.join(arg_value)
                        url = '{}include={}'.format(url, arg_value)
                    else:
                        # Discard argument in the url formation if it was set to None (in other words, this will call
                        # the api with its internal defined parameter)
                        if isinstance(arg_value, tuple) or isinstance(arg_value, list):
                            # If the argument is given as list, then we have to format it, you gotta format it nicely
                            arg_value = ','.join(arg_value)
                        url = '{}&filter[{}]={}'.format(url, arg_name, arg_value)
            return self._handle_api_call(url)
        return _call_wrapper

    def _handle_api_call(self, url):
        """
        Handle the return call from the api and return a data and meta_data object. It raises a ValueError on problems
        url:  The url of the service
        """
        try:
            if self.use_curl_cffi:
                # Option 1: Using curl_cffi
                response = self.session.get(url, headers=self.headers)
            else:
                # Option 2: Using standard requests with verification disabled
                response = self.session.get(url, headers=self.headers, verify=False)

            json_response = response.json()
            if not json_response:
                raise ValueError('Error getting data from the api, no return was given.')

            return json_response
        except Exception as e:
            print(f"Error making API request: {str(e)}")
            raise


class PredictionsSSL(PyMBTA3SSL):
    """
    Modified version of Predictions class that handles SSL issues.
    """
    @PyMBTA3SSL._call_api_on_func
    def get(self,
            include: Union[str, list, tuple] = None,
            direction_id: Union[str, list, tuple] = None,
            latitude: Union[str, list, tuple] = None,
            longitude: Union[str, list, tuple] = None,
            radius: Union[str, list, tuple] = None,
            route_pattern: Union[str, list, tuple] = None,
            route: Union[str, list, tuple] = None,
            stop: Union[str, list, tuple] = None,
            trip: Union[str, list, tuple] = None):
        """
        List of predictions for trips.
        https://api-v3.mbta.com/docs/swagger/index.html#/Prediction/ApiWeb_PredictionController_index
        Keyword Arguments:
        :param include: Relationships to include. [schedule, stop, route, trip, vehicle, alerts]
        Includes data from related objects in the "included" keyword
        :param direction_id: Filter by direction of travel along the route.
        :param latitude: Latitude in degrees North
        :param longitude: Longitude in degrees East
        :param radius: distance in degrees
        :param route_pattern: Filter by /included/{index}/relationships/route_pattern/data/id of a trip.
        :param route: Filter by /data/{index}/relationships/route/data/id.
        :param stop: Filter by /data/{index}/relationships/stop/data/id.
        :param trip: Filter by /data/{index}/relationships/trip/data/id.
        """
        _CALL_KEY = "predictions?"
        return _CALL_KEY
