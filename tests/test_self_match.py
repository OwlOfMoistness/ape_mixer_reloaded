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

def test_single_bayc_self_match(matcher, ape, bayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':nft_guy})
	ape.mint(nft_guy, '1000000 ether')
	pre = ape.balanceOf(ape_staking)

	matcher.matchNftsSelf([1], [], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == BAYC_CAP
	assert bayc.ownerOf(1) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, 1, nft_guy, NULL, True)

def test_single_mayc_self_match(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)

	matcher.matchNftsSelf([], [2], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == MAYC_CAP
	assert mayc.ownerOf(2) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, 2, nft_guy, NULL, True)

def test_many_bayc_self_match(matcher, ape, bayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	pre = ape.balanceOf(ape_staking)

	matcher.matchNftsSelf([3,4,5], [], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == BAYC_CAP * 3
	(self, dogless, ids, pO, dO) = matcher.matches(2)
	assert (dogless & 1, ids, pO, dO, self) == (1, 3, nft_guy, NULL, True)
	(self, dogless, ids, pO, dO) = matcher.matches(3)
	assert (dogless & 1, ids, pO, dO, self) == (1, 4, nft_guy, NULL, True)
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (1, 5, nft_guy, NULL, True)

def test_many_mayc_self_match(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	pre = ape.balanceOf(ape_staking)

	matcher.matchNftsSelf([], [6,7,8], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == MAYC_CAP * 3
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (0, 6, nft_guy, NULL, True)
	(self, dogless, ids, pO, dO) = matcher.matches(6)
	assert (dogless & 1, ids, pO, dO, self) == (0, 7, nft_guy, NULL, True)
	(self, dogless, ids, pO, dO) = matcher.matches(7)
	assert (dogless & 1, ids, pO, dO, self) == (0, 8, nft_guy, NULL, True)

def test_smart_break(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	ape.approve(compounder, 2 ** 256 - 1, {'from':nft_guy})
	compounder.deposit('100000 ether', {'from':nft_guy})
	debt = compounder.debt()
	matcher.batchSmartBreakMatch([5], [[False, True, False]], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (0, 6, nft_guy, NULL, False)
	assert compounder.debt() - debt == '2042 ether'