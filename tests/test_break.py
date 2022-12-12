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

def test_break_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking):
	ape.mint(coin_guy, '1000000 ether')
	bayc.mint(nft_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})
	to_sleep = 0 if chain.time() > 1670864400 else 1670864400 - chain.time()
	chain.sleep(to_sleep)
	chain.mine()
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	matcher.depositApeToken([1,0,0], {'from':coin_guy})
	with reverts('!match'):
		matcher.batchBreakMatch([0], [False], {'from':other_guy})
	with reverts('Must wait min duration to break clause'):
		matcher.batchBreakMatch([0], [False], {'from':nft_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(1, smooth, 1)
	matcher.batchBreakMatch([0], [False], {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy), rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy), rewards // 2 * 96 // 100)
	assert bayc.ownerOf(1) == nft_guy
	matcher.alphaCurrentTotalDeposits() == 1
	matcher.alphaDepositCounter() == 2
	matcher.alphaSpentCounter() == 1
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	with reverts('Must wait min duration to break clause'):
		matcher.batchBreakMatch([1], [False], {'from':nft_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(1, smooth, 1)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	matcher.batchBreakMatch([1], [False], {'from':coin_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, rewards // 2 * 96 // 100)
	assert bayc.ownerOf(1) == matcher
	with reverts('ApeMatcher: !owner'):
		matcher.depositNfts([1], [], [], {'from':dog_guy})
	assert ape.balanceOf(coin_guy) == '1000000 ether'
	matcher.alphaCurrentTotalDeposits() == 0

def test_break_mayc(matcher, ape, mayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking):
	mayc.mint(nft_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	matcher.depositNfts([], [2], [], {'from':nft_guy})
	matcher.depositApeToken([0,1,0], {'from':coin_guy})
	with reverts('!match'):
		matcher.batchBreakMatch([2], [False], {'from':other_guy})
	with reverts('Must wait min duration to break clause'):
		matcher.batchBreakMatch([2], [False], {'from':nft_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(2, smooth, 2)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	matcher.batchBreakMatch([2], [False], {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, rewards // 2 * 96 // 100)
	assert mayc.ownerOf(2) == nft_guy
	matcher.betaCurrentTotalDeposits() == 1
	matcher.betaDepositCounter() == 2
	matcher.betaSpentCounter() == 1
	matcher.depositNfts([], [2], [], {'from':nft_guy})
	with reverts('Must wait min duration to break clause'):
		matcher.batchBreakMatch([3], [False], {'from':nft_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(2, smooth, 2)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	matcher.batchBreakMatch([3], [False], {'from':coin_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, rewards // 2 * 96 // 100)
	assert mayc.ownerOf(2) == matcher
	with reverts('ApeMatcher: !owner'):
		matcher.depositNfts([], [2], [], {'from':dog_guy})
	assert ape.balanceOf(coin_guy) == '1000000 ether'
	matcher.betaCurrentTotalDeposits() == 0

def test_break_dog_calling_standard_break_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking):
	ape.mint(other_guy, '1000000 ether')
	bakc.mint(dog_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':dog_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':other_guy})
	matcher.depositApeToken([1,0,0], {'from':coin_guy})
	matcher.depositApeToken([0,0,1], {'from':other_guy})
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	with reverts('Must wait min duration to break clause'):
		matcher.batchBreakMatch([4], [False], {'from':dog_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(1, smooth, 1)
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	pre_d = matcher.payments(dog_guy)
	pre_o = matcher.payments(other_guy)
	matcher.batchBreakMatch([4], [False], {'from':dog_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(other_guy) - pre_o, rewards_d  * 4// 10 * 96 // 100)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, 1, nft_guy, coin_guy, NULL, NULL)
	assert bakc.ownerOf(3) == dog_guy
	matcher.gammaCurrentTotalDeposits() == 1
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	pre_d = matcher.payments(dog_guy)
	pre_o = matcher.payments(other_guy)
	matcher.batchBreakMatch([4], [False], {'from':other_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(other_guy) - pre_o, rewards_d  * 4// 10 * 96 // 100)
	assert bakc.ownerOf(3) == matcher
	assert ape.balanceOf(other_guy) == '1000000 ether'

def test_break_dog_calling_standard_break_mayc(matcher, ape, mayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking):
	bakc.mint(dog_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':dog_guy})
	ape.approve(matcher, 2 ** 256 - 1, {'from':other_guy})
	matcher.depositApeToken([0,1,0], {'from':coin_guy})
	matcher.depositApeToken([0,0,1], {'from':other_guy})
	with reverts('Must wait min duration to break clause'):
		matcher.batchBreakMatch([5], [False], {'from':dog_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards = ape_staking.pendingRewards(2, smooth,41)
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	pre_d = matcher.payments(dog_guy)
	pre_o = matcher.payments(other_guy)
	matcher.batchBreakMatch([5], [False], {'from':dog_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(other_guy) - pre_o, rewards_d  * 4// 10 * 96 // 100)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(5)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, 2, nft_guy, coin_guy, NULL, NULL)
	assert bakc.ownerOf(3) == dog_guy
	matcher.gammaCurrentTotalDeposits() == 1
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	pre_d = matcher.payments(dog_guy)
	pre_o = matcher.payments(other_guy)
	matcher.batchBreakMatch([5], [False], {'from':other_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, (rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(other_guy) - pre_o, rewards_d  * 4// 10 * 96 // 100)
	assert bakc.ownerOf(3) == matcher
	assert ape.balanceOf(other_guy) == '1000000 ether'

def test_break_primary_filled_match_mayc(matcher, ape, mayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking):
	matcher.depositApeToken([0,0,1], {'from':other_guy})
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(5)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 2, (3 << 48) + 2, nft_guy, coin_guy, dog_guy, other_guy)
	chain.sleep(7 * 86400 + 1)
	chain.mine()
	rewards_m = ape_staking.pendingRewards(2, smooth, 2)
	rewards_d = ape_staking.pendingRewards(3, smooth, 3)
	pre_n = matcher.payments(nft_guy)
	pre_c = matcher.payments(coin_guy)
	pre_d = matcher.payments(dog_guy)
	pre_o = matcher.payments(other_guy)
	assert bakc.ownerOf(3) == smooth
	matcher.batchBreakMatch([5], [False], {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - pre_n, (rewards_d * 1 // 10 + rewards_m // 2) * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy) - pre_c, (rewards_d * 1 // 10 + rewards_m // 2) * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - pre_d, rewards_d * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(other_guy) - pre_o, rewards_d  * 4// 10 * 96 // 100)
	assert mayc.ownerOf(2) == nft_guy
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(4)
	assert (active, pri, ids, pO, pT, dO, dT) == (True, 1, (3 << 48) + 1, nft_guy, coin_guy, dog_guy, other_guy)
	(active, pri, _, ids, pO, pT, dO, dT) = matcher.matches(5)
	assert (active, pri, ids, pO, pT, dO, dT) == (False, 0, 0, NULL, NULL, NULL, NULL)
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.betaCurrentTotalDeposits() == 1
