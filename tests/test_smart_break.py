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

def test_break_match_bayc(matcher, ape, bayc, smooth, nft_guy, dog_guy, coin_guy, other_guy):
	ape.mint(coin_guy, '1000000 ether')
	ape.mint(other_guy, '1000000 ether')
	bayc.mint(nft_guy, 10)
	bayc.mint(dog_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.setApprovalForAll(matcher, True, {'from':dog_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':other_guy})

	matcher.depositNfts([1], [], [], {'from':nft_guy})
	matcher.depositApeToken([1,0,0], {'from':coin_guy})
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 1, nft_guy, coin_guy, NULL, NULL)
	with reverts('ApeMatcher: !primary asset'):
		matcher.batchSmartBreakMatch([0], [False], {'from':nft_guy})
	with reverts('ApeMatcher: !alpha deposits'):
		matcher.batchSmartBreakMatch([0], [False], {'from':coin_guy})
	with reverts('!match'):
		matcher.batchSmartBreakMatch([0], [False], {'from':other_guy})
	matcher.depositNfts([11], [], [], {'from':dog_guy})
	matcher.batchSmartBreakMatch([0], [False], {'from':nft_guy})
	assert bayc.ownerOf(1) == nft_guy
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 11, dog_guy, coin_guy, NULL, NULL)
	matcher.depositApeToken([1,0,0], {'from':other_guy})
	matcher.batchSmartBreakMatch([0], [False], {'from':coin_guy})
	assert ape.balanceOf(coin_guy) == '1000000 ether'
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 11, dog_guy, other_guy, NULL, NULL)
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	matcher.batchSmartBreakMatch([0], [False], {'from':dog_guy})
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 1, nft_guy, other_guy, NULL, NULL)
	assert bayc.ownerOf(11) == dog_guy

def test_break_match_mayc(matcher, ape, mayc, smooth, nft_guy, dog_guy, coin_guy, other_guy):
	mayc.mint(nft_guy, 10)
	mayc.mint(dog_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.setApprovalForAll(matcher, True, {'from':dog_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':other_guy})

	matcher.depositNfts([], [1], [], {'from':nft_guy})
	matcher.depositApeToken([0,1,0], {'from':coin_guy})
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 1, nft_guy, coin_guy, NULL, NULL)
	with reverts('ApeMatcher: !primary asset'):
		matcher.batchSmartBreakMatch([1], [False], {'from':nft_guy})
	with reverts('ApeMatcher: !beta deposits'):
		matcher.batchSmartBreakMatch([1], [False], {'from':coin_guy})
	with reverts('!match'):
		matcher.batchSmartBreakMatch([1], [False], {'from':other_guy})
	matcher.depositNfts([], [11], [], {'from':dog_guy})
	matcher.batchSmartBreakMatch([1], [False], {'from':nft_guy})
	assert mayc.ownerOf(1) == nft_guy
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 11, dog_guy, coin_guy, NULL, NULL)
	matcher.depositApeToken([0,1,0], {'from':other_guy})
	matcher.batchSmartBreakMatch([1], [False], {'from':coin_guy})
	assert ape.balanceOf(coin_guy) == '1000000 ether'
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 11, dog_guy, other_guy, NULL, NULL)
	matcher.depositNfts([], [1], [], {'from':nft_guy})
	matcher.batchSmartBreakMatch([1], [False], {'from':dog_guy})
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 1, nft_guy, other_guy, NULL, NULL)
	assert mayc.ownerOf(11) == dog_guy

def test_break_match_bakc_on_mayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, some_guy, accounts):
	bakc.mint(dog_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':dog_guy})
	bakc.mint(some_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':some_guy})
	assert matcher.doglessMatchCounter() == 2
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	assert matcher.doglessMatchCounter() == 1
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, (3 << 48) + 1, nft_guy, other_guy, dog_guy, coin_guy)
	with reverts('ApeMatcher: !dog asset'):
		matcher.batchSmartBreakMatch([1], [False], {'from':dog_guy})
	with reverts('ApeMatcher: !dog deposit'):
		matcher.batchSmartBreakMatch([1], [False], {'from':coin_guy})
	with reverts('!match'):
		matcher.batchSmartBreakMatch([1], [False], {'from':accounts[9]})
	matcher.depositNfts([], [], [13], {'from':some_guy})
	matcher.batchSmartBreakMatch([1], [False], {'from':dog_guy})
	assert bakc.ownerOf(3) == dog_guy
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, (13 << 48) + 1, nft_guy, other_guy, some_guy, coin_guy)
	ape.mint(dog_guy, '100000 ether')
	ape.approve(matcher, 2 ** 256 - 1, {'from':dog_guy})
	matcher.depositApeToken([0,0,1], {'from':dog_guy})
	assert matcher.gammaCurrentTotalDeposits() == 1
	pre = ape.balanceOf(coin_guy)
	matcher.batchSmartBreakMatch([1], [False], {'from':coin_guy})
	assert matcher.gammaCurrentTotalDeposits() == 0
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, (13 << 48) + 1, nft_guy, other_guy, some_guy, dog_guy)
	assert ape.balanceOf(coin_guy) == pre + BAKC_CAP
	assert matcher.doglessMatchCounter() == 1

def test_break_match_bakc_on_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, some_guy, accounts):
	assert matcher.doglessMatchCounter() == 1
	matcher.depositNfts([], [], [8], {'from':dog_guy})
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, (8 << 48) + 1, nft_guy, other_guy, dog_guy, coin_guy)
	with reverts('ApeMatcher: !dog asset'):
		matcher.batchSmartBreakMatch([0], [False], {'from':dog_guy})
	with reverts('ApeMatcher: !dog deposit'):
		matcher.batchSmartBreakMatch([0], [False], {'from':coin_guy})
	with reverts('!match'):
		matcher.batchSmartBreakMatch([0], [False], {'from':accounts[9]})
	matcher.depositNfts([], [], [18], {'from':some_guy})
	matcher.batchSmartBreakMatch([0], [False], {'from':dog_guy})
	assert bakc.ownerOf(8) == dog_guy
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, (18 << 48) + 1, nft_guy, other_guy, some_guy, coin_guy)
	matcher.depositApeToken([0,0,1], {'from':dog_guy})
	pre = ape.balanceOf(coin_guy)
	matcher.batchSmartBreakMatch([0], [False], {'from':coin_guy})
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, (18 << 48) + 1, nft_guy, other_guy, some_guy, dog_guy)
	assert ape.balanceOf(coin_guy) == pre + BAKC_CAP
