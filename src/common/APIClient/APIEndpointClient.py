'''
Copyright 2019-2020 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import enum
import requests


class APIEndpointClient(object):

    ## Property getter : Last reported error message.
    @property
    def LastErrMsg(self):
        return self._lastErrMsg


    class __MethodType(enum.Enum):
        Get = 1
        Post = 2


    def __init__(self, urlBase):
        self.__urlBase = urlBase
        self.__userAgent = 'Default Agent'
        self._lastErrMsg = ''


    def SendGetMsg(self, route, mimeType, additionalHeaders = None,
        body = None):

        self._lastErrMsg = ''
        return self.__SendMessage(route, self.__MethodType.Get, mimeType,
            additionalHeaders, body)


    def SendPostMsg(self, route, mimeType, additionalHeaders = None,
        body = None):

        self._lastErrMsg = ''
        return self.__SendMessage(route, self.__MethodType.Post, mimeType,
            additionalHeaders, body)


    def __SendMessage(self, route, clientMethodType, mimeType,
        additionalHeaders, body):

        url = f'{self.__urlBase}{route}'

        # Firstly build the header dictionary with the header elements that
        # will always exist - user-agent and content-type.
        headerDict = \
        {
            'User-Agent': self.__userAgent,
            'Content-Type': mimeType
        }

        # If there are any additional header elements, if so add them to the
        # initial header dictionary.
        if additionalHeaders is not None:
            headerDict.update(additionalHeaders)

        try:
            if clientMethodType == self.__MethodType.Get:
                pass

            elif clientMethodType == self.__MethodType.Post:
                return requests.post(url, data=body, headers=headerDict)

        except requests.exceptions.ConnectionError:
            self._lastErrMsg = 'A Connection error occurred.'

        except requests.exceptions.ProxyError:
            self._lastErrMsg = 'A proxy error occurred.'

        except requests.exceptions.Timeout:
            self._lastErrMsg = 'The request timed out.'

        except requests.exceptions.RequestException as exceptionInst:
            self._lastErrMsg = exceptionInst

        # If you have fallen through to this part of then something has gone
        # wrong so return None to identify this as self.__lastErrMsg should
        # have been set.
        return None
