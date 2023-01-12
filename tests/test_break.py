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
BAYC_Q1 = 1678726800 - 1670864400
MAYC_Q1 = 1678726800 - 1670864400
BAKC_Q1 = 1678726800 - 1670864400
BAYC_DAILY_RATE = 16486750000000000000000000 // (MAYC_Q1 // 86400)
MAYC_DAILY_RATE = 6671000000000000000000000 // (MAYC_Q1 // 86400)
BAKC_DAILY_RATE = 1342250000000000000000000 // (BAKC_Q1 // 86400)

def test_break_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder, admin):
	ape.mint(coin_guy, '1000000 ether')
	bayc.mint(nft_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})
	compounder.deposit('100000 ether', {'from':coin_guy})
	to_sleep = 0 if chain.time() > 1670864400 else 1670864400 - chain.time()
	chain.sleep(to_sleep)
	chain.mine()
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	assert compounder.debt() == BAYC_CAP
	assert matcher.doglessMatchCounter() == 1
	with reverts('!mtch'):
		matcher.batchBreakMatch([0], [False], {'from':other_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(1, smooth, 1)
	matcher.batchBreakMatch([0], [False], {'from':nft_guy})
	assert compounder.debt() == 0
	assert math.isclose(matcher.payments(nft_guy), rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder), rewards // 2 * 96 // 100)
	assert bayc.ownerOf(1) == nft_guy
	assert matcher.doglessMatchCounter() == 0
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	assert bayc.ownerOf(1) == smooth
	assert compounder.debt() == BAYC_CAP
	assert matcher.doglessMatchCounter() == 1
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(1, smooth, 1)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	compounder.batchBreakMatch([1], [False], {'from':admin})
	assert compounder.debt() == 0
	assert matcher.doglessMatchCounter() == 0
	assert math.isclose(matcher.payments(nft_guy) - pre_n, rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, rewards // 2 * 96 // 100)
	assert bayc.ownerOf(1) == matcher
	matcher.withdrawNfts([1],[],[], {'from':nft_guy})
	with reverts('!ownr'):
		matcher.depositNfts([1], [], [], {'from':dog_guy})
	assert compounder.liquid() > '100000 ether'

def test_break_mayc(matcher, ape, mayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder, admin):
	mayc.mint(nft_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	matcher.depositNfts([], [2], [], {'from':nft_guy})
	assert compounder.debt() == MAYC_CAP
	assert matcher.doglessMatchCounter() == 1
	with reverts('!mtch'):
		matcher.batchBreakMatch([2], [False], {'from':other_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(2, smooth, 2)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	matcher.batchBreakMatch([2], [False], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0
	assert compounder.debt() == 0
	assert math.isclose(matcher.payments(nft_guy) - pre_n, rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, rewards // 2 * 96 // 100)
	assert mayc.ownerOf(2) == nft_guy
	matcher.depositNfts([], [2], [], {'from':nft_guy})
	assert compounder.debt() == MAYC_CAP
	assert matcher.doglessMatchCounter() == 1
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(2, smooth, 2)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	compounder.batchBreakMatch([3], [False], {'from':admin})
	assert compounder.debt() == 0
	assert matcher.doglessMatchCounter() == 0
	assert math.isclose(matcher.payments(nft_guy) - pre_n, rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, rewards // 2 * 96 // 100)
	assert mayc.ownerOf(2) == matcher
	with reverts('!ownr'):
		matcher.depositNfts([], [2], [], {'from':dog_guy})
	assert compounder.liquid() > '100000 ether'



def test_break_dog_calling_standard_break_mayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder, admin):
	bakc.mint(dog_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':dog_guy})
	compounder.makeMatches({'from':admin})
	assert compounder.debt() == MAYC_CAP
	assert matcher.doglessMatchCounter() == 1
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (0, 2, nft_guy, NULL, False)
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	assert compounder.debt() == MAYC_CAP + BAKC_CAP
	assert matcher.doglessMatchCounter() == 0
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (0, (3 << 48) + 2, nft_guy, dog_guy, False)
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(2, smooth, 2)
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	pre_d = matcher.payments(dog_guy)
	matcher.batchBreakMatch([4], [False], {'from':dog_guy})
	assert compounder.debt() == MAYC_CAP
	assert matcher.doglessMatchCounter() == 1
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, (rewards_d * 1 // 10) * 96 // 100 + rewards_d  * 4// 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (0, 2, nft_guy, NULL, False)
	assert bakc.ownerOf(3) == dog_guy
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	assert compounder.debt() == MAYC_CAP + BAKC_CAP
	assert matcher.doglessMatchCounter() == 0
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (0, (3 << 48) + 2, nft_guy, dog_guy, False)
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	pre_d = matcher.payments(dog_guy)
	compounder.batchBreakMatch([4], [False], {'from':admin})
	assert matcher.doglessMatchCounter() == 1
	assert compounder.debt() == MAYC_CAP
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, (rewards_d * 1 // 10) * 96 // 100 + rewards_d  * 4// 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert bakc.ownerOf(3) == matcher

	matcher.withdrawNfts([],[],[3], {'from':dog_guy})
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (0, (3 << 48) + 2, nft_guy, dog_guy, False)
	compounder.batchBreakMatch([4], [True], {'from':admin})
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (0, 0, NULL, NULL, False)
	assert compounder.debt() == 0
	assert matcher.doglessMatchCounter() == 0
	matcher.withdrawNfts([],[2],[], {'from':nft_guy})

def test_break_dog_calling_standard_break_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder, admin):
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	assert matcher.doglessMatchCounter() == 0
	assert compounder.debt() == BAYC_CAP + BAKC_CAP
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (1, (3 << 48) + 1, nft_guy, dog_guy, False)
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(1, smooth, 1)
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	pre_d = matcher.payments(dog_guy)

	matcher.batchBreakMatch([5], [False], {'from':dog_guy})
	assert compounder.debt() == BAYC_CAP
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, (rewards_d * 1 // 10) * 96 // 100 + rewards_d  * 4// 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (1, 1, nft_guy, NULL, False)
	assert bakc.ownerOf(3) == dog_guy
	assert matcher.doglessMatchCounter() == 1
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (1, (3 << 48) + 1, nft_guy, dog_guy, False)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	pre_d = matcher.payments(dog_guy)
	compounder.batchBreakMatch([5], [False], {'from':admin})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, (rewards_d * 1 // 10) * 96 // 100 +  rewards_d  * 4// 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert bakc.ownerOf(3) == matcher
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (1, 1, nft_guy, NULL, False)

	matcher.withdrawNfts([],[],[3], {'from':dog_guy})
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (1, (3 << 48) + 1, nft_guy, dog_guy, False)
	compounder.batchBreakMatch([5], [True], {'from':admin})
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (0, 0, NULL, NULL, False)
	assert compounder.debt() == 0
	assert matcher.doglessMatchCounter() == 0
	matcher.withdrawNfts([1],[],[], {'from':nft_guy})

def test_break_primary_filled_match_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder):
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	assert compounder.debt() == BAYC_CAP + BAKC_CAP
	(self, dogless, ids, pO, dO) = matcher.matches(6)
	assert (dogless & 1, ids, pO, dO, self) == (1, (3 << 48) + 1, nft_guy, dog_guy, False)
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards_m = ape_staking.pendingRewards(1, smooth, 1)
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(compounder)
	pre_d = matcher.payments(dog_guy)
	assert bakc.ownerOf(3) == smooth
	matcher.batchBreakMatch([6], [False], {'from':nft_guy})
	assert compounder.debt() == 0
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10 + rewards_m // 2) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - pre_c, (rewards_d * 1 // 10 + rewards_m // 2) * 96 // 100) + rewards_d  * 4// 10 * 96 // 100
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert bayc.ownerOf(1) == nft_guy
	(self, dogless, ids, pO, dO) = matcher.matches(6)
	assert (dogless & 1, ids, pO, dO, self) == (0, 0, NULL, NULL, False)
