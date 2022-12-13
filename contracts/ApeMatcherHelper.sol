pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeMatcherHelper.sol";


contract ApeMatcherHelper {
	IApeStaking public immutable APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	IERC721Enumerable public immutable ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	IERC721Enumerable public immutable BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	IERC721Enumerable public immutable GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	IERC20 public immutable APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);
	IApeMatcherHelper public immutable MATCHER = IApeMatcherHelper(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	uint256 constant ALPHA_SHARE = 10094 ether; //bayc
	uint256 constant BETA_SHARE = 2042 ether; // mayc
	uint256 constant GAMMA_SHARE = 856 ether; // dog

	function getUserQueuedNftsIDs(address _user, IERC721Enumerable _nft, uint256 _index, uint256 _maxLen) external view returns(uint256[] memory tokenIds) {
		tokenIds = new uint256[](_maxLen);
		uint256 j;
		uint256 balance = _nft.balanceOf(address(MATCHER));

		// if _index is higher than balance at time of call, return empty array instead of revert
		if (balance < _index) {
			return new uint256[](0);
		}

		// if endIndex (_index + _maxLen) overflows, set endIndex to balance
		uint256 endIndex = _index + _maxLen;
		if (balance < endIndex)
			endIndex = balance;

		// from index to endIndex, check if asset is owner's and populate tokenIds array
		for(uint256 i = _index; i < endIndex; i++) {
			uint256 tokenId = _nft.tokenOfOwnerByIndex(address(MATCHER), i);
			address owner = MATCHER.assetToUser(address(_nft), tokenId);
			if (_user == owner)
				tokenIds[j++] = tokenId;
		}
	}

	function getUserQueuedCoinDepositsIDs(address _user, uint256 _type, uint256 _index, uint256 _maxLen) external view returns(uint256[] memory depositIds) {
		depositIds = new uint256[](_maxLen);
		uint256 j;
		uint256 start;
		uint256 end;

		if (_type == ALPHA_SHARE) {
			start = MATCHER.alphaSpentCounter();
			end = MATCHER.alphaDepositCounter();
		}
		else if (_type == BETA_SHARE) {
			start = MATCHER.betaSpentCounter();
			end = MATCHER.betaDepositCounter();
		}
		else if (_type == GAMMA_SHARE) {
			start = MATCHER.gammaSpentCounter();
			end = MATCHER.gammaDepositCounter();
		}

		// if start + _index is higher than end (max endIndex) at time of call, return empty array
		if (start + _index > end) {
			return new uint256[](0);
		}

		// if endIndex (_index + _maxLen) overflows, set endIndex to end
		uint256 endIndex = _index + _maxLen;
		if (end < endIndex)
			endIndex = end;

		for(uint256 i = start + _index; i < endIndex; i++) {
			IApeMatcherHelper.DepositPosition memory pos =  MATCHER.depositPosition(_type, i);
			if (pos.depositor == _user)
				depositIds[j++] = i;
		}
	}

	function getUserMatches(address _user, uint256 _index, uint256 _maxLen) external view returns(IApeMatcherHelper.GreatMatch[] memory matches) {
		matches = new IApeMatcherHelper.GreatMatch[](_maxLen);
		uint256 j;
		uint256 counter = MATCHER.matchCounter();

		if (_index > counter)
			return new IApeMatcherHelper.GreatMatch[](0);

		// if endIndex (_index + _maxLen) overflows, set endIndex to counter
		uint256 endIndex = _index + _maxLen;
		if (counter < endIndex)
			endIndex = counter;

		for(uint256 i = _index; i < endIndex; i++) {
			IApeMatcherHelper.GreatMatch memory _match = MATCHER.matches(i);
			if (_user == _match.primaryOwner ||
				_user == _match.primaryTokensOwner ||
				_user == _match.doggoOwner ||
				_user == _match.doggoTokensOwner)
				matches[j++] = _match;
		}
	}
}