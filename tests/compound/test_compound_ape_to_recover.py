import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts, interface
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


@pytest.mark.require_network("mainnet-fork")
def test_make_matches(compounder, ape, bayc, nft_guy, coin_guy, matcher, admin, interface):
	ape.mint(coin_guy, '300000 ether')
	ape.approve(compounder, 2**256 - 1, {'from':coin_guy})
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})

	compounder.coverSwitch({'from':admin})
	matcher.depositNfts([1,2,3,4,5], [], [], {'from':nft_guy})
	compounder.deposit('200000 ether', {'from':coin_guy})
	assert ape.balanceOf(admin) == 0
	compounder.makeMatches({'from':admin, 'gas_price':'20 gwei'})
	for i in range(5):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, compounder, NULL, NULL)
	assert ape.balanceOf(admin) > 0

@pytest.mark.require_network("mainnet-fork")
def test_break_matches(compounder, ape, bayc, nft_guy, coin_guy, matcher, admin, interface):
	pre = ape.balanceOf(admin)
	compounder.batchBreakMatch([0,1,2,3], [True] * 4, {'from':admin, 'gas_price':'20 gwei'})
	for i in range(4):
		(dogless, ids, pO, pT, dO, dT) = matcher.matches(i)
		assert (dogless & 1, pO, pT, dO, dT) == (0, NULL, NULL, NULL, NULL)
	assert ape.balanceOf(admin) - pre > 0

@pytest.mark.require_network("mainnet-fork")
def test_smart_break_matches(compounder, ape, bayc, nft_guy, coin_guy, matcher, admin, interface):
	pre = ape.balanceOf(admin)
	matcher.withdrawNfts([1,3,4,5],[],[], {'from':nft_guy})
	matcher.depositApeToken([1, 0, 0], {'from':coin_guy})
	compounder.batchSmartBreakMatch([4], [[True, True, True, True]], {'from':admin, 'gas_price':'20 gwei'})
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (dogless & 1, pO, pT, dO, dT) == (1, nft_guy, coin_guy, NULL, NULL)
	assert ape.balanceOf(admin) - pre > 0