export FLASK_APP=KeypadController
export FLASK_ENV=development

export CENCON_CONFIG=centralController/configuration.json
export CENCON_DB=centralController/ccontroller.db

python -m flask run -p 1100 -h 0.0.0.0 --eager-loading --no-reload
