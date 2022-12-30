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
	pre = ape.balanceOf(ape_staking)

	matcher.depositNfts([10], [], [], {'from':nft_guy})
	matcher.depositApeToken([1,0,0], {'from':coin_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == BAYC_CAP
	assert bayc.ownerOf(10) == smooth
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 10, nft_guy, coin_guy, NULL, NULL)
	assert matcher.alphaSpentCounter() == 1
	with reverts('consumed'):
		matcher.withdrawApeToken([[(0, 1)] ,[], []], {'from':coin_guy})

def test_single_mayc_match(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)

	matcher.depositNfts([], [5], [], {'from':nft_guy})
	matcher.depositApeToken([0,1,0], {'from':coin_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == MAYC_CAP
	assert mayc.ownerOf(5) == smooth
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 5, nft_guy, coin_guy, NULL, NULL)
	assert matcher.doglessMatchCounter() == 2
	assert matcher.betaSpentCounter() == 1
	with reverts('consumed'):
		matcher.withdrawApeToken([[] ,[(0, 1)], []], {'from':coin_guy})


def test_single_bakc_bind(matcher, ape, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)

	matcher.depositNfts([], [], [5], {'from':nft_guy})
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP
	assert bakc.ownerOf(5) == smooth
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(1)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(5 << 48) + 5, nft_guy, coin_guy, nft_guy, coin_guy)

	matcher.depositNfts([], [], [6], {'from':nft_guy})
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	assert matcher.gammaDepositCounter() == 2
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP + BAKC_CAP
	assert bakc.ownerOf(6) == smooth
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(0)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(6 << 48) + 10, nft_guy, coin_guy, nft_guy, coin_guy)
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 2
	with reverts('consumed'):
		matcher.withdrawApeToken([[] ,[], [(0, 1)]], {'from':coin_guy})

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
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(2)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 7, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(3)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 9, nft_guy, coin_guy, NULL, NULL)

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 8, nft_guy, coin_guy, NULL, NULL)

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
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(5)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 9, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(6)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 8, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(7)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 7, nft_guy, coin_guy, NULL, NULL)

	assert matcher.betaSpentCounter() == 2

def test_many_bakc_bind(matcher, ape, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	pre = ape.balanceOf(ape_staking)
	assert matcher.doglessMatchCounter() == 6
	matcher.depositNfts([], [], [1,2,3,4,7,8], {'from':nft_guy})
	matcher.depositApeToken([0,0,6], {'from':coin_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP * 6
	assert bakc.ownerOf(1) == smooth
	assert bakc.ownerOf(2) == smooth
	assert bakc.ownerOf(3) == smooth
	assert bakc.ownerOf(4) == smooth
	assert bakc.ownerOf(7) == smooth
	assert bakc.ownerOf(8) == smooth
	assert matcher.gammaDepositCounter() == 3
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(7)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(1 << 48) + 7, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(6)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(8 << 48) + 8, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(5)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(7 << 48) + 9, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(4 << 48) + 8, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(3)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(3 << 48) + 9, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(2)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(2 << 48) + 7, nft_guy, coin_guy, nft_guy, coin_guy)
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
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(8)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 11, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(9)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 13, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(10)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 12, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(11)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 14, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(12)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 16, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(13)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 15, nft_guy, coin_guy, NULL, NULL)
	assert matcher.alphaSpentCounter() == 3
	assert matcher.betaSpentCounter() == 3
	assert matcher.doglessMatchCounter() == 6

	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)
	matcher.depositNfts([], [], [11,12,13,14,17,18], {'from':nft_guy})
	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	assert ape.balanceOf(smooth) == 0
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP * 6
	assert bakc.ownerOf(11) == smooth
	assert bakc.ownerOf(12) == smooth
	assert bakc.ownerOf(13) == smooth
	assert bakc.ownerOf(14) == smooth
	assert bakc.ownerOf(17) == smooth
	assert bakc.ownerOf(18) == smooth
	assert matcher.gammaDepositCounter() == 6
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(13)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(11 << 48) + 15, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(12)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(18 << 48) + 16, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(11)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(17 << 48) + 14, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(10)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(14 << 48) + 12, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(9)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(13 << 48) + 13, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(8)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(12 << 48) + 11, nft_guy, coin_guy, nft_guy, coin_guy)
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 6

def test_dogs_then_primary(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)
	matcher.depositNfts([], [], [21,22,23,24], {'from':nft_guy})
	matcher.depositApeToken([0,0,4], {'from':coin_guy})
	assert bakc.balanceOf(matcher) == 4
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP * 4
	assert matcher.gammaDepositCounter() == 7
	assert matcher.gammaCurrentTotalDeposits() == 4
	assert matcher.doglessMatchCounter() == 0

	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	matcher.depositNfts([21,22,23], [24], [], {'from':nft_guy})
	matcher.depositApeToken([2,0,0], {'from':coin_guy})
	matcher.depositApeToken([1,1,0], {'from':coin_guy})
	assert bakc.balanceOf(matcher) == 0
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.betaCurrentTotalDeposits() == 0
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 7
	assert matcher.alphaSpentCounter() == 5
	assert matcher.betaSpentCounter() == 4
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(14)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(21 << 48) + 21, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(15)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(24 << 48) + 23, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(16)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(23 << 48) + 22, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(17)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(22 << 48) + 24, nft_guy, coin_guy, nft_guy, coin_guy)

