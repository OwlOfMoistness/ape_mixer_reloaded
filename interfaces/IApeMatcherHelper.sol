pragma solidity ^0.8.17;

interface IApeMatcherHelper {

	struct DepositPosition {
		uint32 count;
		address depositor;
	}

	struct GreatMatchWithId {
		uint256 id;
		GreatMatch _match;
	}

	struct GreatMatch {
		uint96	doglessIndex;
		uint96	ids;				// right most 48 bits => primary | left most 48 bits => doggo
		address	primaryOwner;
		address	primaryTokensOwner;	// owner of ape tokens attributed to primary
		address doggoOwner;
		address	doggoTokensOwner;	// owner of ape tokens attributed to doggo
	}

	function weights() external view returns(uint256);

	function assetToUser(address, uint256) external view returns(address);
	function alphaSpentCounter() external view returns(uint256);
	function betaSpentCounter() external view returns(uint256);
	function gammaSpentCounter() external view returns(uint256);
	function alphaDepositCounter() external view returns(uint256);
	function betaDepositCounter() external view returns(uint256);
	function gammaDepositCounter() external view returns(uint256);

	function alphaCurrentTotalDeposits() external view returns(uint256);
	function betaCurrentTotalDeposits() external view returns(uint256);
	function gammaCurrentTotalDeposits() external view returns(uint256);

	function depositPosition(uint256, uint256) external view returns(DepositPosition memory);
	function matches(uint256) external view returns(GreatMatch memory);
	function matchCounter() external view returns(uint256);

	function doglessMatchCounter() external view returns(uint256);
	function doglessMatches(uint256) external view returns(uint256);
}