// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";


contract Pausable is Ownable {
	bool public paused;

	modifier notPaused() {
		require(!paused, "Pausable: Contract is paused");
		_;
	}

	function pause() external onlyOwner {
		paused = true;
	}

	function unpause() external onlyOwner {
		paused = false;
	}
}