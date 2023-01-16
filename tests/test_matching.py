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

def test_single_bayc_match(matcher, ape, bayc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})
	ape.mint(coin_guy, '320000 ether')
	compounder.deposit('192872 ether', {'from':coin_guy})
	pre = compounder.debt()
	matcher.depositNfts([10], [], [], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert compounder.debt() - pre == BAYC_CAP
	assert bayc.ownerOf(10) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, 10, nft_guy, NULL, False)

def test_single_mayc_match(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.mint(nft_guy, 10)
	pre = compounder.debt()

	matcher.depositNfts([], [5], [], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert compounder.debt() - pre == MAYC_CAP
	assert mayc.ownerOf(5) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, 5, nft_guy, NULL, False)
	assert matcher.doglessMatchCounter() == 2

def test_single_bakc_bind(matcher, ape, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.mint(nft_guy, 10)
	pre = compounder.debt()

	matcher.depositNfts([], [], [5], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert compounder.debt() - pre == BAKC_CAP
	assert bakc.ownerOf(5) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0,(5 << 48) + 5, nft_guy, nft_guy, False)

	matcher.depositNfts([], [], [6], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert compounder.debt() - pre == BAKC_CAP + BAKC_CAP
	assert bakc.ownerOf(6) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1,(6 << 48) + 10, nft_guy, nft_guy, False)
	assert matcher.doglessMatchCounter() == 0

def test_many_bayc_match(matcher, ape, bayc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	pre = compounder.debt()
	pre_nft =  bayc.balanceOf(smooth)
	matcher.depositNfts([7,8,9], [], [], {'from':nft_guy})
	assert bayc.balanceOf(smooth) - pre_nft == 3
	assert compounder.debt() - pre == BAYC_CAP * 3
	assert bayc.ownerOf(9) == smooth
	assert bayc.ownerOf(8) == smooth
	assert bayc.ownerOf(7) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(2)
	assert (dogless & 1, ids, pO, dO, self) == (1, 7, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(3)
	assert (dogless & 1, ids, pO, dO, self) == (1, 9, nft_guy, NULL, False)

	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (1, 8, nft_guy, NULL, False)


def test_many_mayc_match(matcher, ape, mayc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	pre = compounder.debt()
	pre_nft =  mayc.balanceOf(smooth)
	matcher.depositNfts([], [9,7,8], [], {'from':nft_guy})
	assert mayc.balanceOf(smooth) - pre_nft == 3
	assert compounder.debt() - pre == MAYC_CAP * 3
	assert mayc.ownerOf(9) == smooth
	assert mayc.ownerOf(8) == smooth
	assert mayc.ownerOf(7) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (0, 9, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(6)
	assert (dogless & 1, ids, pO, dO, self) == (0, 8, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(7)
	assert (dogless & 1, ids, pO, dO, self) == (0, 7, nft_guy, NULL, False)


def test_many_bakc_bind(matcher, ape, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	pre = compounder.debt()
	assert matcher.doglessMatchCounter() == 6
	matcher.depositNfts([], [], [1,2,3,4,7,8], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert compounder.debt() - pre == BAKC_CAP * 6
	assert bakc.ownerOf(1) == smooth
	assert bakc.ownerOf(2) == smooth
	assert bakc.ownerOf(3) == smooth
	assert bakc.ownerOf(4) == smooth
	assert bakc.ownerOf(7) == smooth
	assert bakc.ownerOf(8) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(7)
	assert (dogless & 1, ids, pO, dO, self) == (0,(1 << 48) + 7, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(6)
	assert (dogless & 1, ids, pO, dO, self) == (0,(8 << 48) + 8, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (0,(7 << 48) + 9, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (1,(4 << 48) + 8, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(3)
	assert (dogless & 1, ids, pO, dO, self) == (1,(3 << 48) + 9, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(2)
	assert (dogless & 1, ids, pO, dO, self) == (1,(2 << 48) + 7, nft_guy, nft_guy, False)
	assert matcher.doglessMatchCounter() == 0

def test_many_multi_match_then_dogs(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	pre = compounder.debt()
	pre_nft_b =  mayc.balanceOf(smooth)
	pre_nft_a =  bayc.balanceOf(smooth)
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	matcher.depositNfts([11,12,13], [14,15,16], [], {'from':nft_guy})
	assert mayc.balanceOf(smooth) - pre_nft_b == 3
	assert bayc.balanceOf(smooth) - pre_nft_a == 3
	assert compounder.debt() - pre == MAYC_CAP * 3 + BAYC_CAP * 3
	assert mayc.ownerOf(14) == smooth
	assert mayc.ownerOf(15) == smooth
	assert mayc.ownerOf(16) == smooth
	assert bayc.ownerOf(11) == smooth
	assert bayc.ownerOf(12) == smooth
	assert bayc.ownerOf(13) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(8)
	assert (dogless & 1, ids, pO, dO, self) == (1, 11, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(9)
	assert (dogless & 1, ids, pO, dO, self) == (1, 13, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(10)
	assert (dogless & 1, ids, pO, dO, self) == (1, 12, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(11)
	assert (dogless & 1, ids, pO, dO, self) == (0, 14, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(12)
	assert (dogless & 1, ids, pO, dO, self) == (0, 16, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(13)
	assert (dogless & 1, ids, pO, dO, self) == (0, 15, nft_guy, NULL, False)
	assert matcher.doglessMatchCounter() == 6

	bakc.mint(nft_guy, 10)
	pre = compounder.debt()
	matcher.depositNfts([], [], [11,12,13,14,17,18], {'from':nft_guy})
	assert ape.balanceOf(smooth) == 0
	assert compounder.debt() - pre == BAKC_CAP * 6
	assert bakc.ownerOf(11) == smooth
	assert bakc.ownerOf(12) == smooth
	assert bakc.ownerOf(13) == smooth
	assert bakc.ownerOf(14) == smooth
	assert bakc.ownerOf(17) == smooth
	assert bakc.ownerOf(18) == smooth
	(self, dogless, ids, pO, dO) = matcher.matches(13)
	assert (dogless & 1, ids, pO, dO, self) == (0,(11 << 48) + 15, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(12)
	assert (dogless & 1, ids, pO, dO, self) == (0,(18 << 48) + 16, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(11)
	assert (dogless & 1, ids, pO, dO, self) == (0,(17 << 48) + 14, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(10)
	assert (dogless & 1, ids, pO, dO, self) == (1,(14 << 48) + 12, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(9)
	assert (dogless & 1, ids, pO, dO, self) == (1,(13 << 48) + 13, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(8)
	assert (dogless & 1, ids, pO, dO, self) == (1,(12 << 48) + 11, nft_guy, nft_guy, False)
	assert matcher.doglessMatchCounter() == 0

def test_dogs_then_primary(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	bakc.mint(nft_guy, 10)
	pre = compounder.debt()
	matcher.depositNfts([], [], [21,22,23,24], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 4
	assert compounder.debt() - pre == 0
	assert matcher.doglessMatchCounter() == 0

	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	matcher.depositNfts([21,22,23], [24], [], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 0
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.doglessMatchCounter() == 0
	(self, dogless, ids, pO, dO) = matcher.matches(14)
	assert (dogless & 1, ids, pO, dO, self) == (1,(21 << 48) + 21, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(15)
	assert (dogless & 1, ids, pO, dO, self) == (1,(24 << 48) + 23, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(16)
	assert (dogless & 1, ids, pO, dO, self) == (1,(23 << 48) + 22, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(17)
	assert (dogless & 1, ids, pO, dO, self) == (0,(22 << 48) + 24, nft_guy, nft_guy, False)

def test_dogs_then_primary_2(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	bakc.mint(nft_guy, 10)
	pre = compounder.debt()
	matcher.depositNfts([], [], [31,32,33,34], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 4
	assert compounder.debt() - pre == 0
	assert matcher.doglessMatchCounter() == 0

	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	matcher.depositNfts([34], [31,32,33], [], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 0
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.doglessMatchCounter() == 0
	(self, dogless, ids, pO, dO) = matcher.matches(18)
	assert (dogless & 1, ids, pO, dO, self) == (1,(31 << 48) + 34, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(19)
	assert (dogless & 1, ids, pO, dO, self) == (0,(34 << 48) + 31, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(20)
	assert (dogless & 1, ids, pO, dO, self) == (0,(33 << 48) + 33, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(21)
	assert (dogless & 1, ids, pO, dO, self) == (0,(32 << 48) + 32, nft_guy, nft_guy, False)

def test_more_primary_deposits(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	compounder.withdraw('40544 ethers' ,{'from':coin_guy})
	compounder.deposit('36409 ether', {'from':coin_guy})
	matcher.depositNfts([40, 41, 42, 43], [44, 45, 46, 47], [], {'from':nft_guy})
	assert bayc.balanceOf(matcher) == 1
	assert mayc.balanceOf(matcher) == 1

	(self, dogless, ids, pO, dO) = matcher.matches(22)
	assert (dogless & 1, ids, pO, dO, self) == (1, 40, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(23)
	assert (dogless & 1, ids, pO, dO, self) == (1, 43, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(24)
	assert (dogless & 1, ids, pO, dO, self) == (1, 42, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(25)
	assert (dogless & 1, ids, pO, dO, self) == (0, 44, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(26)
	assert (dogless & 1, ids, pO, dO, self) == (0, 47, nft_guy, NULL, False)
	(self, dogless, ids, pO, dO) = matcher.matches(27)
	assert (dogless & 1, ids, pO, dO, self) == (0, 46, nft_guy, NULL, False)
	assert matcher.doglessMatchCounter() == 6

def test_fill_match_batch(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	ape.mint(coin_guy, '220000 ether')
	compounder.deposit('1712 ether', {'from':coin_guy})
	bakc.mint(nft_guy, 10)
	pre = ape.balanceOf(ape_staking)
	pre_smooth = ape.balanceOf(smooth)
	matcher.depositNfts([], [], [41,42], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 4
	compounder.deposit('1712 ether', {'from':coin_guy})
	matcher.depositNfts([], [], [43,44], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 2
	compounder.deposit('1712 ether', {'from':coin_guy})
	matcher.depositNfts([], [], [45,46], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0

	(self, dogless, ids, pO, dO) = matcher.matches(22)
	assert (dogless & 1, ids, pO, dO, self) == (1, (46 << 48) + 40, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(23)
	assert (dogless & 1, ids, pO, dO, self) == (1, (45 << 48) + 43, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(24)
	assert (dogless & 1, ids, pO, dO, self) == (1, (44 << 48) + 42, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(25)
	assert (dogless & 1, ids, pO, dO, self) == (0, (43 << 48) + 44, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(26)
	assert (dogless & 1, ids, pO, dO, self) == (0, (42 << 48) + 47, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(27)
	assert (dogless & 1, ids, pO, dO, self) == (0, (41 << 48) + 46, nft_guy, nft_guy, False)

def test_less_primary_deposits(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	compounder.deposit('100000 ether', {'from':coin_guy})
	matcher.depositNfts([48], [49], [], {'from':nft_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.doglessMatchCounter() == 4 

def test_more_primary_than_dogs(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	matcher.depositNfts([50,51], [52,53], [], {'from':nft_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.doglessMatchCounter() == 8
	matcher.depositNfts([], [], [55, 56, 57, 58, 59, 60], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 2
# 41  48        50  51
#        45  49       52  53
	(self, dogless, ids, pO, dO) = matcher.matches(30)
	assert (dogless & 1, ids, pO, dO, self) == (0, (56 << 48) + 45, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(31)
	assert (dogless & 1, ids, pO, dO, self) == (0, (57 << 48) + 49, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(32)
	assert (dogless & 1, ids, pO, dO, self) == (1, (58 << 48) + 50, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(33)
	assert (dogless & 1, ids, pO, dO, self) == (1, (59 << 48) + 51, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(34)
	assert (dogless & 1, ids, pO, dO, self) == (0, (60 << 48) + 52, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(35)
	assert (dogless & 1, ids, pO, dO, self) == (0, (55 << 48) + 53, nft_guy, nft_guy, False)

	matcher.depositNfts([], [], [53, 54], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert bakc.balanceOf(matcher) == 0

def test_less_primary_than_dogs(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	matcher.depositNfts([60,61], [62,63], [], {'from':nft_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert matcher.doglessMatchCounter() == 4
	matcher.depositNfts([], [], [65, 66, 67, 68, 69, 70], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 2
	assert matcher.doglessMatchCounter() == 0

	(self, dogless, ids, pO, dO) = matcher.matches(36)
	assert (dogless & 1, ids, pO, dO, self) == (1, (68 << 48) + 60, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(37)
	assert (dogless & 1, ids, pO, dO, self) == (1, (69 << 48) + 61, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(38)
	assert (dogless & 1, ids, pO, dO, self) == (0, (70 << 48) + 62, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(39)
	assert (dogless & 1, ids, pO, dO, self) == (0, (65 << 48) + 63, nft_guy, nft_guy, False)

	matcher.depositNfts([64], [65], [], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0
	(self, dogless, ids, pO, dO) = matcher.matches(40)
	assert (dogless & 1, ids, pO, dO, self) == (1, (67 << 48) + 64, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(41)
	assert (dogless & 1, ids, pO, dO, self) == (0, (66 << 48) + 65, nft_guy, nft_guy, False)

def test_all_in_one(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	compounder.deposit('100000 ether', {'from':coin_guy})
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)

	pre_a = bayc.balanceOf(smooth)
	pre_b = mayc.balanceOf(smooth)
	pre_d = bakc.balanceOf(smooth)
	matcher.depositNfts([71,72], [73,74], [71,72,73,74], {'from':nft_guy})
	assert bayc.balanceOf(smooth) - pre_a == 2
	assert mayc.balanceOf(smooth) - pre_b == 2
	assert bakc.balanceOf(smooth) - pre_d == 4
	assert matcher.doglessMatchCounter() == 0

	(self, dogless, ids, pO, dO) = matcher.matches(42)
	assert (dogless & 1, ids, pO, dO, self) == (1, (71 << 48) + 71, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(43)
	assert (dogless & 1, ids, pO, dO, self) == (1, (74 << 48) + 72, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(44)
	assert (dogless & 1, ids, pO, dO, self) == (0, (73 << 48) + 73, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(45)
	assert (dogless & 1, ids, pO, dO, self) == (0, (72 << 48) + 74, nft_guy, nft_guy, False)


def test_all_in_one_inverse(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	ape.mint(coin_guy, '110000 ether')

	pre_a = bayc.balanceOf(smooth)
	pre_b = mayc.balanceOf(smooth)
	pre_d = bakc.balanceOf(smooth)
	matcher.depositNfts([82,83], [80,81], [84,85,86,87], {'from':nft_guy})
	assert bayc.balanceOf(smooth) - pre_a == 2
	assert mayc.balanceOf(smooth) - pre_b == 2
	assert bakc.balanceOf(smooth) - pre_d == 4
	assert matcher.doglessMatchCounter() == 0

	(self, dogless, ids, pO, dO) = matcher.matches(46)
	assert (dogless & 1, ids, pO, dO, self) == (1, (84 << 48) + 82, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(47)
	assert (dogless & 1, ids, pO, dO, self) == (1, (87 << 48) + 83, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(48)
	assert (dogless & 1, ids, pO, dO, self) == (0, (86 << 48) + 80, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(49)
	assert (dogless & 1, ids, pO, dO, self) == (0, (85 << 48) + 81, nft_guy, nft_guy, False)

def test_less_primary_than_dogs__dog_first(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	ape.mint(coin_guy, '110000 ether')

	matcher.depositNfts([], [], [91,92,93,94,95], {'from':nft_guy})
	matcher.depositNfts([91,92], [93,94], [], {'from':nft_guy})
	assert bakc.balanceOf(matcher) == 1

	(self, dogless, ids, pO, dO) = matcher.matches(50)
	assert (dogless & 1, ids, pO, dO, self) == (1, (91 << 48) + 91, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(51)
	assert (dogless & 1, ids, pO, dO, self) == (1, (95 << 48) + 92, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(52)
	assert (dogless & 1, ids, pO, dO, self) == (0, (94 << 48) + 93, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(53)
	assert (dogless & 1, ids, pO, dO, self) == (0, (93 << 48) + 94, nft_guy, nft_guy, False)

def test_more_primary_than_dogs__dog_first(matcher, ape, bayc, mayc, bakc, nft_guy, coin_guy, ape_staking, smooth, chain, compounder):
	mayc.mint(nft_guy, 10)
	bayc.mint(nft_guy, 10)
	bakc.mint(nft_guy, 10)
	compounder.deposit('100000 ether', {'from':coin_guy})
	matcher.depositNfts([], [], [101,102,103], {'from':nft_guy})
	matcher.depositNfts([109, 108], [107, 106, 105], [], {'from':nft_guy})
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(matcher) == 0
	assert bakc.balanceOf(matcher) == 0


	(self, dogless, ids, pO, dO) = matcher.matches(54)
	assert (dogless & 1, ids, pO, dO, self) == (1, (92 << 48) + 109, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(55)
	assert (dogless & 1, ids, pO, dO, self) == (1, (103 << 48) + 108, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(56)
	assert (dogless & 1, ids, pO, dO, self) == (0, (102 << 48) + 107, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(57)
	assert (dogless & 1, ids, pO, dO, self) == (0, (101 << 48) + 105, nft_guy, nft_guy, False)
	(self, dogless, ids, pO, dO) = matcher.matches(58)
	assert (dogless & 1, ids, pO, dO, self) == (0, 106, nft_guy, NULL, False)