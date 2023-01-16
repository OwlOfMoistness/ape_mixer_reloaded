// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

contract Debug {
	bool debug;

	function debugOn() external {
		debug = true;
	}

	function debugOff() external {
		debug = false;
	}

	function debugRevert(string memory _msg) internal view {
		if (debug)
			revert(_msg);
	}

	function uint2str(uint _i) internal pure returns (string memory _uintAsString) {
        if (_i == 0) {
            return "0";
        }
        uint j = _i;
        uint len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint k = len;
        while (_i != 0) {
            k = k-1;
            uint8 temp = (48 + uint8(_i - _i / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }
}