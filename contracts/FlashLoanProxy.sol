// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract FlashloanManager is Ownable {
	mapping(address => bool) public validImplementations;

	function setValidImplementation(address _implementation, bool _val) external onlyOwner {
		validImplementations[_implementation] = _val;
	}

	/**
	 * @notice
	 * Function that executes flashloan logic given by an approved implementation
	 * @param _nft Contract address of the asset
	 * @param _tokenId Asset ID to be handle
	 * @param _implementation Contract address of the implementation logic
	 * @param _data Payload to send to the implementation via delegatecall
	 */
	function executeFlashLoan(address _nft, uint256 _tokenId, address _implementation, bytes calldata _data) external {
		require(validImplementations[_implementation], "imp");

		(bool success,) = _implementation.delegatecall(_data);
		require(success);
		IERC721Enumerable(_nft).transferFrom(address(this), msg.sender, _tokenId);
	}

	/**
	 * @notice
	 * Nothing should be in this contract. Shame on you if you send anything.
	 */
	function exec(address _target, bytes calldata _data) external payable onlyOwner {
		(bool success,) = _target.call{value:msg.value}(_data);
		require(success);
	}
}