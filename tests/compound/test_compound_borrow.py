import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv
import math
115384615384615384615384
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

def test_match_from_borrow_bayc(compounder, ape, bayc, nft_guy, coin_guy, matcher, ape_staking):
	ape.mint(coin_guy, '200000 ether')
	ape.approve(compounder, 2**256 - 1, {'from':coin_guy})
	compounder.deposit('50471 ether', {'from':coin_guy})

	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})

	liquid = compounder.liquid()
	matcher.depositNfts([1,2,3,4,5], [], [], {'from':nft_guy})
	for i in range(5):
		(self, dogless, ids, pO, dO) = matcher.matches(i)
		assert (dogless & 1, pO, dO, self) == (1, nft_guy, NULL, False)
	assert compounder.debt() == BAYC_CAP * 5
	assert liquid - compounder.liquid() == BAYC_CAP * 5

def test_match_some_deposits_bayc(compounder, ape, bayc, nft_guy, coin_guy, matcher, ape_staking):
	ape.mint(coin_guy, '200000 ether')
	ape.approve(matcher, 2**256 - 1, {'from':coin_guy})
	compounder.deposit('40376 ether', {'from':coin_guy})
	liquid = compounder.liquid()
	matcher.depositNfts([6,7,8,9], [], [], {'from':nft_guy})
	for i in range(2):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 5)
		assert (dogless & 1, pO, dO, self) == (1, nft_guy, NULL, False)
	for i in range(2):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 7)
		assert (dogless & 1, pO, dO, self) == (1, nft_guy, NULL, False)
	assert compounder.debt() == BAYC_CAP * 9
	assert liquid - compounder.liquid() == BAYC_CAP * 4

def test_match_from_borrow_mayc(compounder, ape, mayc, nft_guy, coin_guy, matcher, ape_staking):
	ape.mint(coin_guy, '200000 ether')
	ape.approve(compounder, 2**256 - 1, {'from':coin_guy})
	compounder.deposit('200000 ether', {'from':coin_guy})

	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})

	liquid = compounder.liquid()
	matcher.depositNfts([], [1,2,3,4,5], [], {'from':nft_guy})
	for i in range(5):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 9)
		assert (dogless & 1, pO, dO, self) == (0, nft_guy, NULL, False)
	assert compounder.debt() == MAYC_CAP * 5 + BAYC_CAP * 9
	assert liquid - compounder.liquid() == MAYC_CAP * 5

def test_match_some_deposits_mayc(compounder, ape, mayc, nft_guy, coin_guy, matcher, ape_staking):
	ape.mint(coin_guy, '200000 ether')
	ape.approve(matcher, 2**256 - 1, {'from':coin_guy})
	liquid = compounder.liquid()
	matcher.depositNfts([], [6,7,8,9], [], {'from':nft_guy})
	for i in range(2):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 14)
		assert (dogless & 1, pO, dO, self) == (0, nft_guy, NULL, False)
	for i in range(2):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 16)
		assert (dogless & 1, pO, dO, self) == (0, nft_guy, NULL, False)
	assert compounder.debt() == MAYC_CAP * 9 + BAYC_CAP * 9
	assert liquid - compounder.liquid() == MAYC_CAP * 4

def test_no_borrow_bayc(compounder, ape, bayc, nft_guy, coin_guy, matcher, ape_staking):
	bayc.mint(nft_guy, 10)
	ape.mint(coin_guy, '200000 ether')
	liquid = compounder.liquid()
	matcher.depositNfts([11, 12], [], [], {'from':nft_guy})
	for i in range(2):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 18)
		assert (dogless & 1, pO, dO, self) == (1, nft_guy, NULL, False)
	matcher.depositNfts([13, 14], [], [], {'from':nft_guy})
	for i in range(2):
			(self, dogless, ids, pO, dO) = matcher.matches(i + 20)
			assert (dogless & 1, pO, dO, self) == (1, nft_guy, NULL, False)
	assert liquid - compounder.liquid() == BAYC_CAP  * 4
	assert compounder.debt() == MAYC_CAP * 9 + BAYC_CAP * 13

def test_no_borrow_mayc(compounder, ape, mayc, nft_guy, coin_guy, matcher, ape_staking):
	mayc.mint(nft_guy, 10)
	ape.mint(coin_guy, '200000 ether')
	liquid = compounder.liquid()
	matcher.depositNfts([], [11, 12], [], {'from':nft_guy})
	for i in range(2):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 22)
		assert (dogless & 1, pO, dO, self) == (0, nft_guy, NULL, False)
	matcher.depositNfts([], [13, 14], [], {'from':nft_guy})
	for i in range(2):
			(self, dogless, ids, pO, dO) = matcher.matches(i + 24)
			assert (dogless & 1, pO, dO, self) == (0, nft_guy, NULL, False)
	assert liquid - compounder.liquid() == MAYC_CAP * 4
	assert compounder.debt() == MAYC_CAP * 13 + BAYC_CAP * 13

def test_match_from_borrow_bakc(compounder, ape, bakc, nft_guy, coin_guy, matcher, ape_staking):
	ape.mint(coin_guy, '200000 ether')
	compounder.deposit('200000 ether', {'from':coin_guy})

	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.mint(nft_guy, 10)

	liquid = compounder.liquid()
	matcher.depositNfts([], [], [1,2,3,4,5], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(21)
	assert (dogless & 1, pO, dO, self) == (1, nft_guy, nft_guy, False)
	for i in range(4):
		(self, dogless, ids, pO, dO) = matcher.matches(i + 22)
		assert (dogless & 1, pO, dO, self) == (0, nft_guy, nft_guy, False)
	assert compounder.debt() == BAKC_CAP * 5 + MAYC_CAP * 13 + BAYC_CAP * 13
	assert liquid - compounder.liquid() == BAKC_CAP * 5

def test_repay_some(compounder, ape, bakc, nft_guy, coin_guy, matcher, ape_staking, admin, chain):
	v_price = compounder.pricePerShare()
	debt = compounder.debt()
	liquid = compounder.liquid()
	chain.sleep(86400)
	chain.mine()
	compounder.batchBreakMatch([0,1,2,3,4], [True]*5, {'from':admin})
	compounder.batchBreakMatch([9,10,11,12,13], [True]*5, {'from':admin})
	assert debt - compounder.debt() == (BAYC_CAP + MAYC_CAP) * 5
	assert compounder.liquid() - liquid > (BAYC_CAP + MAYC_CAP) * 5
	assert matcher.payments(compounder) > 0
	assert compounder.pricePerShare() > v_price
	assert compounder.debt() == BAKC_CAP * 5 + MAYC_CAP * 8 + BAYC_CAP * 8
