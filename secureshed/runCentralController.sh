export FLASK_APP=central_controller
export FLASK_ENV=development

export CENCON_CONFIG=central_controller/configuration.json
export CENCON_DB=central_controller/ccontroller.db

python3 -m flask run -p 2020 -h 0.0.0.0 --eager-loading --no-reload
