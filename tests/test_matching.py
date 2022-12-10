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

def test_single_bayc_match(matcher, ape, bayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})
	ape.mint(coin_guy, '110000 ether')

	matcher.depositNfts([10], [], [], {'from':nft_guy})
	matcher.depositApeToken([1,0,0], {'from':coin_guy})
	assert ape.balanceOf(matcher) == 0
	assert ape.balanceOf(ape_staking) == BAYC_CAP
	assert bayc.ownerOf(10) == smooth
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 10, nft_guy, coin_guy, NULL, NULL)
	assert matcher.alphaSpentCounter() == 1

def test_single_mayc_match(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.mint(nft_guy, 10)

	matcher.depositNfts([], [5], [], {'from':nft_guy})
	matcher.depositApeToken([0,1,0], {'from':coin_guy})
	assert ape.balanceOf(matcher) == 0
	assert ape.balanceOf(ape_staking) == MAYC_CAP + BAYC_CAP
	assert mayc.ownerOf(5) == smooth
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 5, nft_guy, coin_guy, NULL, NULL)
	assert matcher.doglessMatchCounter() == 2
	assert matcher.betaSpentCounter() == 1

def test_single_bakc_bind(matcher, ape, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.mint(nft_guy, 10)

	matcher.depositNfts([], [], [5], {'from':nft_guy})
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	assert ape.balanceOf(matcher) == 0
	assert ape.balanceOf(ape_staking) == BAKC_CAP + MAYC_CAP + BAYC_CAP
	assert bakc.ownerOf(5) == smooth
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(5 << 48) + 5, nft_guy, coin_guy, nft_guy, coin_guy)

	matcher.depositNfts([], [], [6], {'from':nft_guy})
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	assert matcher.gammaDepositCounter() == 2
	assert ape.balanceOf(matcher) == 0
	assert ape.balanceOf(ape_staking) == BAKC_CAP + BAKC_CAP + MAYC_CAP + BAYC_CAP
	assert bakc.ownerOf(6) == smooth
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(6 << 48) + 10, nft_guy, coin_guy, nft_guy, coin_guy)
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 2

def test_many_bayc_match(matcher, ape, bayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	pre = ape.balanceOf(ape_staking)
	pre_nft =  bayc.balanceOf(smooth)
	assert matcher.alphaSpentCounter() == 1
	matcher.depositNfts([7,8,9], [], [], {'from':nft_guy})
	matcher.depositApeToken([3,0,0], {'from':coin_guy})
	assert bayc.balanceOf(smooth) - pre_nft == 3
	assert ape.balanceOf(ape_staking) - pre == BAYC_CAP * 3
	assert bayc.ownerOf(9) == smooth
	assert bayc.ownerOf(8) == smooth
	assert bayc.ownerOf(7) == smooth
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(2)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 7, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(3)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 9, nft_guy, coin_guy, NULL, NULL)

	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 8, nft_guy, coin_guy, NULL, NULL)

	assert matcher.alphaSpentCounter() == 2

def test_many_mayc_match(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	pre = ape.balanceOf(ape_staking)
	pre_nft =  mayc.balanceOf(smooth)
	assert matcher.betaSpentCounter() == 1
	matcher.depositNfts([], [9,7,8], [], {'from':nft_guy})
	matcher.depositApeToken([0,3,0], {'from':coin_guy})
	assert mayc.balanceOf(smooth) - pre_nft == 3
	assert ape.balanceOf(ape_staking) - pre == MAYC_CAP * 3
	assert mayc.ownerOf(9) == smooth
	assert mayc.ownerOf(8) == smooth
	assert mayc.ownerOf(7) == smooth
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(5)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 9, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(6)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 8, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(7)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 7, nft_guy, coin_guy, NULL, NULL)

	assert matcher.betaSpentCounter() == 2

def test_many_bakc_bind(matcher, ape, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	pre = ape.balanceOf(ape_staking)
	assert matcher.doglessMatchCounter() == 6
	matcher.depositNfts([], [], [1,2,3,4,7,8], {'from':nft_guy})
	matcher.depositApeToken([0,0,6], {'from':coin_guy})
	assert ape.balanceOf(matcher) == 0
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP * 6
	assert bakc.ownerOf(1) == smooth
	assert bakc.ownerOf(2) == smooth
	assert bakc.ownerOf(3) == smooth
	assert bakc.ownerOf(4) == smooth
	assert bakc.ownerOf(7) == smooth
	assert bakc.ownerOf(8) == smooth
	assert matcher.gammaDepositCounter() == 3
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(7)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(1 << 48) + 7, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(6)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(8 << 48) + 8, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(5)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(7 << 48) + 9, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(4 << 48) + 8, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(3)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(3 << 48) + 9, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(2)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(2 << 48) + 7, nft_guy, coin_guy, nft_guy, coin_guy)
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 3

