run:
	@./manage.py runserver 0.0.0.0:8000

shell:
	@./manage.py shell

dbshell:
	@./manage.py dbshell

test_script = ./manage.py test actionlog projects releases resources teams \
    autofetch charts cla datastores gtranslate locks lotte priorities \
    suggestions timeline txapps watches webhooks widgets --settings=settings_test

test:
	$(test_script)

test_coverage:
	coverage run $(test_script)

static:
	@./manage.py collectstatic
