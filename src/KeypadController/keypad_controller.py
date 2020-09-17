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
# pylint: disable=C0413
import sys
sys.path.insert(0, '..')
from KeypadApp import KeypadApp


## Keypad controller application entry point.
def Main():
    keypadApp = KeypadApp()
    keypadApp.start_app()
    keypadApp.stop_app()

if __name__ == "__main__":
    Main()