pragma solidity ^0.8.17;

import "./IApeMatcher.sol";

interface ISmoothOperator {
	function commitNFTs(address _primary, uint256 _tokenId, uint256 _gammaId) external;

	function uncommitNFTs(IApeMatcher.GreatMatch calldata _match, address _caller) external returns(uint256, uint256);

	function claim(address _primary, uint256 _tokenId, uint256 _gammaId, uint256 _claimSetup) external returns(uint256 total, uint256 totalGamma);

	function swapPrimaryNft(
		address _primary,
		uint256 _in,
		uint256 _out,
		address _receiver,
		uint256 _gammaId) external returns(uint256 totalGamma, uint256 totalPrimary);

		function swapDoggoNft(
		address _primary,
		uint256 _primaryId,
		uint256 _in,
		uint256 _out,
		address _receiver) external returns(uint256 totalGamma);

	function bindDoggoToExistingPrimary(address _primary, uint256 _tokenId, uint256 _gammaId) external;
	
	function unbindDoggoFromExistingPrimary(
		address _primary,
		uint256 _tokenId,
		uint256 _gammaId,
		address _receiver,
		address _tokenOwner,
		address _caller) external returns(uint256 totalGamma);

	
}