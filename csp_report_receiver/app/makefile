init:
	pip install -r requirements.txt
lint:
	python -m flake8 .
format:
	black .
	make lint
migrate:
	python craft migrate
reset:
	python craft migrate:reset
serve:
	python craft serve
test:
	python craft migrate -c testing &&\
	coverage run -m pytest -s -vv tests &&\
	coverage report -m
