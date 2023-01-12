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

def test_expected_return(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, chain, compounder, smooth, ape_staking):
	ape.mint(nft_guy, '1000000 ether')
	ape.mint(coin_guy, '1000000 ether')
	bayc.mint(nft_guy, 10)
	mayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	ape.approve(compounder, 2 ** 256 - 1, {'from':nft_guy})
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})
	compounder.deposit('28500 ether', {'from':coin_guy})
	matcher.depositNfts([1,2],[3,4,5],[6,7], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, (6 << 48) + 1, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (1, (7 << 48) + 2, nft_guy, nft_guy, False)
	setup = [True, False, True]
	bayc.mint(nft_guy, 10)
	mayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	matcher.depositNfts([11,12],[13,14,15],[16,17], {'from':nft_guy})
	pre = ape.balanceOf(nft_guy)
	matcher.batchSmartBreakMatch([0,1,2,3,4], [setup] * 5, {'from':nft_guy})
	assert bayc.ownerOf(1) == nft_guy
	assert bayc.ownerOf(2) == nft_guy
	assert mayc.ownerOf(3) == nft_guy
	assert mayc.ownerOf(4) == nft_guy
	assert mayc.ownerOf(5) == nft_guy
	assert bakc.ownerOf(6) == nft_guy
	assert bakc.ownerOf(7) == nft_guy