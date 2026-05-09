.PHONY: install lint format test test-integration up down clean smoke dump-caseB ps logs help

help:
	@task --list

install:
	task install

lint:
	task lint

format:
	task format

test:
	task test

test-integration:
	task test:integration

up:
	task up

down:
	task down

clean:
	task clean

smoke:
	task smoke

dump-caseB:
	task dump:caseB

ps:
	task ps

logs:
	task logs
