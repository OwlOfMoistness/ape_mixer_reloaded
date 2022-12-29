pragma solidity ^0.8.17;

interface IApeCompounder {
	function borrow(uint256 _amount) external;
	function repay(uint256 _amount) external;
	function liquid() external view returns(uint256);
}