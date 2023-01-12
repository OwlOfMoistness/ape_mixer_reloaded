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

def assert_expected_payment_both(matcher, p1, p2, p3, p4, reward_p, rewards_d, s):
	assert math.isclose(matcher.payments(p1) - s[0], (reward_p // 2 + rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(p2) - s[1], (reward_p // 2 + rewards_d * 1 // 10) * 96 // 100 + rewards_d * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p3) - s[2], rewards_d * 4 // 10 * 96 // 100)
	# assert math.isclose(matcher.payments(p4) - s[3], rewards_d * 4 // 10 * 96 // 100)

def assert_expected_payment_dog(matcher, p1, p2, p3, p4, rewards, s):
	assert math.isclose(matcher.payments(p1) - s[0], rewards * 1 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p2) - s[1], rewards * 1 // 10 * 96 // 100 + rewards * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p3) - s[2], rewards * 4 // 10 * 96 // 100)
	# assert math.isclose(matcher.payments(p4) - s[3], rewards * 4 // 10 * 96 // 100)

def assert_expected_payment(matcher, p1, p2, rewards, s):
	assert math.isclose(matcher.payments(p1) - s[0], rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(p2) - s[1], rewards // 2 * 96 // 100)

def test_break_match_bayc(matcher, ape, bayc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder):
	ape.mint(coin_guy, '1000000 ether')
	ape.mint(other_guy, '100000000 ether')
	bayc.mint(nft_guy, 10)
	bayc.mint(dog_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.setApprovalForAll(matcher, True, {'from':dog_guy})
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})
	ape.approve(ape_staking, 2 ** 256 - 1, {'from':other_guy})

	ape_staking.depositSelfApeCoin('100000000 ether', {'from':other_guy})
	compounder.deposit('10100 ether', {'from':coin_guy})
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, 1, nft_guy, NULL, False)
	with reverts('!prim'):
		matcher.batchSmartBreakMatch([0], [[True, False, False,]], {'from':nft_guy})
	# with reverts('!alpha'):
	# 	matcher.batchSmartBreakMatch([0], [[False, True, False, False]], {'from':coin_guy})
	with reverts('!mtch'):
		matcher.batchSmartBreakMatch([0], [[True, False, False]], {'from':other_guy})
	matcher.depositNfts([11], [], [], {'from':dog_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, NULL, NULL)
	reward = ape_staking.pendingRewards(1, smooth, 1)
	assert reward > 0
	matcher.batchSmartBreakMatch([0], [[True, False, False]], {'from':nft_guy})
	assert_expected_payment(matcher, nft_guy, compounder, reward, snap)
	assert bayc.ownerOf(1) == nft_guy
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, 11, dog_guy, NULL, False)
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, dog_guy, compounder, NULL, NULL)
	reward = ape_staking.pendingRewards(1, smooth, 11)
	assert reward > 0
	# matcher.depositApeToken([1,0,0], {'from':other_guy})
	# matcher.batchSmartBreakMatch([0], [[False, True, False, False]], {'from':coin_guy})
	# assert compounder.fundsLocked(other_guy) == 0
	# assert matcher.alphaCurrentTotalDeposits() == 0
	# assert_expected_payment(matcher, dog_guy, coin_guy, reward, snap)
	# assert ape.balanceOf(coin_guy) == '1000000 ether'
	# (self, dogless, ids, pO, dO) = matcher.matches(0)
	# assert (dogless & 1, ids, pO, dO, self) == (1, 11, dog_guy, other_guy, NULL, NULL)
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, dog_guy, compounder, NULL, NULL)
	reward = ape_staking.pendingRewards(1, smooth, 11)
	assert reward > 0
	matcher.batchSmartBreakMatch([0], [[True, False, False]], {'from':dog_guy})
	assert_expected_payment(matcher, dog_guy, compounder, reward, snap)
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, 1, nft_guy, NULL, False)
	assert bayc.ownerOf(11) == dog_guy

def test_break_match_mayc(matcher, ape, mayc, smooth, nft_guy, dog_guy, coin_guy, other_guy, chain, ape_staking, compounder):
	mayc.mint(nft_guy, 10)
	mayc.mint(dog_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.setApprovalForAll(matcher, True, {'from':dog_guy})

	compounder.deposit('2042 ether', {'from':coin_guy})
	pre_smooth = ape.balanceOf(smooth)
	matcher.depositNfts([], [1], [], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, 1, nft_guy, NULL, False)



	with reverts('!prim'):
		matcher.batchSmartBreakMatch([1], [[True, False, False]], {'from':nft_guy})
	with reverts('!mtch'):
		matcher.batchSmartBreakMatch([1], [[True, False, False]], {'from':other_guy})
	matcher.depositNfts([], [11], [], {'from':dog_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, NULL, NULL)
	reward = ape_staking.pendingRewards(2, smooth, 1)
	assert reward > 0
	matcher.batchSmartBreakMatch([1], [[True, False, False]], {'from':nft_guy})
	assert_expected_payment(matcher, nft_guy, compounder, reward, snap)
	assert mayc.ownerOf(1) == nft_guy
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, 11, dog_guy, NULL, False)
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, dog_guy, compounder, NULL, NULL)
	reward = ape_staking.pendingRewards(2, smooth, 11)
	assert reward > 0
	matcher.depositNfts([], [1], [], {'from':nft_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, dog_guy, compounder, NULL, NULL)
	reward = ape_staking.pendingRewards(2, smooth, 11)
	assert reward > 0
	matcher.batchSmartBreakMatch([1], [[True, False, False]], {'from':dog_guy})
	assert_expected_payment(matcher, dog_guy, compounder, reward, snap)
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, 1, nft_guy, NULL, False)
	assert mayc.ownerOf(11) == dog_guy

