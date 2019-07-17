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
import time
from KeypadAPIEndpoint import KeypadAPIThread


### application/json
### https://stackoverflow.com/questions/23110383/how-to-dynamically-build-a-json-object-with-python

server = KeypadAPIThread(5000)
server.start()

#while True:
#    pass

time.sleep(20)
server.shutdown()
