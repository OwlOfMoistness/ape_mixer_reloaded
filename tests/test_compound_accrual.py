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

def test_deposit(compounder, ape, coin_guy, matcher, ape_staking, accounts, chain):
	i = 0
	for acc in accounts:
		i += 1
		ape.mint(acc, '100000 ether')
		ape.approve(compounder, 2**256 - 1, {'from':acc})
		compounder.deposit('10000 ether', {'from':acc})
		assert compounder.balanceOf(acc) == '10000 ether'
		assert compounder.totalSupply() == Wei('10000 ether') * i
		assert compounder.liquid() == Wei('10000 ether') * i
	assert compounder.pricePerShare() == '1 ether'
	pre = compounder.pricePerShare()
	for i in range(10):
		chain.sleep(86400)
		chain.mine()
		compounder.compound()
		assert compounder.pricePerShare() >= pre
		pre = compounder.pricePerShare()

def test_match_from_borrow_bayc(compounder, ape, bayc, nft_guy, coin_guy, matcher, ape_staking, chain):
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})

	liquid = compounder.liquid()
	matcher.depositNfts([1,2,3,4,5], [], [], {'from':nft_guy})
	for i in range(5):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, compounder, NULL, NULL)
	assert compounder.debt() == BAYC_CAP * 5
	assert liquid - compounder.liquid() == BAYC_CAP * 5
	assert matcher.alphaSpentCounter() == 0
	assert matcher.alphaDepositCounter() == 0
	assert matcher.alphaCurrentTotalDeposits() == 0
	pre = compounder.pricePerShare()
	for i in range(10):
		chain.sleep(86400)
		chain.mine()
		compounder.compound()
		assert compounder.pricePerShare() >= pre
		pre = compounder.pricePerShare()
		compounder.claimNftStaking([0,1,2,3,4], {'from':coin_guy})
		assert compounder.pricePerShare() >= pre
		pre = compounder.pricePerShare()
	
def test_withdraw_all(compounder, ape, bayc, nft_guy, coin_guy, matcher, ape_staking, chain, accounts):
	with reverts('typed error: 0x9acaefc7'):
		for acc in accounts:
			compounder.withdraw({'from':acc})
			assert compounder.balanceOf(acc) == 0
	compounder.batchBreakMatch([0,1,2,3,4], [True]*5, {'from':coin_guy})
	for acc in accounts:
		if compounder.balanceOf(acc) > 0:
			compounder.withdraw({'from':acc})
		assert compounder.balanceOf(acc) == 0
	assert compounder.debt() == 0
	assert compounder.totalUserDebt() == 0
	assert compounder.totalSupply() == 0
	assert compounder.liquid() <= '0.00001 ether'
	assert compounder.pricePerShare() == '1 ether'
	compounder.deposit('10000 ether', {'from':coin_guy})
	assert math.isclose(compounder.pricePerShare(), Wei('1 ether'))
