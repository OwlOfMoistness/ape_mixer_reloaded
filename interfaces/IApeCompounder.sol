// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

interface IApeCompounder {
	function borrow(uint256 _amount) external;
	function borrowAndWithdrawExactFor(uint256 _amount, address _user) external;
	function repay(uint256 _amount) external;
	function liquid() external view returns(uint256);
	function permissionnedDepositFor(uint256 _amount, address _user) external;
}