def test_dogs_then_primary_first_coins(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	matcher.depositApeToken([0,0,1], {'from':coin_guy})
	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	matcher.depositNfts([], [], [31,32,33,34], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 4
	assert ape.balanceOf(ape_staking) - pre == BAKC_CAP * 4
	assert matcher.gammaDepositCounter() == 10
	assert matcher.gammaCurrentTotalDeposits() == 4
	assert matcher.doglessMatchCounter() == 0

	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	matcher.depositApeToken([1,3,0], {'from':coin_guy})
	matcher.depositNfts([34], [31,32,33], [], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 0
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.betaCurrentTotalDeposits() == 0
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaSpentCounter() == 10
	assert matcher.alphaSpentCounter() == 6
	assert matcher.betaSpentCounter() == 5
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(18)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1,(31 << 48) + 34, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(19)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(34 << 48) + 31, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(20)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(33 << 48) + 33, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(21)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0,(32 << 48) + 32, nft_guy, coin_guy, nft_guy, coin_guy)


def test_more_primary_deposits(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	matcher.depositNfts([40, 41, 42, 43], [44, 45, 46, 47], [], {'from':nft_guy})
	matcher.depositApeToken([3,3,0], {'from':coin_guy})
	assert bayc.balanceOf(matcher) == 1
	assert mayc.balanceOf(matcher) == 1
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.betaCurrentTotalDeposits() == 0
	assert matcher.alphaDepositCounter() == 7
	assert matcher.betaDepositCounter() == 6
	assert matcher.alphaSpentCounter() == 7
	assert matcher.betaSpentCounter() == 6

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(22)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 40, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(23)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 43, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(24)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, 42, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(25)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 44, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(26)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 47, nft_guy, coin_guy, NULL, NULL)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(27)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 46, nft_guy, coin_guy, NULL, NULL)
	assert matcher.doglessMatchCounter() == 6

def test_fill_match_batch(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)
	pre_smooth = ape.balanceOf(smooth)
	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	matcher.depositNfts([], [], [41,42], {'from':nft_guy})
	assert matcher.gammaDepositCounter() == 11
	assert matcher.gammaSpentCounter() == 11
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.doglessMatchCounter() == 4

	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	matcher.depositNfts([], [], [43,44], {'from':nft_guy})
	assert matcher.gammaDepositCounter() == 12
	assert matcher.gammaSpentCounter() == 12
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.doglessMatchCounter() == 2

	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	matcher.depositNfts([], [], [45,46], {'from':nft_guy})
	assert matcher.gammaDepositCounter() == 13
	assert matcher.gammaSpentCounter() == 13
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.doglessMatchCounter() == 0

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(22)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (46 << 48) + 40, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(23)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (45 << 48) + 43, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(24)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (44 << 48) + 42, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(25)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (43 << 48) + 44, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(26)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (42 << 48) + 47, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(27)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (41 << 48) + 46, nft_guy, coin_guy, nft_guy, coin_guy)

