export QUART_APP=central_controller
export QUART_ENV=development

BASEDIR=${PWD}
export PYTHONPATH=${PWD}/central_controller:${PWD}/common
export SECURESHED_CONTROLLER_CONFIG=../config_files/central_controller/settings.cfg
export SECURESHED_CONTROLLER_CONFIG_REQUIRED=1
export SECURESHED_CONTROLLER_DB=./controller.db

python3 -m quart run -p 2020 -h 0.0.0.0 --no-reload
