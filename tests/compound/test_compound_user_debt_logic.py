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

def test_user_debt_smart_break(compounder, ape, bayc, bakc, nft_guy, coin_guy, matcher, ape_staking, dog_guy, admin):
	ape.mint(coin_guy, '300000 ether')
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

	matcher.depositNfts([1], [], [], {'from':nft_guy})
	for i in range(1):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, compounder, NULL, NULL)
	assert compounder.debt() == BAYC_CAP

	matcher.depositApeToken([1, 0, 0], {'from':coin_guy})

	compounder.batchSmartBreakMatch([0], [[False, True, False, False]], {'from':admin})

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, coin_guy, NULL, NULL)
	assert compounder.fundsLocked(coin_guy) == 0
	assert compounder.totalFundsLocked() == 0
