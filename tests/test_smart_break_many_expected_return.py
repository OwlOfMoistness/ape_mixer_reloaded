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

def test_expected_return(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, chain):
	ape.mint(nft_guy, '1000000 ether')
	ape.mint(coin_guy, '1000000 ether')
	bayc.mint(nft_guy, 10)
	mayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':nft_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})

	matcher.depositApeToken([2,3,2], {'from':nft_guy})
	matcher.depositNfts([1,2],[3,4,5],[6,7], {'from':nft_guy})
	matcher.depositApeToken([2,3,2], {'from':coin_guy})
	setup = [False, True] * 2
	pre = ape.balanceOf(nft_guy)
	matcher.batchSmartBreakMatch([0,1,2,3,4], [setup] * 5, {'from':nft_guy})
	assert ape.balanceOf(nft_guy) - pre == 2 * BAYC_CAP + 3 * MAYC_CAP + 2 * BAKC_CAP