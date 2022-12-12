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

	function getUserQueuedNftsIDs(address _user, IERC721Enumerable _nft, uint256 _index) external view returns(uint256[] memory tokenIds) {
		tokenIds = new uint256[](200);
		uint256 j;
		uint256 balance = _nft.balanceOf(address(MATCHER));
		uint256 len = balance - _index;
		if (len > 200)
			len = 200 + _index;
		else
			len = balance;
		for(uint256 i = _index; i < balance; i++) {
			uint256 tokenId = _nft.tokenOfOwnerByIndex(address(MATCHER), i);
			address owner = MATCHER.assetToUser(address(_nft), tokenId);
			if (_user == owner)
				tokenIds[j++] = tokenId;
		}
	}

	function getUserQueuedCoinDepositsIDs(address _user, uint256 _type, uint256 _index) external view returns(uint256[] memory depositIds) {
		depositIds = new uint256[](200);
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
		uint256 len = end - start;
		if (_index > start) {
			len = end - _index;
			start = _index;
		}
		if (len > 200)
			len = start + 200;
		for(uint256 i = start; i < len; i++) {
			IApeMatcherHelper.DepositPosition memory pos =  MATCHER.depositPosition(_type, i);
			if (pos.depositor == _user)
				depositIds[j++] = i;
		}
	}

	function getUserMatches(address _user, uint256 _index) external view returns(IApeMatcherHelper.GreatMatch[] memory matches) {
		matches = new IApeMatcherHelper.GreatMatch[](100);
		uint256 j;
		uint256 counter = MATCHER.matchCounter();
		uint256 len = counter - _index;
		if (len > 100)
			len = _index + 100;

		for(uint256 i = _index; i < len; i++) {
			IApeMatcherHelper.GreatMatch memory _match = MATCHER.matches(i);
			if (_user == _match.primaryOwner ||
				_user == _match.primaryTokensOwner ||
				_user == _match.doggoOwner ||
				_user == _match.doggoTokensOwner)
				matches[j++] = _match;
		}
	}
}