def test_many_multi_match_then_dogs(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	pre = ape.balanceOf(ape_staking)
	pre_nft_b =  mayc.balanceOf(smooth)
	assert matcher.betaSpentCounter() == 2
	pre_nft_a =  bayc.balanceOf(smooth)
	assert matcher.alphaSpentCounter() == 2
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	ape.mint(coin_guy, '110000 ether')
	matcher.depositNfts([11,12,13], [14,15,16], [], {'from':nft_guy})
	matcher.depositApeToken([3,3,0], {'from':coin_guy})
	assert mayc.balanceOf(smooth) - pre_nft_b == 3
	assert bayc.balanceOf(smooth) - pre_nft_a == 3
	assert ape.balanceOf(ape_staking) - pre == MAYC_CAP * 3 + BAYC_CAP * 3
	assert mayc.ownerOf(14) == smooth
	assert mayc.ownerOf(15) == smooth
	assert mayc.ownerOf(16) == smooth
	assert bayc.ownerOf(11) == smooth
	assert bayc.ownerOf(12) == smooth
	assert bayc.ownerOf(13) == smooth
	assert matcher.alphaDepositCounter() == 3
	assert matcher.betaDepositCounter() == 3
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(8)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 11, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(9)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 13, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(10)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 12, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(11)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 14, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(12)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 16, nft_guy, coin_guy, NULL, NULL)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(13)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 15, nft_guy, coin_guy, NULL, NULL)
	assert matcher.alphaSpentCounter() == 3
	assert matcher.betaSpentCounter() == 3
	assert matcher.doglessMatchCounter() == 6

	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)
	matcher.depositNfts([], [], [11,12,13,14,17,18], {'from':nft_guy})
	matcher.depositApeToken([0,0,6], {'from':coin_guy})
	assert ape.balanceOf(matcher) == 0
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP * 6
	assert bakc.ownerOf(11) == smooth
	assert bakc.ownerOf(12) == smooth
	assert bakc.ownerOf(13) == smooth
	assert bakc.ownerOf(14) == smooth
	assert bakc.ownerOf(17) == smooth
	assert bakc.ownerOf(18) == smooth
	assert matcher.gammaDepositCounter() == 4
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(13)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(11 << 48) + 15, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(12)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(18 << 48) + 16, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(11)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(17 << 48) + 14, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(10)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(14 << 48) + 12, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(9)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(13 << 48) + 13, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(8)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(12 << 48) + 11, nft_guy, coin_guy, nft_guy, coin_guy)
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 4

def test_dogs_then_primary(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)
	matcher.depositNfts([], [], [21,22,23,24], {'from':nft_guy})
	matcher.depositApeToken([0,0,4], {'from':coin_guy})
	assert bakc.balanceOf(matcher) == 4
	assert ape.balanceOf(matcher) == BAKC_CAP * 4
	assert matcher.gammaDepositCounter() == 5
	assert matcher.gammaCurrentTotalDeposits() == 4
	assert matcher.doglessMatchCounter() == 0

	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	matcher.depositNfts([21,22,23], [24], [], {'from':nft_guy})
	matcher.depositApeToken([3,1,0], {'from':coin_guy})
	assert bakc.balanceOf(matcher) == 0
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert ape.balanceOf(matcher) == 0
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.betaCurrentTotalDeposits() == 0
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 5
	assert matcher.alphaSpentCounter() == 4
	assert matcher.betaSpentCounter() == 4
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(14)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(21 << 48) + 21, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(15)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(24 << 48) + 23, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(16)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1,(23 << 48) + 22, nft_guy, coin_guy, nft_guy, coin_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(17)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2,(22 << 48) + 24, nft_guy, coin_guy, nft_guy, coin_guy)

# tests to add:
# - test_dogs_then_primary_first_coins
# - test_more_primary_than_dogs
# - test_less primary_than_dogs
# - test_more_primary_than_dogs__dog_first
# - test_less primary_than_dogs__dog_first