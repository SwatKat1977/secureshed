export FLASK_APP=centralController
export FLASK_ENV=development

export CENCON_CONFIG=centralController/configuration.json
export CENCON_DB=centralController/ccontroller.db

python -m flask run -p 2020 --eager-loading --no-reload