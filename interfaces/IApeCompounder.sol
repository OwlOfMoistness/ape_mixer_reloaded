pragma solidity ^0.8.17;

interface IApeCompounder {
	function borrow(uint256 _amount) external;
	function repay(uint256 _amount) external;
	function unlockOnBehalf(uint256 _amount, address _user) external;
	function liquid() external view returns(uint256);
	function lockOnBehalf(uint256 _amount, address _user) external;
	function permissionnedDepositFor(uint256 _amount, address _user) external;
	function withdrawAndUnlockExactAmountOnBehalf(uint256 _amount, address _user, address _to) external;
}