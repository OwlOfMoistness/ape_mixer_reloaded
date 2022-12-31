import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv
import math

NULL = "0x0000000000000000000000000000000000000000"
BAYC_CAP = 10094000000000000000000
MAYC_CAP = 2042000000000000000000
BAKC_CAP = 856000000000000000000
BAYC_Q1 = 1678726800 - 1670864400
MAYC_Q1 = 1678726800 - 1670864400
BAKC_Q1 = 1678726800 - 1670864400
POOL_0_DAILY_RATE = 10500000000000000000000000 // (MAYC_Q1 // 86400)
BAYC_DAILY_RATE =   16486750000000000000000000 // (MAYC_Q1 // 86400)
MAYC_DAILY_RATE = 6671000000000000000000000 // (MAYC_Q1 // 86400)
BAKC_DAILY_RATE = 1342250000000000000000000 // (BAKC_Q1 // 86400)

def test_deposit(compounder, ape, coin_guy, matcher, ape_staking):
	ape.mint(coin_guy, '100000 ether')
	ape.approve(compounder, 2**256 - 1, {'from':coin_guy})
	compounder.deposit('50000 ether', {'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == '50000 ether'
	assert compounder.totalSupply() == '50000 ether'
	compounder.deposit('10000 ether', {'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == '60000 ether'
	assert compounder.totalSupply() == '60000 ether'

def test_withdraw(compounder, ape, coin_guy):
	compounder.withdraw('30000 ether', {'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == '30000 ether'
	assert compounder.totalSupply() == '30000 ether'
	compounder.withdraw('30000 ether', {'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == 0
	assert compounder.totalSupply() == 0

def test_deposit_and_withdraw_all(compounder, ape, coin_guy, matcher, ape_staking):
	compounder.deposit('50000 ether', {'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == '50000 ether'
	assert compounder.totalSupply() == '50000 ether'
	compounder.deposit('10000 ether', {'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == '60000 ether'
	assert compounder.totalSupply() == '60000 ether'
	compounder.withdraw({'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == 0
	assert compounder.totalSupply() == 0

def test_deposit_and_withdraw_all_1_day(compounder, ape, coin_guy, matcher, ape_staking, chain):
	compounder.deposit('60000 ether', {'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == '60000 ether'
	assert compounder.totalSupply() == '60000 ether'
	assert compounder.liquid() == '60000 ether'
	chain.sleep(86400)
	chain.mine()
	reward = ape_staking.pendingRewards(0, compounder, 0)
	compounder.compound()
	assert math.isclose(compounder.liquid(), Wei('60000 ether') + reward)
	compounder.withdraw({'from':coin_guy})
	assert compounder.balanceOf(coin_guy) == 0
	assert compounder.totalSupply() == 0

def test_deposit_and_withdraw_many_all_1_day(compounder, ape, coin_guy, matcher, ape_staking, chain, accounts):
	i = 0
	for acc in accounts:
		i += 1
		ape.mint(acc, '100000 ether')
		ape.approve(compounder, 2**256 - 1, {'from':acc})
		compounder.deposit('10000 ether', {'from':acc})
		assert compounder.balanceOf(acc) == '10000 ether'
		assert compounder.totalSupply() == Wei('10000 ether') * i
		assert compounder.liquid() == Wei('10000 ether') * i
	chain.sleep(86400 * 2)
	chain.mine()
	reward = ape_staking.pendingRewards(0, compounder, 0)
	compounder.compound()
	assert math.isclose(compounder.liquid(), Wei('10000 ether') * len(accounts) + reward)
	pre = ape.balanceOf(coin_guy)
	compounder.withdraw({'from':coin_guy})
	profit = ape.balanceOf(coin_guy) - pre - Wei('10000 ether')
	assert math.isclose(profit, reward // 30)
	assert compounder.balanceOf(coin_guy) == 0
	assert compounder.totalSupply() == Wei('10000 ether') * (len(accounts) - 1)
	assert compounder.pricePerShare() > '1 ether'