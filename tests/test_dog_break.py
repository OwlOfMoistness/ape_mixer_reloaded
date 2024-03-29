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

def get_payment_snapshot(matcher, p1, p2, p3, p4, ):
	return [
		matcher.payments(p1),
		matcher.payments(p2),
		matcher.payments(p3),
		matcher.payments(p4)
	]

def assert_expected_payment(matcher, p1, p2, p3, p4, rewards, s):
	assert math.isclose(matcher.payments(p1) - s[0], rewards * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p2) - s[1], rewards * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p3) - s[2], rewards * 1 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p4) - s[3], rewards * 1 // 10 * 96 // 100)

def test_break_dog_match_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder):
	ape.mint(coin_guy, '1000000 ether')
	bayc.mint(nft_guy, 10)
	bakc.mint(dog_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.setApprovalForAll(matcher, True, {'from':dog_guy})
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})

	compounder.deposit('1000000 ether', {'from':coin_guy})
	pre_ape = compounder.liquid()
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	matcher.depositNfts([], [], [2], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 0
	assert compounder.liquid() == pre_ape - BAYC_CAP - BAKC_CAP
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, (2 << 48) + 1, nft_guy, dog_guy, False)
	with reverts('!mtch'):
		matcher.batchBreakMatch([0], [False], {'from':other_guy})
	with reverts('!mtch'):
		matcher.batchBreakMatch([1], [False], {'from':nft_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, coin_guy, dog_guy, coin_guy)
	reward = ape_staking.pendingRewards(3, smooth, 2)
	assert reward > 0
	matcher.batchBreakMatch([0], [False], {'from':dog_guy})
	assert math.isclose(matcher.payments(nft_guy) - snap[0], reward * 1 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1], reward * 1 // 10 * 96 // 100 + reward * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - snap[2], reward * 4 // 10 * 96 // 100)
	assert matcher.doglessMatchCounter() == 1
	assert bakc.ownerOf(2) == dog_guy
	assert matcher.assetToUser(bakc, 2) == NULL
	assert compounder.liquid() == pre_ape - BAYC_CAP
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, 1, nft_guy, NULL, False)

def test_break_dog_match_mayc(matcher, ape, mayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder, admin):
	mayc.mint(nft_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})

	matcher.depositNfts([], [], [2], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 0
	pre_ape = compounder.liquid()
	matcher.depositNfts([], [2], [], {'from':nft_guy})
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 0
	assert compounder.liquid() == pre_ape - MAYC_CAP - BAKC_CAP
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, (3 << 48) + 2, nft_guy, dog_guy, False)
	with reverts('!mtch'):
		matcher.batchBreakMatch([1], [False], {'from':other_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, dog_guy, compounder)
	reward = ape_staking.pendingRewards(3, smooth, 3)
	assert reward > 0
	pool0_rewards = ape_staking.pendingRewards(0, compounder, 0)
	compounder.batchBreakMatch([1], [False], {'from':admin})
	assert math.isclose(matcher.payments(nft_guy) - snap[0], reward * 1 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1], reward * 1 // 10 * 96 // 100 + reward * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - snap[2], reward * 4 // 10 * 96 // 100)

	assert matcher.doglessMatchCounter() == 1
	assert bakc.ownerOf(3) == matcher
	assert compounder.liquid() - pool0_rewards == pre_ape - MAYC_CAP
	assert matcher.assetToUser(bakc, 3) == dog_guy
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, 2, nft_guy, NULL, False)

def test_combo_bind_break(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, compounder, admin):
	pre_ape = compounder.liquid()
	compounder.makeMatches({'from':admin})
	assert matcher.doglessMatchCounter() == 0
	compounder.batchBreakMatch([1], [False], {'from':admin})
	assert compounder.liquid() == pre_ape
	assert matcher.doglessMatchCounter() == 1
	compounder.makeMatches({'from':admin})
	assert matcher.doglessMatchCounter() == 0
	matcher.batchBreakMatch([1], [False], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 1
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 0
	matcher.batchBreakMatch([1], [False], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 1
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 0
	assert compounder.liquid() == pre_ape - BAKC_CAP
	matcher.batchBreakMatch([1], [False], {'from':dog_guy})
	assert bakc.ownerOf(3) == dog_guy
	assert matcher.assetToUser(bakc, 3) == NULL
	assert compounder.liquid() == pre_ape