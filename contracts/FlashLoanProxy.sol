// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract FlashloanManager is Ownable {
	mapping(address => bool) public validImplementations;

	function setValidImplementation(address _implementation, bool _val) external onlyOwner {
		validImplementations[_implementation] = _val;
	}

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