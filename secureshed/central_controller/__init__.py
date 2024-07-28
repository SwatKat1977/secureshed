"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys
from quart import Quart
from application import CentralControllerApp, Application

app = Quart(__name__)

@app.before_serving
async def startup() -> None:
    """
    Code executed before Quart has started serving http requests.
    """
    app.add_background_task(SERVICE_APP.run)

@app.after_serving
async def shutdown() -> None:
    """
    Code executed after Quart has stopped serving http requests.
    """
    SERVICE_APP.stop()

SERVICE_APP = Application(app)
if not SERVICE_APP.initialise():
    sys.exit()
