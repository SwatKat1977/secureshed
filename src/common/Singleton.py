'''
Copyright 2019 Secure Shed Project Dev Team

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


## A non-thread-safe helper class to ease implementing singletons.  This should
#  be used as a decorator -- not a metaclass -- to the class that should be a
#  singleton.
#  The decorated class can define one `__init__` function that takes only the
#  `self` argument. Also, the decorated class cannot be inherited from. Other
#  than that, there are no restrictions that apply to the decorated class.
#  To get the singleton instance, use the `Instance` method. Trying to use
# `__call__` will result in a `TypeError` being raised.
class Singleton(object):

    ## Class default constructor.
    #  @param self The object pointer.
    #  @param decorated Class to decorate.
    def __init__(self, decorated):
        ## Class to be decorated.
        self.__decorated = decorated


    ## Returns the singleton instance. Upon its first call, it creates a new
    #  instance of the decorated class and calls its `__init__` method.
    #  On all subsequent calls, the already created instance is returned.
    #  @param self The object pointer.
    #  @return Returns an instance of the decorated class.
    def Instance(self):
        try:
            return self.__instance
        except AttributeError:
            self.__instance = self.__decorated()
            return self.__instance


    ## Override the call operator to stop it being called.  Any attempt to call
    #  it will throw a TypeError exception. d
    #  @param self The object pointer.
    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')


    ## Check the instance is same as the decorated class.
    #  @param self The object pointer.
    #  @param inst Object instance to check.
    #  @return Returns True if is an instance or False if not.
    def __instancecheck__(self, inst):
        return isinstance(inst, self.__decorated)
