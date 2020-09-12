export FLASK_APP=centralController
export FLASK_ENV=development

export CENCON_CONFIG=centralController/configuration.json
export CENCON_DB=centralController/ccontroller.db

python3 -m flask run -p 2020 -h 0.0.0.0 --eager-loading --no-reload
