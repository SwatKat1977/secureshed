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
import flask
from KeypadController.KeypadApp import KeypadApp


## Flask startup function.
#  @param test_config Unused.
def create_app(test_config=None):
    # pylint: disable=W0613,E1101,C0103

    app = flask.Flask(__name__)

    keypadApp = KeypadApp()
    keypadApp.StartApp(app)

    return app