def test_less_primary_deposits(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	matcher.depositNfts([48], [49], [], {'from':nft_guy})
	ape.mint(coin_guy, '110000 ether')
	matcher.depositApeToken([4,4,0], {'from':coin_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.alphaDepositCounter() == 8
	assert matcher.betaDepositCounter() == 7
	assert matcher.alphaSpentCounter() == 7
	assert matcher.betaSpentCounter() == 6
	assert matcher.depositPosition(MAYC_CAP, 6) == (2, coin_guy)
	assert matcher.depositPosition(BAYC_CAP, 7) == (2, coin_guy)
	assert matcher.doglessMatchCounter() == 4 

def test_more_primary_than_dogs(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	matcher.depositNfts([50,51], [52,53], [], {'from':nft_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.doglessMatchCounter() == 8
	assert matcher.alphaSpentCounter() == 8
	assert matcher.betaSpentCounter() == 7
	matcher.depositApeToken([0,0,6], {'from':coin_guy})
	matcher.depositNfts([], [], [55, 56, 57, 58, 59, 60], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 2
	assert matcher.gammaDepositCounter() == 14
	assert matcher.gammaSpentCounter() == 14
# 41  48        50  51
#        45  49       52  53
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(30)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (56 << 48) + 45, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(31)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (57 << 48) + 49, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(32)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (58 << 48) + 50, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(33)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (59 << 48) + 51, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(34)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (60 << 48) + 52, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(35)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (55 << 48) + 53, nft_guy, coin_guy, nft_guy, coin_guy)

	matcher.depositApeToken([0,0,2], {'from':coin_guy})
	matcher.depositNfts([], [], [53, 54], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaDepositCounter() == 15
	assert matcher.gammaSpentCounter() == 15
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert bakc.balanceOf(matcher) == 0

def test_less_primary_than_dogs(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	matcher.depositNfts([60,61], [62,63], [], {'from':nft_guy})
	matcher.depositApeToken([2,2,0], {'from':coin_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.doglessMatchCounter() == 4
	assert matcher.alphaSpentCounter() == 9
	assert matcher.betaSpentCounter() == 8
	matcher.depositApeToken([0,0,6], {'from':coin_guy})
	matcher.depositNfts([], [], [65, 66, 67, 68, 69, 70], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 2
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaDepositCounter() == 16
	assert matcher.gammaSpentCounter() == 15

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(36)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (68 << 48) + 60, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(37)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (69 << 48) + 61, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(38)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (70 << 48) + 62, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(39)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (65 << 48) + 63, nft_guy, coin_guy, nft_guy, coin_guy)

	matcher.depositNfts([64], [65], [], {'from':nft_guy})
	matcher.depositApeToken([1,1,0], {'from':coin_guy})
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaDepositCounter() == 16
	assert matcher.gammaSpentCounter() == 16
	assert matcher.alphaSpentCounter() == 10
	assert matcher.betaSpentCounter() == 9
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(40)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (67 << 48) + 64, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(41)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (66 << 48) + 65, nft_guy, coin_guy, nft_guy, coin_guy)

def test_all_in_one(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	ape.mint(coin_guy, '110000 ether')

	pre_a = bayc.balanceOf(smooth)
	pre_b = mayc.balanceOf(smooth)
	pre_d = bakc.balanceOf(smooth)
	matcher.depositNfts([71,72], [73,74], [71,72,73,74], {'from':nft_guy})
	matcher.depositApeToken([2,2,4], {'from':coin_guy})
	assert bayc.balanceOf(smooth) - pre_a == 2
	assert mayc.balanceOf(smooth) - pre_b == 2
	assert bakc.balanceOf(smooth) - pre_d == 4
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaDepositCounter() == 17
	assert matcher.gammaSpentCounter() == 17
	assert matcher.alphaSpentCounter() == 11
	assert matcher.betaSpentCounter() == 10

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(42)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (71 << 48) + 71, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(43)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (74 << 48) + 72, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(44)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (73 << 48) + 73, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(45)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (72 << 48) + 74, nft_guy, coin_guy, nft_guy, coin_guy)


def test_all_in_one_inverse(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	ape.mint(coin_guy, '110000 ether')

	pre_a = bayc.balanceOf(smooth)
	pre_b = mayc.balanceOf(smooth)
	pre_d = bakc.balanceOf(smooth)
	matcher.depositApeToken([2,2,4], {'from':coin_guy})
	matcher.depositNfts([82,83], [80,81], [84,85,86,87], {'from':nft_guy})
	assert bayc.balanceOf(smooth) - pre_a == 2
	assert mayc.balanceOf(smooth) - pre_b == 2
	assert bakc.balanceOf(smooth) - pre_d == 4
	assert matcher.doglessMatchCounter() == 0
	assert matcher.gammaDepositCounter() == 18
	assert matcher.gammaSpentCounter() == 18
	assert matcher.alphaSpentCounter() == 12
	assert matcher.betaSpentCounter() == 11

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(46)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (84 << 48) + 82, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(47)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (87 << 48) + 83, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(48)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (86 << 48) + 80, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(49)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (85 << 48) + 81, nft_guy, coin_guy, nft_guy, coin_guy)

def test_less_primary_than_dogs__dog_first(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	ape.mint(coin_guy, '110000 ether')

	matcher.depositApeToken([2,2,5], {'from':coin_guy})
	matcher.depositNfts([], [], [91,92,93,94,95], {'from':nft_guy})
	matcher.depositNfts([91,92], [93,94], [], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 1
	assert matcher.alphaSpentCounter() == 13
	assert matcher.betaSpentCounter() == 12
	assert matcher.gammaDepositCounter() == 19
	assert matcher.gammaSpentCounter() == 18

	(dogless, ids, pO, pT, dO, dT) = matcher.matches(50)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (91 << 48) + 91, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(51)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (95 << 48) + 92, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(52)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (94 << 48) + 93, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(53)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (93 << 48) + 94, nft_guy, coin_guy, nft_guy, coin_guy)

def test_more_primary_than_dogs__dog_first(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	matcher.depositApeToken([2,3,3], {'from':coin_guy})
	matcher.depositNfts([], [], [101,102,103], {'from':nft_guy})
	matcher.depositNfts([109, 108], [107, 106, 105], [], {'from':nft_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert bakc.balanceOf(matcher) == 0

	assert matcher.alphaSpentCounter() == 14
	assert matcher.betaSpentCounter() == 13
	assert matcher.gammaDepositCounter() == 20
	assert matcher.gammaSpentCounter() == 20


	(dogless, ids, pO, pT, dO, dT) = matcher.matches(54)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (92 << 48) + 109, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(55)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (1, (103 << 48) + 108, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(56)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (102 << 48) + 107, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(57)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, (101 << 48) + 105, nft_guy, coin_guy, nft_guy, coin_guy)
	(dogless, ids, pO, pT, dO, dT) = matcher.matches(58)
	assert (dogless & 1, ids, pO, pT, dO, dT) == (0, 106, nft_guy, coin_guy, NULL, NULL)