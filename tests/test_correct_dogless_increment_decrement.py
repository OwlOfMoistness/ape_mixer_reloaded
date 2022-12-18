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

def test_dog(matcher, ape, bayc, mayc, bakc, nft_guy, chain):
	ape.mint(nft_guy, '1000000 ether')
	bayc.mint(nft_guy, 10)
	mayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':nft_guy})

	matcher.depositApeToken([2,4,4], {'from':nft_guy})
	matcher.depositNfts([1],[2,3,4,5],[6,7], {'from':nft_guy})
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, (6 << 48) + 1, nft_guy, nft_guy, nft_guy, nft_guy)
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, (7 << 48) + 2, nft_guy, nft_guy, nft_guy, nft_guy)
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(2)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 5, nft_guy, nft_guy, NULL, NULL)
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(3)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 4, nft_guy, nft_guy, NULL, NULL)
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 3, nft_guy, nft_guy, NULL, NULL)
	assert matcher.doglessMatchCounter() == 3
	chain.sleep(8 * 86400)
	chain.mine()
	matcher.batchBreakMatch([1,0,2,3], [True, True, True, True],{'from':nft_guy})
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (False, 0, 0, NULL, NULL, NULL, NULL)
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (False, 0, 0, NULL, NULL, NULL, NULL)
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(2)
	assert (active, pri, ids, pO, pT, dO, dT) == (False, 0, 0, NULL, NULL, NULL, NULL)
	(active, pri, _, _, ids, pO, pT, dO, dT) = matcher.matches(3)
	assert (active, pri, ids, pO, pT, dO, dT) == (False, 0, 0, NULL, NULL, NULL, NULL)
	assert matcher.doglessMatchCounter() == 1
	assert matcher.doglessMatches(0) == 4
	matcher.batchBreakMatch([4], [True],{'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0
	matcher.depositNfts([], [], [8], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0
