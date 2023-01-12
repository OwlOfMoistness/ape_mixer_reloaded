import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv

NULL = "0x0000000000000000000000000000000000000000"

def test_revert_operator(matcher, admin):
	assert matcher.smoothOperator() != NULL
	with reverts():
		matcher.init(admin, admin, {'from':admin})

def test_exec_smooth(smooth, admin, bayc, mayc, bakc, ape, matcher):
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(bayc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(mayc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(bakc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(ape,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(matcher,'', {'from':admin})
	smooth.exec(admin,'', {'from':admin})

def test_ownership(smooth, admin, matcher, dog_guy):
	with reverts('Ownable: caller is not the owner'):
		matcher.transferOwnership(dog_guy, {'from':dog_guy})
	with reverts('Ownable: new owner is the zero address'):
		matcher.transferOwnership(NULL, {'from':admin})
	matcher.transferOwnership(dog_guy, {'from':admin})
	matcher.transferOwnership(admin, {'from':dog_guy})

	with reverts('Ownable: caller is not the owner'):
		smooth.transferOwnership(dog_guy, {'from':dog_guy})
	with reverts('Ownable: new owner is the zero address'):
		smooth.transferOwnership(NULL, {'from':admin})
	smooth.transferOwnership(dog_guy, {'from':admin})
	smooth.transferOwnership(admin, {'from':dog_guy})

def test_smooth_access(smooth, dog_guy):
	with reverts("Smooth: Can't toucht this"):
		smooth.swapPrimaryNft(NULL,0,0,NULL,0, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.swapDoggoNft(NULL,0,0,0,NULL, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.claim(NULL,0,0,False, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.commitNFTs(NULL,0,0, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.bindDoggoToExistingPrimary(NULL,0,0, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.unbindDoggoFromExistingPrimary(NULL,0,0,NULL,NULL, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.uncommitNFTs((False,0,0,NULL,NULL),NULL, {'from':dog_guy})

def test_correct_weights(matcher, admin):
	weight = matcher.weights()
	_uint16Mask = 0xffff

	alpha_weight = weight >> (64 * 2)
	alpha_arr = []
	alpha_arr.append(((alpha_weight >> (16 * 3)) & _uint16Mask))
	alpha_arr.append(((alpha_weight >> (16 * 2)) & _uint16Mask))
	alpha_arr.append(((alpha_weight >> (16 * 1)) & _uint16Mask))
	alpha_arr.append(((alpha_weight >> (16 * 0)) & _uint16Mask))
	assert alpha_arr[0] == 500
	assert alpha_arr[1] == 500
	assert alpha_arr[2] == 0
	assert alpha_arr[3] == 0

	beta_weight = weight >> (64 * 1)
	beta_arr = []
	beta_arr.append(((beta_weight >> (16 * 3)) & _uint16Mask))
	beta_arr.append(((beta_weight >> (16 * 2)) & _uint16Mask))
	beta_arr.append(((beta_weight >> (16 * 1)) & _uint16Mask))
	beta_arr.append(((beta_weight >> (16 * 0)) & _uint16Mask))
	print(beta_arr)
	assert beta_arr[0] == 500
	assert beta_arr[1] == 500
	assert beta_arr[2] == 0
	assert beta_arr[3] == 0

	gamma_weight = weight >> (64 * 0)
	gamma_arr = []
	gamma_arr.append(((gamma_weight >> (16 * 3)) & _uint16Mask))
	gamma_arr.append(((gamma_weight >> (16 * 2)) & _uint16Mask))
	gamma_arr.append(((gamma_weight >> (16 * 1)) & _uint16Mask))
	gamma_arr.append(((gamma_weight >> (16 * 0)) & _uint16Mask))
	assert gamma_arr[0] == 100
	assert gamma_arr[1] == 100
	assert gamma_arr[2] == 400
	assert gamma_arr[3] == 400