import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv

NULL = "0x0000000000000000000000000000000000000000"
BAYC_CAP = 10094000000000000000000
MAYC_CAP = 2042000000000000000000
BAKC_CAP = 856000000000000000000

def test_deposit_one_type(matcher, ape, nft_guy, smooth):
	with reverts('!smooooth'):
		matcher.depositApeTokenForUser([10,10,10], nft_guy, {'from':nft_guy})

	ape.mint(nft_guy, '10_000_000 ether')
	ape.approve(matcher, 2 ** 256 - 1, {'from':nft_guy})
	matcher.depositApeToken([1, 0, 0], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 1
	assert ape.balanceOf(smooth) == BAYC_CAP
	assert matcher.alphaDepositCounter() == 1
	assert matcher.depositPosition(BAYC_CAP, 0) == (1, nft_guy)

	matcher.depositApeToken([0, 1, 0], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 1
	assert ape.balanceOf(smooth) == BAYC_CAP + MAYC_CAP
	assert matcher.betaDepositCounter() == 1
	assert matcher.depositPosition(MAYC_CAP, 0) == (1, nft_guy)

	matcher.depositApeToken([0, 0, 1], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 1
	assert ape.balanceOf(smooth) == BAYC_CAP + MAYC_CAP + BAKC_CAP
	assert matcher.gammaDepositCounter() == 1
	assert matcher.depositPosition(BAKC_CAP, 0) == (1, nft_guy)

def test_withdraw_one_type(matcher, ape, nft_guy, smooth):

	matcher.withdrawApeToken([(0, 1)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert ape.balanceOf(smooth) ==  MAYC_CAP + BAKC_CAP
	assert matcher.alphaDepositCounter() == 0
	assert matcher.depositPosition(BAYC_CAP, 0) == (0, NULL)

	matcher.withdrawApeToken([] ,[(0, 1)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 0
	assert ape.balanceOf(smooth) == BAKC_CAP
	assert matcher.betaDepositCounter() == 0
	assert matcher.depositPosition(MAYC_CAP, 0) == (0, NULL)

	matcher.withdrawApeToken([] ,[], [(0, 1)],{'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert ape.balanceOf(smooth) == 0
	assert matcher.gammaDepositCounter() == 0
	assert matcher.depositPosition(BAKC_CAP, 0) == (0, NULL)

def test_deposit_many_one_type(matcher, ape, nft_guy, smooth):

	matcher.depositApeToken([100, 0, 0], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 100
	assert ape.balanceOf(smooth) == BAYC_CAP * 100
	assert matcher.alphaDepositCounter() == 1
	assert matcher.depositPosition(BAYC_CAP, 0) == (100, nft_guy)

	matcher.depositApeToken([0, 100, 0], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 100
	assert ape.balanceOf(smooth) == (BAYC_CAP + MAYC_CAP) * 100
	assert matcher.betaDepositCounter() == 1
	assert matcher.depositPosition(MAYC_CAP, 0) == (100, nft_guy)

	matcher.depositApeToken([0, 0, 100], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 100
	assert ape.balanceOf(smooth) == (BAYC_CAP + MAYC_CAP + BAKC_CAP) * 100
	assert matcher.gammaDepositCounter() == 1
	assert matcher.depositPosition(BAKC_CAP, 0) == (100, nft_guy)

def test_withdraw_many_one_type(matcher, ape, nft_guy, smooth):

	matcher.withdrawApeToken([(0, 100)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert ape.balanceOf(smooth) ==  (MAYC_CAP + BAKC_CAP) * 100
	assert matcher.alphaDepositCounter() == 0
	assert matcher.depositPosition(BAYC_CAP, 0) == (0, NULL)

	matcher.withdrawApeToken([] ,[(0, 100)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 0
	assert ape.balanceOf(smooth) == BAKC_CAP * 100
	assert matcher.betaDepositCounter() == 0
	assert matcher.depositPosition(MAYC_CAP, 0) == (0, NULL)

	matcher.withdrawApeToken([], [], [(0, 100)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert ape.balanceOf(smooth) == 0
	assert matcher.gammaDepositCounter() == 0
	assert matcher.depositPosition(BAKC_CAP, 0) == (0, NULL)

def test_deposit_many(matcher, ape, nft_guy, smooth):

	matcher.depositApeToken([100, 100, 100], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 100
	assert matcher.alphaDepositCounter() == 1
	assert matcher.depositPosition(BAYC_CAP, 0) == (100, nft_guy)

	assert matcher.betaCurrentTotalDeposits() == 100
	assert matcher.betaDepositCounter() == 1
	assert matcher.depositPosition(MAYC_CAP, 0) == (100, nft_guy)

	assert matcher.gammaCurrentTotalDeposits() == 100
	assert matcher.gammaDepositCounter() == 1
	assert matcher.depositPosition(BAKC_CAP, 0) == (100, nft_guy)

	assert ape.balanceOf(smooth) == (BAYC_CAP + MAYC_CAP + BAKC_CAP) * 100

def test_withdraw_many(matcher, ape, nft_guy, smooth):

	matcher.withdrawApeToken([(0, 100)], [(0, 100)], [(0, 100)], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.alphaDepositCounter() == 0
	assert matcher.depositPosition(BAYC_CAP, 0) == (0, NULL)

	assert matcher.betaCurrentTotalDeposits() == 0
	assert matcher.betaDepositCounter() == 0
	assert matcher.depositPosition(MAYC_CAP, 0) == (0, NULL)

	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.gammaDepositCounter() == 0
	assert matcher.depositPosition(BAKC_CAP, 0) == (0, NULL)

	assert ape.balanceOf(smooth) == 0

def test_revert_outside_index(matcher, ape, nft_guy):
	with reverts('ApeMatcher: deposit !exist'):
		matcher.withdrawApeToken([(1, 0)] ,[], [], {'from':nft_guy})
	with reverts('ApeMatcher: deposit !exist'):
		matcher.withdrawApeToken([], [(1, 0)], [], {'from':nft_guy})
	with reverts('ApeMatcher: deposit !exist'):
		matcher.withdrawApeToken([] , [], [(1, 0)], {'from':nft_guy})

def test_revert_withdraw_not_owned_deposit(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([2, 2, 2], {'from':nft_guy})
	with reverts('ApeMatcher: Not owner of deposit'):
		matcher.withdrawApeToken([(0, 2)] ,[], [],{'from':other_guy})
	with reverts('ApeMatcher: Not owner of deposit'):
		matcher.withdrawApeToken([] ,[(0, 2)], [], {'from':other_guy})
	with reverts('ApeMatcher: Not owner of deposit'):
		matcher.withdrawApeToken([] ,[], [(0, 2)], {'from':other_guy})
	matcher.withdrawApeToken([(0, 2)] ,[(0, 2)], [(0, 2)], {'from':nft_guy})

def test_chain_multi_deposits_same_key(matcher, ape, nft_guy, other_guy):
	for i in range(5):
		matcher.depositApeToken([2, 0, 0], {'from':nft_guy})
		assert matcher.depositPosition(BAYC_CAP, i) == (2, nft_guy)
	assert matcher.alphaCurrentTotalDeposits() == 10
	assert matcher.alphaDepositCounter() == 5
	assert matcher.depositPosition(BAYC_CAP, 6) == (0, NULL)

def test_withdraw_deposit_same_key(matcher, ape, nft_guy, other_guy):
	matcher.withdrawApeToken([(0, 2)] ,[], [], {'from':nft_guy})
	matcher.withdrawApeToken([(0, 2)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 6
	assert matcher.alphaDepositCounter() == 3
	matcher.withdrawApeToken([(2,2),(1, 2),(0, 2)], [], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.alphaDepositCounter() == 0

def test_with_granular_alpha(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([5, 0, 0], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 5
	matcher.withdrawApeToken([(0, 2)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 3
	matcher.withdrawApeToken([(0, 2)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 1
	matcher.withdrawApeToken([(0, 1)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 0

def test_with_granular_beta(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([0, 5, 0], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 5
	matcher.withdrawApeToken([], [(0, 2)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 3
	matcher.withdrawApeToken([], [(0, 2)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 1
	matcher.withdrawApeToken([], [(0, 1)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 0

def test_with_granular_beta(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([0, 0, 5], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 5
	matcher.withdrawApeToken([], [], [(0, 2)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 3
	matcher.withdrawApeToken([], [], [(0, 2)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 1
	matcher.withdrawApeToken([], [], [(0, 1)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 0

def test_revert_large_amount(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([2, 2, 2], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 2
	assert matcher.alphaDepositCounter() == 1
	assert matcher.betaCurrentTotalDeposits() == 2
	assert matcher.betaDepositCounter() == 1
	assert matcher.gammaCurrentTotalDeposits() == 2
	assert matcher.gammaDepositCounter() == 1
	with reverts('ApeMatcher: !amount'):
		matcher.withdrawApeToken([(0, 3)] ,[], [],{'from':nft_guy})
	with reverts('ApeMatcher: !amount'):
		matcher.withdrawApeToken([] ,[(0, 3)], [], {'from':nft_guy})
	with reverts('ApeMatcher: !amount'):
		matcher.withdrawApeToken([] ,[], [(0, 3)], {'from':nft_guy})
	matcher.withdrawApeToken([(0, 2)], [(0, 2)], [(0, 2)], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.alphaDepositCounter() == 0
	assert matcher.betaCurrentTotalDeposits() == 0
	assert matcher.betaDepositCounter() == 0
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.gammaDepositCounter() == 0

def test_with_granular_many_alpha(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([5, 0, 0], {'from':nft_guy})
	matcher.depositApeToken([5, 0, 0], {'from':nft_guy})
	matcher.depositApeToken([5, 0, 0], {'from':nft_guy})
	assert matcher.alphaDepositCounter() == 3
	assert matcher.alphaSpentCounter() == 0
	assert matcher.alphaCurrentTotalDeposits() == 15
	matcher.withdrawApeToken([(0, 3)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 12
	matcher.withdrawApeToken([(1, 3)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 9
	matcher.withdrawApeToken([(2, 3)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 6
	matcher.withdrawApeToken([(2, 2), (1, 2), (0, 2)] ,[], [], {'from':nft_guy})
	assert matcher.alphaCurrentTotalDeposits() == 0
	assert matcher.alphaDepositCounter() == 0

def test_with_granular_many_beta(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([0, 5, 0], {'from':nft_guy})
	matcher.depositApeToken([0, 5, 0], {'from':nft_guy})
	matcher.depositApeToken([0, 5, 0], {'from':nft_guy})
	assert matcher.betaDepositCounter() == 3
	assert matcher.betaSpentCounter() == 0
	assert matcher.betaCurrentTotalDeposits() == 15
	matcher.withdrawApeToken([], [(0, 3)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 12
	matcher.withdrawApeToken([], [(1, 3)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 9
	matcher.withdrawApeToken([], [(2, 3)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 6
	matcher.withdrawApeToken([], [(2, 2), (1, 2), (0, 2)], [], {'from':nft_guy})
	assert matcher.betaCurrentTotalDeposits() == 0
	assert matcher.betaDepositCounter() == 0

def test_with_granular_many_gamma(matcher, ape, nft_guy, other_guy):
	matcher.depositApeToken([0, 0, 5], {'from':nft_guy})
	matcher.depositApeToken([0, 0, 5], {'from':nft_guy})
	matcher.depositApeToken([0, 0, 5], {'from':nft_guy})
	assert matcher.gammaDepositCounter() == 3
	assert matcher.gammaSpentCounter() == 0
	assert matcher.gammaCurrentTotalDeposits() == 15
	matcher.withdrawApeToken([], [], [(0, 3)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 12
	matcher.withdrawApeToken([], [], [(1, 3)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 9
	matcher.withdrawApeToken([], [], [(2, 3)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 6
	matcher.withdrawApeToken([], [], [(2, 2), (1, 2), (0, 2)], {'from':nft_guy})
	assert matcher.gammaCurrentTotalDeposits() == 0
	assert matcher.gammaDepositCounter() == 0