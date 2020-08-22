export FLASK_APP=CentralController
export FLASK_ENV=development

export CENCON_CONFIG=CentralController/configuration.json
export CENCON_DB=CentralController/ccontroller.db

python3 -m flask run -p 2020 -h 0.0.0.0 --eager-loading --no-reload
