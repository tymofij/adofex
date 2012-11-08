# This is here to save few keystrokes on common operations

# .PHONY: run

run:
	@./manage.py runserver 0.0.0.0:8000

shell:
	@./manage.py shell

dbshell:
	@./manage.py dbshell

install:
	./manage.py syncdb --noinput
	./manage.py migrate
	./manage.py txcreatenoticetypes
	./manage.py txlanguages
	./manage.py mzlanguages
	./manage.py check_permissions
	./manage.py collectstatic

static:
	@./manage.py collectstatic
