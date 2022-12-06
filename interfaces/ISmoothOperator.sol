pragma solidity ^0.8.17;

import "./IApeMatcher.sol";

interface ISmoothOperator is IApeMatcher {
	function commitNFTs(address _primary, uint256 _tokenId, uint256 _gammaId) external;

	function uncommitNFTs(GreatMatch calldata _match) external returns(uint256);

	function claim(address _primary, uint256 _tokenId, uint256 _gammaId) external returns(uint256);

	function swapPrimaryNft(address _primary, uint256 _in, uint256 _out, address _receiver, uint256 _gammaId) external;

	function swapDoggoNft(address _primary, uint256 _primaryId, uint256 _in, uint256 _out, address _receiver) external;
}