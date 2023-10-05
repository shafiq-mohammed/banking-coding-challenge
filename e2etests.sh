#!/bin/bash

echo New Account Alice:

curl -s -H "Content-Type: application/json" -X POST -d '{"full_name": "alice", "email_address":"alicekmz@example.com","password":"alice@1233"}' http://localhost:5000/api/v1/signup

echo New Account Bob:

curl -s -H "Content-Type: application/json" -X POST -d '{"full_name": "bob", "email_address":"bobbkkm@example.com","password":"bob@1233"}' http://localhost:5000/api/v1/signup

echo Login Alice:

ALICETOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"email_address":"alicekmz@example.com","password":"alice@1233"}' http://localhost:5000/api/v1/login | jq -r ".access_token")

echo Login Bob:

BOBTOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"email_address":"bobbkkm@example.com","password":"bob@1233"}' http://localhost:5000/api/v1/login | jq -r ".access_token")

echo Get Account Alice:

ALICE=$(curl -s -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/account -H "Authorization: JWT $ALICETOKEN" | jq -r ".identity")
echo $ALICE 
ALICEBALANCE=$(curl -s -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/account -H "Authorization: JWT $ALICETOKEN" | jq -r ".balance")
echo $ALICEBALANCE

echo Get Account Bob:

BOB=$(curl -s -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/account -H "Authorization: JWT $BOBTOKEN" | jq -r ".identity")
echo $BOB 

echo Deposit 100 dollars Alice:

ALICEDEPOSIT=$(curl -s -H "Content-Type: application/json" -X POST http://localhost:5000/api/v1/deposit -H "Authorization: JWT $ALICETOKEN" -d '{"account_id": "'"$ALICE"'", "amount": 10000}' | jq -r ".data")

if [ "$ALICEDEPOSIT" = "10000" ]
then
echo Success
else
echo $ALICEDEPOSIT
echo Deposit Failed
exit 1
fi

echo Get Account Alice:

curl -s -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/account -H "Authorization: JWT $ALICETOKEN"

echo Transfer 10 dollars to Bob:

TRANSFER='{"amount": 1000,"source_account_id": "'$ALICE'", "target_account_id": "'$BOB'"}'
echo $TRANSFER
curl -s -H "Content-Type: application/json" -X POST http://localhost:5000/api/v1/transfer -H "Authorization: JWT $ALICETOKEN" -d "$TRANSFER"

echo Get Account Alice:

curl -s -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/account -H "Authorization: JWT $ALICETOKEN"

echo Get Account Bob:

curl -s -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/account -H "Authorization: JWT $BOBTOKEN"


echo Transfer 10 dollars to unknown:

TRANSFER='{"amount": 1000, "source_account_id": "'$ALICE'", "target_account_id": "0db7b668-2856-4c86-83cf-a0b42c80d935"}'
RESULT=$(curl -s -H "Content-Type: application/json" -X POST http://localhost:5000/api/v1/transfer -H "Authorization: JWT $ALICETOKEN" -d "$TRANSFER" | jq -r ".error")

EXPECTED_ERROR="Account not found: 0db7b668-2856-4c86-83cf-a0b42c80d935"
if [ "$EXPECTED_ERROR" = "$RESULT" ]
then
echo Successfully blocked an invalid transfer
else
echo Failed, should have blocked an invalid transfer
echo $RESULT
exit 1
fi


echo Transfer more money than available:

TRANSFER='{"amount": 50000,"source_account_id": "'$ALICE'", "target_account_id": "'$BOB'"}'
RESULT=$(curl -s -H "Content-Type: application/json" -X POST http://localhost:5000/api/v1/transfer -H "Authorization: JWT $ALICETOKEN" -d "$TRANSFER" | jq -r ".error")

EXPECTED_ERROR="Insufficient funds"
if [ "$EXPECTED_ERROR" = "$RESULT" ]
then
    echo Successfully blocked an overdraw transfer
else
    echo Failed, should have blocked an overdraw transfer
    echo $RESULT
    exit 1
fi


echo Login with invalid email:

INVALIDTOKEN=$(curl -s -H "Content-Type: application/json" -X POST -d '{"email_address":"Invalid-user@example.com","password":"alice@1233"}' http://localhost:5000/api/v1/login | jq -r ".error")

EXPECTED_ERROR="Invalid credentials"
if [ "$EXPECTED_ERROR" = "$INVALIDTOKEN" ]
then
    echo Successfully blocked login with invalid email
else
    echo Failed, should have blocked login with invalid email
    echo $INVALIDTOKEN
    exit 1
fi


echo Login with incorrect password:

EXPECTED_ERROR="Bad username or password"
WRONGPASS=$(curl -s -H "Content-Type: application/json" -X POST -d '{"email_address":"alicekmz@example.com","password":"wrongpassword"}' http://localhost:5000/api/v1/login | jq -r ".msg")

if [ "$EXPECTED_ERROR" = "$WRONGPASS" ]
then
    echo Successfully blocked login with incorrect password
else
    echo Failed, should have blocked login with incorrect password
    echo $WRONGPASS
    exit 1
fi


echo Deposit negative amount:

NEGDEPOSIT=$(curl -s -H "Content-Type: application/json" -X POST http://localhost:5000/api/v1/deposit -H "Authorization: JWT $ALICETOKEN" -d '{"account_id": "'"$ALICE"'", "amount": -5000}' | jq -r ".error")

EXPECTED_ERROR="Invalid deposit amount"
if [ "$EXPECTED_ERROR" = "$NEGDEPOSIT" ]
then
    echo Successfully blocked negative deposit
else
    echo Failed, should have blocked negative deposit
    echo $NEGDEPOSIT
    exit 1
fi
