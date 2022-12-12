pragma solidity ^0.8.17;

interface IApeMatcherHelper {

	struct DepositPosition {
		uint32 count;
		address depositor;
	}

	struct GreatMatch {
		bool	active;	
		uint8	primary;			// alpha:1/beta:2
		uint32	start;				// time of activation
		uint96	ids;				// right most 48 bits => primary | left most 48 bits => doggo
		address	primaryOwner;
		address	primaryTokensOwner;	// owner of ape tokens attributed to primary
		address doggoOwner;
		address	doggoTokensOwner;	// owner of ape tokens attributed to doggo
	}

	function assetToUser(address, uint256) external view returns(address);
	function alphaSpentCounter() external view returns(uint256);
	function betaSpentCounter() external view returns(uint256);
	function gammaSpentCounter() external view returns(uint256);
	function alphaDepositCounter() external view returns(uint256);
	function betaDepositCounter() external view returns(uint256);
	function gammaDepositCounter() external view returns(uint256);

	function depositPosition(uint256, uint256) external view returns(DepositPosition memory);
	function matches(uint256) external view returns(GreatMatch memory);
	function matchCounter() external view returns(uint256);

}