def test_break_match_bakc_on_mayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, some_guy, accounts, chain, ape_staking, compounder):
	bakc.mint(dog_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':dog_guy})
	bakc.mint(some_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':some_guy})
	compounder.deposit('856 ether', {'from':coin_guy})
	assert matcher.doglessMatchCounter() == 2
	matcher.depositNfts([], [], [3], {'from':dog_guy})
	assert matcher.doglessMatchCounter() == 1
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, (3 << 48) + 1, nft_guy, dog_guy, False)
	with reverts('!dog'):
		matcher.batchSmartBreakMatch([1], [[False, False, True]], {'from':dog_guy})
	with reverts('!mtch'):
		matcher.batchSmartBreakMatch([1], [[True, False, False]], {'from':accounts[9]})
	matcher.depositNfts([], [], [13], {'from':some_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, dog_guy, compounder)
	reward = ape_staking.pendingRewards(3, smooth, 3)
	assert reward > 0
	matcher.batchSmartBreakMatch([1], [[False, False, True]], {'from':dog_guy})
	assert_expected_payment_dog(matcher, nft_guy, compounder, dog_guy, compounder, reward, snap)
	assert bakc.ownerOf(3) == dog_guy
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, (13 << 48) + 1, nft_guy, some_guy, False)
	chain.sleep(86400)
	chain.mine()
	# assert ape.balanceOf(smooth) == 0

def test_break_match_bakc_on_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, some_guy, accounts, chain, ape_staking, compounder):
	assert matcher.doglessMatchCounter() == 1
	compounder.deposit('856 ether', {'from':coin_guy})
	matcher.depositNfts([], [], [8], {'from':dog_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, (8 << 48) + 1, nft_guy, dog_guy, False)
	with reverts('!dog'):
		matcher.batchSmartBreakMatch([0], [[False, False, True]], {'from':dog_guy})
	with reverts('!mtch'):
		matcher.batchSmartBreakMatch([0], [[True, False, False]], {'from':accounts[9]})
	matcher.depositNfts([], [], [18], {'from':some_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, dog_guy, compounder)
	reward = ape_staking.pendingRewards(3, smooth, 8)
	assert reward > 0
	matcher.batchSmartBreakMatch([0], [[True, True, True]], {'from':dog_guy})
	assert_expected_payment_dog(matcher, nft_guy, compounder, dog_guy, compounder, reward, snap)
	assert bakc.ownerOf(8) == dog_guy
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, (18 << 48) + 1, nft_guy, some_guy, False)
	pre = ape.balanceOf(coin_guy)
	# assert ape.balanceOf(smooth) == 0

def test_break_filled_match_bayc(matcher, ape, bayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, mix_guy, some_guy, chain, ape_staking, compounder):
	bayc.mint(mix_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':mix_guy})
	assert bayc.balanceOf(matcher) == 0
	# compounder.deposit('10094 ether', {'from':coin_guy})
	matcher.depositNfts([21], [], [], {'from':mix_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, some_guy, compounder)
	reward = ape_staking.pendingRewards(1, smooth, 1)
	reward_d = ape_staking.pendingRewards(3, smooth, 18)
	assert reward > 0
	assert reward_d > 0
	matcher.batchSmartBreakMatch([0], [[True, True, False]], {'from':nft_guy})
	assert_expected_payment_both(matcher, nft_guy, compounder, some_guy, compounder, reward, reward_d, snap)
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, (18 << 48) + 21, mix_guy, some_guy, False)
	assert bayc.ownerOf(1) == nft_guy
	# matcher.depositApeToken([2,0,0], {'from':coin_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, mix_guy, compounder, some_guy, compounder)
	reward = ape_staking.pendingRewards(1, smooth, 21)
	reward_d = ape_staking.pendingRewards(3, smooth, 18)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([0], 0, {'from':some_guy})
	matcher.batchClaimRewardsFromMatches([0], 0, {'from':mix_guy})
	assert_expected_payment_both(matcher, mix_guy, compounder, some_guy, compounder, reward, reward_d,snap)
	(self, dogless, ids, pO, dO) = matcher.matches(0)
	assert (dogless & 1, ids, pO, dO, self) == (1, (18 << 48) + 21, mix_guy, some_guy, False)


def test_break_filled_match_mayc(matcher, ape, mayc, bakc, smooth, nft_guy, dog_guy, coin_guy, other_guy, mix_guy, some_guy, chain, ape_staking, compounder):
	mayc.mint(mix_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':mix_guy})
	assert mayc.balanceOf(matcher) == 0
	matcher.depositNfts([], [21], [], {'from':mix_guy})
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, some_guy, compounder)
	reward = ape_staking.pendingRewards(2, smooth, 1)
	reward_d = ape_staking.pendingRewards(3, smooth, 13)
	assert reward > 0
	assert reward_d > 0
	matcher.batchSmartBreakMatch([1], [[True, True, False]], {'from':nft_guy})
	assert_expected_payment_both(matcher, nft_guy, compounder, some_guy, compounder, reward, reward_d, snap)
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, (13 << 48) + 21, mix_guy, some_guy, False)
	assert mayc.ownerOf(1) == nft_guy
	# assert ape.balanceOf(smooth) == 0
	pre = ape.balanceOf(other_guy)
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, mix_guy, compounder, some_guy, compounder)
	reward = ape_staking.pendingRewards(2, smooth, 21)
	reward_d = ape_staking.pendingRewards(3, smooth, 13)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([1], 0, {'from':some_guy})
	matcher.batchClaimRewardsFromMatches([1], 0, {'from':mix_guy})
	assert_expected_payment_both(matcher, mix_guy, compounder, some_guy, compounder, reward, reward_d,snap)
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, (13 << 48) + 21, mix_guy, some_guy, False)
