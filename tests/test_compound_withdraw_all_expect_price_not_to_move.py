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
	ape.transfer(compounder, '100000 ether', {'from':coin_guy})
	compounder.deposit('100000 ether', {'from':coin_guy})
	price = compounder.pricePerShare()
	assert compounder.pricePerShare() == '2 ether'

	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})

	liquid = compounder.liquid()
	matcher.depositNfts([1,2,3,4,5], [], [], {'from':nft_guy})

	compounder.withdraw((Wei('200000 ether') -  BAYC_CAP * 5) // 2,{'from':coin_guy})
	assert ape.balanceOf(coin_guy) == Wei('200000 ether') -  BAYC_CAP * 5
	assert compounder.getStakedTotal() == 0
	assert compounder.pricePerShare() == price
	assert compounder.debt() == BAYC_CAP * 5
	compounder.batchBreakMatch([0,1,2,3,4], [True]*5, {'from':coin_guy})
	compounder.withdraw({'from':coin_guy})
	assert ape.balanceOf(coin_guy) == Wei('200000 ether')
	assert compounder.getStakedTotal() == 0
	assert compounder.pricePerShare() == '1 ether'
	assert compounder.debt() == 0