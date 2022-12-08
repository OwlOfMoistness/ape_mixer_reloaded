pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./Pausable.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";

contract ApeMatcher is Pausable, IApeMatcher {

	uint256 constant public MIN_STAKING_PERIOD = 15 days;
	uint256 constant public FEE = 30; // 3%
	uint256 constant public DENOMINATOR = 1000;

	IApeStaking public constant APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	IERC721Enumerable public constant ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	IERC721Enumerable public constant BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	IERC721Enumerable public constant GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	IERC20 public constant APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	uint256 constant ALPHA_SHARE = 10094 ether; //bayc
	uint256 constant BETA_SHARE = 2042 ether; // mayc
	uint256 constant GAMMA_SHARE = 856 ether; // dog

	uint256 fee;
	mapping(address => mapping(uint256 => address)) public assetToUser;

	uint256 public matchCounter;

	uint256 public alphaSpentCounter;
	uint256 public betaSpentCounter;
	uint256 public gammaSpentCounter;

	uint256 public alphaDepositCounter;
	uint256 public betaDepositCounter;
	uint256 public gammaDepositCounter;

	// TODO consider using same mapping feature for nfts to enable restaking if user configs in such way
	// NOTE how => spentocunter decreases and nft is sent at beginning of line, skipping everyone

	mapping(uint256 => mapping(uint256 => address)) public shareDeposits;
	mapping(uint256 => GreatMatch) public matches;
	mapping(address => uint256) public payments;

	ISmoothOperator public smoothOperator; // add interface to our smooth operator

	function setOperator(address _operator) external onlyOwner {
		require(address(smoothOperator) == address(0));
		smoothOperator = ISmoothOperator(_operator);
	}

	function fetchApe() external onlyOwner {
		uint256 amount = fee;
		fee = 0;
		APE.transfer(owner(), amount);
	}

	function depositNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external notPaused {
		if (_gammaIds.length > 0)
			_depositNfts(GAMMA, _gammaIds, msg.sender);
		if (_alphaIds.length > 0) {
			_depositNfts(ALPHA, _alphaIds, msg.sender);
			_mixAndMatchAlpha();
		}
		if (_betaIds.length > 0) {
			_depositNfts(BETA, _betaIds, msg.sender);
			_mixAndMatchBeta();
		}
	}

	function depositDogsToBindToIds(uint256[] calldata _gammaIds, uint256[] calldata _matchIds) external {
		require(_gammaIds.length == _matchIds.length, "!len");
		if (_gammaIds.length > 0)
			_depositNfts(GAMMA, _gammaIds, msg.sender);
		_bindDoggoToMatchId(_gammaIds, _matchIds, msg.sender, address(0));
	}

	function depositDogTokenDepositToBindToIds(uint256 _depositCount, uint256[] calldata _matchIds) external {
		require(_depositCount == _matchIds.length, "ApeMatcher: deposit !len");
		require(_depositCount <= GAMMA.balanceOf(address(this)), "ApeMatcher: Not enough dogs");
		require(APE.transferFrom(msg.sender, address(this), _depositCount * GAMMA_SHARE), "ApeMatcher: APE token transfer reverted");
		uint256[] memory gammaIds = new uint256[](_depositCount);
		for (uint256 i = 0; i < _depositCount; i++)
			gammaIds[i] = GAMMA.tokenOfOwnerByIndex(address(this), i);
		_bindDoggoToMatchId(gammaIds, _matchIds, address(0), msg.sender);
		
	}

	function withdrawNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external {
		if (_gammaIds.length > 0)
			_withdrawNfts(GAMMA, _gammaIds, msg.sender);
		if (_alphaIds.length > 0)
			_withdrawNfts(ALPHA, _alphaIds, msg.sender);
		if (_betaIds.length > 0)
			_withdrawNfts(BETA, _betaIds, msg.sender);
	}

	function depositApeToken(uint256[] calldata _depositKeys) external notPaused {
		uint256 totalDeposit = 0;
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		for(uint256 i = 0; i < _depositKeys.length; i++) {
			totalDeposit += depositValues[_depositKeys[i]];
			_handleDeposit(_depositKeys[i], msg.sender);
			// TODO emit event somehow
		}
		require(APE.transferFrom(msg.sender, address(this), totalDeposit), "ApeMatcher: APE token transfer reverted");

		_mixAndMatchAlpha();
		_mixAndMatchBeta();
	}

	function withdrawApeToken(uint256[] calldata _depositKeys, uint256[] calldata _depositIndex) external {
		require(_depositKeys.length == _depositIndex.length, "ApeMatcher: !length");

		uint256 amountToReturn = 0;
		for (uint256 i = 0 ; i < _depositIndex.length; i++) {
			amountToReturn += _verifyAndReturnDepositValue(_depositKeys[i], _depositIndex[i], msg.sender);
		}
		APE.transfer(msg.sender, amountToReturn);
	}

	function claimTokens() external {
		uint256 rewards = payments[msg.sender];
		if (rewards > 0) {
			payments[msg.sender] = 0;
			APE.transfer(msg.sender, rewards);
		}
	}

	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds) external {
		for(uint256 i = 0 ; i < _matchIds.length; i++)
			claimRewardsFromMatch(_matchIds[i]);
	}

	function claimRewardsFromMatch(uint256 _matchId) public {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3]);

		bool claimGamma = msg.sender == adds[2] || msg.sender == adds[3];
		uint256 ids = _match.ids;
		uint256 total = smoothOperator.claim(
			_match.primary == 1 ? address(ALPHA) : address(BETA),
			ids & 0xffffffffffff,
			ids >> 48,
			claimGamma);
		_processRewards(total, adds, msg.sender, claimGamma);
	}

	function batchBreakMatch(uint256[] calldata _matchIds) external {
		for (uint256 i = 0; i < _matchIds.length; i++) 
			breakMatch(_matchIds[i]);
	}

	function breakMatch(uint256 _matchId) public {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3]);
		require (block.timestamp - _match.start > MIN_STAKING_PERIOD, "Must wait min duration to break clause");
		
		uint256 tokenId = _match.ids;
		matches[_matchId].active = false;
		delete assetToUser[_match.primary == 1 ? address(ALPHA) : address(BETA)][tokenId & 0xffffffffffff];
		if (tokenId >> 48 > 0)
			delete assetToUser[address(GAMMA)][tokenId >> 48];
		// ensures all participants receive back their shares
		(uint256 total, uint256 totalGamma) = smoothOperator.uncommitNFTs(_match);
		delete matches[_matchId];
		_processRewards(total, adds, msg.sender, false);
		if (totalGamma > 0)
			_processRewards(totalGamma, adds, msg.sender, true);
	}

	function batchBreakDogMatch(uint256[] calldata _matchIds) external {
		for (uint256 i = 0; i < _matchIds.length; i++)
			breakDogMatch(_matchIds[i]);
	}

	function breakDogMatch(uint256 _matchId) public {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[2] || msg.sender == adds[3]);

		uint256 totalGamma = _unbindDoggoFromMatchId(_matchId);
		_processRewards(totalGamma, adds, msg.sender, true);
	}

	function smartBreakMatch(uint256 _matchId) external {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3]);
		
		uint256 index = 0;
		for (; index < 4; index++)
			if (msg.sender == adds[index])
				break;
		uint256 ids = _match.ids;
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		(uint256 totalPrimary, uint256 totalGamma) = _smartSwap(index, ids, primary, _matchId, msg.sender);
		if (totalPrimary > 0)
				_processRewards(totalPrimary, adds, msg.sender, false);
		if (totalGamma > 0)
			_processRewards(totalGamma, adds, msg.sender, true);
	}

	function _smartSwap(
		uint256 _index,
		uint256 _ids,
		address _primary,
		uint256 _matchId,
		address _user) internal returns (uint256 totalPrimary, uint256 totalGamma) {
		// swap primary nft out
		if (_index == 0) {
			if (IERC721Enumerable(_primary).balanceOf(address(this)) > 0) {
				uint256 id = IERC721Enumerable(_primary).tokenOfOwnerByIndex(address(this), 0);
				uint256 oldId = _ids & 0xffffffffffff;
				matches[_matchId].ids = uint96(((_ids >> 48) << 48) | id); // swap primary ids
				matches[_matchId].primaryOwner = assetToUser[_primary][id]; // swap primary owner
				delete assetToUser[_primary][oldId];
				(totalPrimary, totalGamma) = smoothOperator.swapPrimaryNft(_primary, id, oldId, _user, _ids >> 48);
			}
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		else if (_index == 1) {
			if (_primary == address(ALPHA)) {
				if (alphaDepositCounter - alphaSpentCounter > 0)
					matches[_matchId].primaryTokensOwner = shareDeposits[ALPHA_SHARE][alphaSpentCounter++]; // swap primary token owner
					APE.transfer(_user, ALPHA_SHARE);
					totalPrimary =  smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, false);
			}
			else {
				if (betaDepositCounter - betaSpentCounter > 0)
					matches[_matchId].primaryTokensOwner = shareDeposits[BETA_SHARE][betaSpentCounter++]; // swap primary token owner
					APE.transfer(_user, BETA_SHARE);
					totalPrimary =  smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, false);
			}
		}
		// swap doggo out
		else if (_index == 2) {
			if (GAMMA.balanceOf(address(this)) > 0) {
				uint256 id = GAMMA.tokenOfOwnerByIndex(address(this), 0);
				uint256 oldId = _ids >> 48;
				matches[_matchId].ids = uint96((_ids & 0xffffffffffff) | id); // swap gamma ids
				matches[_matchId].primaryOwner = assetToUser[address(GAMMA)][id]; // swap gamma owner
				delete assetToUser[address(GAMMA)][oldId];
				totalGamma = smoothOperator.swapDoggoNft(_primary, _ids & 0xffffffffffff,  id, oldId, _user);
			}
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		else if (_index == 3) {
			if (gammaDepositCounter - gammaSpentCounter > 0)
				matches[_matchId].doggoTokensOwner = shareDeposits[GAMMA_SHARE][gammaSpentCounter++]; // swap gamma token owner
				APE.transfer(_user, GAMMA_SHARE);
				totalGamma =  smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, true);
		}
	}

	function _processRewards( uint256 _total, address[4] memory _adds, address _user, bool _claimGamma) internal {
		uint256 index = 0;
		for (; index < 4; index++)
			if (_user == _adds[index])
				break;
		uint128[4] memory splits = _smartSplit(uint128(_total), _adds, _claimGamma);
		_total = splits[index] + payments[_user];
		payments[_user] = 0;
		splits[index] = 0;
		for (uint256 i = 0 ; i < 4; i++)
			if (splits[i] > 0)
				payments[_adds[i]] += splits[i];
		fee += _total * FEE / DENOMINATOR;
		if (_total > 0)
			APE.transfer(_user, _total - _total * FEE / DENOMINATOR);
	}

	function _smartSplit(uint128 _total, address[4] memory _adds, bool _claimGamma) internal pure returns(uint128[4] memory splits) {
		uint256 i = 0;
		splits = _getWeights(_claimGamma);
		uint128 sum  = 0;
		// make sum and remove weight if address is null
		for (i = 0 ; i < 4 ; i++)
			sum += _adds[i] != address(0) ? splits[i] : 0;
		// update splits
		for (i = 0 ; i < 4 ; i++)
			splits[i] = _adds[i] != address(0) ? ( _total * splits[i] / sum) : 0;

		// if dog owner or dog token deposit owner is primary owner, bring together (saves gas for sstore and transfers)
		if (_adds[0] == _adds[2]) {
			splits[0] += splits[2];
			splits[2] = 0;
		}
		if (_adds[0] == _adds[3]) {
			splits[0] += splits[3];
			splits[3] = 0;
		}
		// if dog owner or dog token deposit owner is primary token deposit owner, bing together (saves gas for sstore and transfers)
		if (_adds[1] == _adds[2]) {
			splits[1] += splits[2];
			splits[2] = 0;
		}
		if (_adds[1] == _adds[3]) {
			splits[1] += splits[3];
			splits[3] = 0;
		}
	}

	function _mixAndMatchAlpha() internal {
		uint256 count = ALPHA.balanceOf(address(this));
		uint256 deposits = alphaDepositCounter - alphaSpentCounter;
		uint256 countGamma = GAMMA.balanceOf(address(this)); // number of dogs in contract | eg : 2 dogs
		uint256 depositsGamma = gammaDepositCounter - gammaSpentCounter; // number of token deposits in contract | eg : 30 deposits => 30 * 856 tokens
		uint256 matchCount = _min(count, deposits);
		uint256 gammaCount = _min(countGamma, depositsGamma);

		for (uint256 i = 0; i < matchCount ; i++) {
			uint256 gammaId = 0;
			uint256 id = ALPHA.tokenOfOwnerByIndex(address(this), 0);
			bool gammaMatch = i < gammaCount;
			if (gammaMatch)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			matches[matchCount++] = GreatMatch(
				true,
				uint8(1),
				uint32(block.timestamp),
				uint96(gammaId << 48 + id),
				assetToUser[address(ALPHA)][id], // should we delete asset to user for gas saving?
				shareDeposits[ALPHA_SHARE][alphaSpentCounter++], // should we delete asset to user for gas saving?
				gammaMatch ? assetToUser[address(GAMMA)][gammaId] : address(0), // should we delete asset to user for gas saving?
				gammaMatch ? shareDeposits[GAMMA_SHARE][gammaSpentCounter++] : address(0) // should we delete asset to user for gas saving?
			);
			ALPHA.transferFrom(address(this), address(smoothOperator), id);
			if (gammaMatch)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			// TODO check if enough ape or need to unstake (if even a thing)
			APE.transfer(address(smoothOperator), ALPHA_SHARE + (gammaMatch ? GAMMA_SHARE : 0));
			// TODO call smooth operator to take/commit nfts and tokens
			smoothOperator.commitNFTs(address(ALPHA), id, gammaId);
		}
	}

	function _mixAndMatchBeta() internal {
		uint256 count = BETA.balanceOf(address(this));
		uint256 deposits = betaDepositCounter - betaSpentCounter;
		uint256 countGamma = GAMMA.balanceOf(address(this));
		uint256 depositsGamma = gammaDepositCounter - gammaSpentCounter;
		uint256 matchCount = _min(count, deposits);

		for (uint256 i = 0; i < matchCount ; i++) {
			uint256 gammaId = 0;
			uint256 id = BETA.tokenOfOwnerByIndex(address(this), 0);
			bool gammaMatch = i < _min(countGamma, depositsGamma);
			if (gammaMatch)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			matches[matchCount++] = GreatMatch(
				true,
				uint8(2),
				uint32(block.timestamp),
				uint96(gammaId << 48 + id),
				assetToUser[address(BETA)][id], // should we delete asset to user for gas saving?
				shareDeposits[BETA_SHARE][betaSpentCounter++], // should we delete asset to user for gas saving?
				gammaMatch ? assetToUser[address(GAMMA)][gammaId] : address(0), // should we delete asset to user for gas saving?
				gammaMatch ? shareDeposits[GAMMA_SHARE][gammaSpentCounter++]: address(0) // should we delete asset to user for gas saving?
			);
			BETA.transferFrom(address(this), address(smoothOperator), id);
			if (gammaMatch)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			APE.transfer(address(smoothOperator), BETA_SHARE + (gammaMatch ? GAMMA_SHARE : 0));
			smoothOperator.commitNFTs(address(BETA), id, gammaId);
		}
	}

	function _bindDoggoToMatchId(uint256[] memory _gammaIds, uint256[] calldata _matchIds, address _nftOwner, address _depositor) internal {
		uint256 countGamma = _gammaIds.length;
		uint256 depositsGamma = gammaDepositCounter - gammaSpentCounter;
		require (countGamma == depositsGamma, "Insufficient token deposits");
		for (uint256 i = 0; i < _matchIds.length; i++) {
			GreatMatch storage _match = matches[_matchIds[i]];
			require (_match.doggoOwner == address(0), "ApeMatcher: match filled");
			uint256 gammaId = _gammaIds[i];
			address actualDepositor;
			address actualNftOwner = _nftOwner != address(0) ? _nftOwner : assetToUser[address(GAMMA)][gammaId];
			if (_depositor != address(0))
				actualDepositor =_depositor;
			else
				actualDepositor = shareDeposits[GAMMA_SHARE][gammaSpentCounter++];
			_match.doggoOwner = actualNftOwner;
			_match.doggoTokensOwner = actualDepositor;
			GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			APE.transfer(address(smoothOperator), GAMMA_SHARE);
			address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
			smoothOperator.bindDoggoToExistingPrimary(primary, _match.ids & 0xffffffffffff, gammaId);
		}
	}



	function _unbindDoggoFromMatchId(uint256 _matchId) internal returns(uint256 totalGamma) {
		GreatMatch storage _match = matches[_matchId];
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		uint256 ids = _match.ids;
		totalGamma = smoothOperator.unbindDoggoFromExistingPrimary(
			primary,
			ids & 0xffffffffffff,
			ids >> 48,
			_match.doggoOwner,
			_match.doggoTokensOwner);
		delete _match.doggoOwner;
		delete _match.doggoTokensOwner;
		_match.ids = uint96(ids & 0xffffffffffff);
	}

	function _handleDeposit(uint256 _type, address _user) internal {
		if (_type == 0)
			shareDeposits[ALPHA_SHARE][alphaDepositCounter++] = _user;
		else if (_type == 1)
			shareDeposits[BETA_SHARE][betaDepositCounter++] = _user;
		else if (_type == 2)
			shareDeposits[GAMMA_SHARE][gammaDepositCounter++] = _user;
	}

	function _verifyAndReturnDepositValue(uint256 _type, uint256 _index, address _user) internal returns (uint256){
		if (_type == 0) {
			require(shareDeposits[ALPHA_SHARE][_index] == _user, "ApeMatcher: Not owner of deposit");
			require(alphaSpentCounter <= _index, "ApeMatcher: deposit consumed"); 
			require(alphaDepositCounter > _index, "ApeMatcher: deposit !exist");  

			shareDeposits[ALPHA_SHARE][_index] = shareDeposits[ALPHA_SHARE][alphaDepositCounter - 1];
			delete shareDeposits[ALPHA_SHARE][alphaDepositCounter - 1];
			return ALPHA_SHARE;
		}
		else if (_type == 1) {
			require(shareDeposits[BETA_SHARE][_index] == _user, "ApeMatcher: Not owner of deposit");
			require(betaSpentCounter <= _index, "ApeMatcher: deposit consumed");
			require(betaDepositCounter > _index, "ApeMatcher: deposit !exist");

			shareDeposits[BETA_SHARE][_index] = shareDeposits[BETA_SHARE][betaDepositCounter - 1];
			delete shareDeposits[BETA_SHARE][betaDepositCounter - 1];
			return BETA_SHARE;
		}
		else if (_type == 2) {
			require(shareDeposits[GAMMA_SHARE][_index] == _user, "ApeMatcher: Not owner of deposit");
			require(gammaSpentCounter <= _index, "ApeMatcher: deposit consumed");
			require(gammaDepositCounter > _index, "ApeMatcher: deposit !exist");

			shareDeposits[GAMMA_SHARE][_index] = shareDeposits[GAMMA_SHARE][gammaDepositCounter - 1];
			delete shareDeposits[GAMMA_SHARE][gammaDepositCounter - 1];
			return GAMMA_SHARE;
		}
		else 
			revert("ApeMatcher: Outside keys");
	}

	function _depositNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
		uint256 poolId = _nft == ALPHA ? 1 : (_nft == BETA ? 2 : 3);
		for(uint256 i = 0; i < _tokenIds.length; i++) {
			IApeStaking.Position memory pos = APE_STAKING.nftPosition(poolId, _tokenIds[i]);
			require (pos.stakedAmount > 0, "ApeMatcher: NFT already commited");
			assetToUser[address(_nft)][_tokenIds[i]] = _user;
			_nft.transferFrom(_user, address(this), _tokenIds[i]);
		}
	}

	function _withdrawNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
			for (uint256 i = 0; i < _tokenIds.length; i++) {
			require(assetToUser[address(_nft)][_tokenIds[i]] == _user, "!owner");
			delete assetToUser[address(_nft)][_tokenIds[i]];
			_nft.transferFrom(address(this), _user, _tokenIds[i]);
		}
	}

	function _min(uint256 _a, uint256 _b) internal pure returns (uint256) {
		return _a > _b ? _b : _a;
	}

	function _getWeights(bool _claimGamma) internal pure returns(uint128[4] memory weights) {
		// TODO check if we fetch price feed from bend dao and have a dynamic weight or do static
		// NOTE historically looks like nfts are 2x more valuable than token req
		if (_claimGamma) {
			weights[0] = 67;  // 6.7%
			weights[1] = 33;  // 3.3%
			weights[2] = 600; // 60%
			weights[3] = 300; // 30%
		}
		else {
			weights[0] = 1000; // 66.66%
			weights[1] = 500;  // 33.33%
			weights[2] = 0;
			weights[3] = 0;
		}
	}
}