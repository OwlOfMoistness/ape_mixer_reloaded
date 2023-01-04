pragma solidity ^0.8.17;

interface IApeCompounder {
	function borrow(uint256 _amount) external;
	function repay(uint256 _amount) external;
	function repayAndWithdrawOnBehalf(uint256 _amount, address _user) external;
	function liquid() external view returns(uint256);
	function depositOnBehalf(uint256 _amount, address _user) external;
	function permissionnedDepositFor(uint256 _amount, address _user) external;
	function withdrawExactAmountOnBehalf(uint256 _amount, address _user, address _to) external;
}