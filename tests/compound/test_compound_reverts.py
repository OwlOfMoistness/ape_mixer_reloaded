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
POOL_0_DAILY_RATE = 10500000000000000000000000 // (MAYC_Q1 // 86400)
BAYC_DAILY_RATE =   16486750000000000000000000 // (MAYC_Q1 // 86400)
MAYC_DAILY_RATE = 6671000000000000000000000 // (MAYC_Q1 // 86400)
BAKC_DAILY_RATE = 1342250000000000000000000 // (BAKC_Q1 // 86400)

def test_revert_only_matcher_calls(matcher, coin_guy, compounder):
	with reverts():
		compounder.borrow(0, {'from':coin_guy})
	with reverts():
		compounder.repay(0, {'from':coin_guy})
	with reverts():
		compounder.repayAndWithdrawOnBehalf(0, coin_guy, {'from':coin_guy})
	with reverts():
		compounder.permissionnedDepositFor(0, coin_guy, {'from':coin_guy})
	with reverts():
		compounder.depositOnBehalf(0, coin_guy, {'from':coin_guy})
	with reverts():
		compounder.withdrawExactAmountOnBehalf(0, coin_guy, coin_guy, {'from':coin_guy})