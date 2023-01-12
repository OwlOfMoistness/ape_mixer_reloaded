// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

contract MockSplit {

	function smartSplit(uint128 _total, address[4] memory _adds, bool _claimGamma) external pure returns(uint128[4] memory splits) {
		uint256 i = 0;
		splits = _getWeights(_claimGamma);
		uint128 sum  = 0;
		// make sum and remove weight if address is null
		for (i = 0 ; i < 4 ; i++)
			sum += splits[i];
		// update splits
		for (i = 0 ; i < 4 ; i++)
			splits[i] =  _total * splits[i] / sum;

		for (i = 0 ; i < 3 ; i++)
			for (uint256 j = i + 1 ; j < 4 ; j++) {
				if (_adds[i] == _adds[j] && splits[j] > 0) {
					splits[i] += splits[j];
					splits[j] = 0;
				}
			}
	}

	function _getWeights(bool _claimGamma) internal pure returns(uint128[4] memory weights) {
		// TODO check if we fetch price feed from bend dao and have a dynamic weight or do static
		// NOTE historically looks like nfts are 2x more valuable than token req
		if (_claimGamma) {
			weights[0] = 100;  // 10%
			weights[1] = 100;  // 10%
			weights[2] = 400; // 40%
			weights[3] = 400; // 40%
		}
		else {
			weights[0] = 500;  // 50%
			weights[1] = 500;  // 50%
			weights[2] = 0;
			weights[3] = 0;
		}
	}
}