import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv
import math

AMOUNT = 1000000000
# uint128 _total, address[4] memory _adds, bool _claimGamma
def test_split_a_a_a_a(split, accounts):
	arr = [accounts[0]] * 4
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT and res[1] == 0 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == AMOUNT and res[1] == 0 and res[2] == 0 and res[3] == 0

def test_split_b_a_a_a(split, accounts):
	arr = [accounts[1], accounts[0], accounts[0],  accounts[0]]
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 1 * AMOUNT // 10 and res[1] == 9 * AMOUNT // 10 and res[2] == 0 and res[3] == 0

def test_split_a_b_a_a(split, accounts):
	arr = [accounts[0], accounts[1], accounts[0],  accounts[0]]
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 9 * AMOUNT // 10 and res[1] == AMOUNT // 10 and res[2] == 0 and res[3] == 0

def test_split_a_a_b_a(split, accounts):
	arr = [accounts[0], accounts[0], accounts[1],  accounts[0]]
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT and res[1] == 0 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 6 * AMOUNT // 10 and res[1] == 0 and res[2] == 4 * AMOUNT // 10 and res[3] == 0

def test_split_a_a_a_b(split, accounts):
	arr = [accounts[0], accounts[0], accounts[0],  accounts[1]]
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT and res[1] == 0 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 6 * AMOUNT // 10 and res[1] == 0 and res[2] == 0 and res[3] == 4 * AMOUNT // 10

def test_split_a_b_b_a(split, accounts):
	arr = [accounts[0], accounts[1], accounts[1],  accounts[0]]
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0

def test_split_a_b_a_b(split, accounts):
	arr = [accounts[0], accounts[1], accounts[0],  accounts[1]]
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0

def test_split_a_a_b_b(split, accounts):
	arr = [accounts[0], accounts[0], accounts[1],  accounts[1]]
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT and res[1] == 0 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 2 * AMOUNT // 10 and res[1] == 0 and res[2] == 8 * AMOUNT // 10 and res[3] == 0

def test_split_a_b_c_a(split, accounts):
	arr = [accounts[0], accounts[1], accounts[2], accounts[0]] 
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 5 * AMOUNT // 10 and res[1] == AMOUNT // 10 and res[2] ==  4 * AMOUNT // 10 and res[3] ==  0

def test_split_b_a_c_a(split, accounts):
	arr = [accounts[1], accounts[0], accounts[2], accounts[0]] 
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == AMOUNT // 10 and res[1] == 5 * AMOUNT // 10 and res[2] ==  4 * AMOUNT // 10 and res[3] ==  0

def test_split_a_b_a_c(split, accounts):
	arr = [accounts[0], accounts[1], accounts[0], accounts[2]] 
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 5 * AMOUNT // 10 and res[1] == AMOUNT // 10 and res[2] ==  0 and res[3] ==  4 * AMOUNT // 10

def test_split_a_a_b_c(split, accounts):
	arr = [accounts[0], accounts[0], accounts[1], accounts[2]] 
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT and res[1] == 0 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == 2 * AMOUNT // 10 and res[1] == 0 and res[2] ==  4 * AMOUNT // 10 and res[3] ==  4 * AMOUNT // 10


def test_split_a_b_c_d(split, accounts):
	arr = [accounts[0], accounts[1], accounts[2], accounts[3]] 
	res = split.smartSplit(AMOUNT, arr, False)
	assert res[0] == AMOUNT // 2 and res[1] == AMOUNT // 2 and res[2] == 0 and res[3] == 0
	res = split.smartSplit(AMOUNT, arr, True)
	assert res[0] == AMOUNT // 10 and res[1] == AMOUNT // 10 and res[2] ==  4 * AMOUNT // 10 and res[3] ==  4 * AMOUNT // 10
