# Banking Web API

## Setup System

    # install python3.9 and poetry (system specific)

    # https://www.python.org/downloads/release/python-3913/

    # https://python-poetry.org/docs/#installing-with-the-official-installer

## Setup VSCode

    unzip python-coding-challenge.zip
    cd python-coding-challenge

    # setup vscode for mypy error checking

    code --install-extension ms-pyright.pyright
    code --install-extension matangover.mypy
    code --install-extension hbenl.test-adapter-converter

    # setup venv for vscode

    python3.9 -m venv .venv
    poetry config virtualenvs.in-project true 
    poetry install

    # open project directory in vscode
    code .

## Setup Testing

    # run tests

    poetry run python -m pytest

    # run tests continuously watching for changes

    poetry run python -m ptw
    
    # run end to end tests

    bash e2etests.sh  # using curl and jq

## Run Runtime with different persistence options

    # run using in memory database 
    poetry run python main.py
    
    # run using sqlite database
    PERSISTENCE_MODULE=eventsourcing.sqlite SQLITE_DBNAME=mytest.db poetry run python main.py 

## Begin Challenge

You need to implement a banking api to handle deposits, transfers, account signups, logins, and all using secured JWT tokens.

The business logic needs to live in an event sourced application. The library chosen for this is `eventsourcing` on pip, and is included in this project. Interactions with the banking application happen within applicationmodel.py, which underling account business logic is handled in `domainmodel.py`.

The api needs to be written using flask, all libraries needed are included in this project, try to complete this project with only what is already included.

All `banking` module code should have 100% test coverage and end to end tests have been included in the `e2etest.sh` file. All python code should pass mypy and pyright static code analysis, and code analaysis should be setup with vscode if you follow the setup instructions above.

Write more end to end tests to validate that users can not perform invalid actions like transfering more money than they have, or logging in with bad account credentials. Try to think of edge cases that need covered.

Everything above has unit tests and end to end tests completed to validate you have done so successfully. Once you get those things completed, add a new api method to withdraw money from an account, using the account from domainmodel, add unit tests, and end to end tests to cover these new edge cases. Warning that this step has no unit tests or end to end tests to help you along the way.

Tip: be sure to read the documentation for both the `flask` and `eventsourcing` pip packages, they have many many pages of help available.

## Upon Completion

Delete the .venv folder generated with your virtalenvironment, then zip the folder containing all project files and email that zip back to the person that sent you this challenge.