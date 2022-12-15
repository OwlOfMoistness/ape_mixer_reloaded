pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeMatcherHelper.sol";


contract ApeMatcherHelper {

	struct RewardInfo {
		uint128 primaryRewards;
		uint128 gammaRewards;
	}

	IApeStaking public immutable APE_STAKING;
	IERC721Enumerable public immutable ALPHA;
	IERC721Enumerable public immutable BETA;
	IERC721Enumerable public immutable GAMMA;
	IERC20 public immutable APE;
	IApeMatcherHelper public immutable MATCHER;
	address public immutable SMOOTH;

	uint256 constant ALPHA_SHARE = 10094 ether; //bayc
	uint256 constant BETA_SHARE = 2042 ether; // mayc
	uint256 constant GAMMA_SHARE = 856 ether; // dog
	uint256 constant EOF = 69420;

	constructor(address a, address b, address c, address d, address e, address f, address g) {
		APE_STAKING = IApeStaking(a);
		ALPHA = IERC721Enumerable(b);
		BETA = IERC721Enumerable(c);
		GAMMA = IERC721Enumerable(d);
		APE = IERC20(e);
		MATCHER = IApeMatcherHelper(f);
		SMOOTH = address(g);
	}

	function getUserQueuedNftsIDs(address _user, IERC721Enumerable _nft, uint256 _index, uint256 _maxLen) external view returns(uint256[] memory tokenIds) {
		tokenIds = new uint256[](_maxLen + 1);
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
		tokenIds[j++] = EOF;
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

	function getUserMatches(address _user, uint256 _index, uint256 _maxLen) external view returns(IApeMatcherHelper.GreatMatchWithId[] memory) {
		IApeMatcherHelper.GreatMatchWithId[] memory matches = new IApeMatcherHelper.GreatMatchWithId[](_maxLen);
		uint256 j;
		uint256 counter = MATCHER.matchCounter();

		if (_index > counter)
			return new IApeMatcherHelper.GreatMatchWithId[](0);

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
				matches[j++] = IApeMatcherHelper.GreatMatchWithId(i, _match);
		}
		return matches;
	}

	function getDoglessArray(uint256 _index, uint256 _maxLen) external view returns(uint256[] memory) {
		uint256[] memory arr = new uint256[](_maxLen);
		uint256 j;
		uint256 counter = MATCHER.doglessMatchCounter();

		if (_index > counter)
			return new uint256[](0);
		
		uint256 endIndex = _index + _maxLen;
		if (counter < endIndex)
			endIndex = counter;
		for(uint256 i = _index; i < endIndex; i++) {
			arr[j++] = MATCHER.doglessMatches(i);
		}
		return arr;
	}

	function getPendingRewardsOfMatches(uint256[] calldata _matchIds) external view returns(RewardInfo[] memory){
		RewardInfo[] memory arr = new RewardInfo[](_matchIds.length);
		for (uint256 i = 0; i < _matchIds.length; i++) {
			IApeMatcherHelper.GreatMatch memory _match = MATCHER.matches(_matchIds[i]);
			uint256 tP = APE_STAKING.pendingRewards(_match.primary, SMOOTH, _match.ids & 0xffffffffffff);
			uint256 tG;
			if (_match.ids >> 48 > 0)
				tG = APE_STAKING.pendingRewards(3, SMOOTH, _match.ids >> 48);
			arr[i] = RewardInfo(uint128(tP), uint128(tG));
		}
		return arr;
	}
}