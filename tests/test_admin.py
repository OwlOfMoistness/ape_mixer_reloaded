import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv

NULL = "0x0000000000000000000000000000000000000000"

def test_revert_operator(matcher, admin):
	assert matcher.smoothOperator() != NULL
	with reverts():
		matcher.setOperator(admin, {'from':admin})

def test_exec_smooth(smooth, admin, bayc, mayc, bakc, ape):
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(bayc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(mayc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(bakc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(ape,'', {'from':admin})
	smooth.exec(admin,'', {'from':admin})