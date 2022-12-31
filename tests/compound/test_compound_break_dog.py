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

def test_match_from_borrow_bayc(compounder, ape, bayc, bakc, nft_guy, coin_guy, matcher, ape_staking, dog_guy):
	ape.mint(coin_guy, '200000 ether')
	ape.approve(compounder, 2**256 - 1, {'from':coin_guy})
	ape.transfer(compounder, '100000 ether', {'from':coin_guy})
	compounder.deposit('100000 ether', {'from':coin_guy})
	price = compounder.pricePerShare()
	assert compounder.pricePerShare() == '2 ether'

	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})

	bakc.setApprovalForAll(matcher, True, {'from':dog_guy})
	bakc.mint(dog_guy, 10)

	matcher.depositNfts([1,2,3,4,5], [], [], {'from':nft_guy})
	matcher.depositNfts([], [], [1,2,3,4,5], {'from':dog_guy})
	for i in range(5):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, compounder, dog_guy, compounder)
	assert compounder.debt() == BAKC_CAP * 5 + BAYC_CAP * 5

	compounder.batchBreakMatch([0,1,2,3,4], [False]*5, {'from':coin_guy})
	for i in range(5):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, compounder, NULL, NULL)
	matcher.depositNfts([], [], [], {'from':dog_guy})
	for i in range(5):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, compounder, dog_guy, compounder)
	compounder.batchBreakMatch([0,1,2,3,4], [True]*5, {'from':coin_guy})
	for i in range(5):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (0, NULL, NULL, NULL, NULL)