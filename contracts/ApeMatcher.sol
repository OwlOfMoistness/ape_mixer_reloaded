//SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./Pausable.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeCompounder.sol";

contract ApeMatcher is Pausable, IApeMatcher {

	uint256 constant public FEE = 40; // 4%
	uint256 constant public DENOMINATOR = 1000;

	// IApeStaking public immutable APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	// IERC721Enumerable public immutable ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	// IERC721Enumerable public immutable BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	// IERC721Enumerable public immutable GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	// IERC20 public immutable APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	IApeStaking immutable APE_STAKING;
	IERC721Enumerable immutable ALPHA;
	IERC721Enumerable immutable BETA;
	IERC721Enumerable immutable GAMMA;
	IERC20 immutable APE;

	uint256 constant ALPHA_SHARE = 10094 ether; //bayc
	uint256 constant BETA_SHARE = 2042 ether; // mayc
	uint256 constant GAMMA_SHARE = 856 ether; // dog

	uint256 public fee;
	uint256 public weights;
	mapping(address => mapping(uint256 => address)) public assetToUser;

	uint256 public matchCounter;
	uint256 public doglessMatchCounter;

	mapping(uint256 => GreatMatch) public matches;
	mapping(uint256 => uint256) public doglessMatches;
	mapping(address => uint256) public payments;

	ISmoothOperator public smoothOperator;
	IApeCompounder public vault;

	constructor(address a,address b,address c,address d,address e) {
		ALPHA = IERC721Enumerable(a);
		BETA = IERC721Enumerable(b);
		GAMMA = IERC721Enumerable(c);
		APE = IERC20(d);
		APE_STAKING = IApeStaking(e);
	}

	modifier onlyOperator() {
		require(msg.sender == address(smoothOperator), "!sm");
		_;
	}

	/**  
	 * @notice
	 * Set the contract to handle NFTs and Ape coins. Can be called only once. Owner gated
	 * @param _operator contract address of the operator
	 * @param _vault contract address of the vault
	 */
	function init(address _operator, address _vault) external onlyOwner {
		require(address(smoothOperator) == address(0) && address(vault) == address(0));
		smoothOperator = ISmoothOperator(_operator);
		vault = IApeCompounder(_vault);
		APE.approve(_vault, type(uint256).max);
	}

	/**  
	 * @notice
	 * Updates the weights that dictates how rewards are split. Owner gated
	 * @param _alphaWeights Array containing the weights for alpha splits
	 * @param _betaWeights Array containing the weights for beta splits
	 * @param _gammaWeights Array containing the weights for secondary splits
	 */
	function updateWeights(uint16[4] calldata _alphaWeights, uint16[4] calldata _betaWeights, uint16[4] calldata _gammaWeights) external onlyOwner {
		require(_alphaWeights[0] + _alphaWeights[1] + _alphaWeights[2] + _alphaWeights[3] == 1000);
		require(_betaWeights[0] + _betaWeights[1] + _betaWeights[2] + _betaWeights[3] == 1000);

		require(_alphaWeights[2] + _alphaWeights[3] == 0);
		require(_betaWeights[2] + _betaWeights[3] == 0);
		require(_gammaWeights[0] + _gammaWeights[1] + _gammaWeights[2] + _gammaWeights[3] == 1000);

		uint256 val;
		// using 192 bits: 3 sections of 64 bits each. Each section subdivided in 4 sections of 16
		for (uint256 i = 0; i < 4 ; i++)
			val |= (uint256(_alphaWeights[i]) << (16 * (11 - i))) + (uint256(_betaWeights[i]) << (16 * (7 - i))) + (uint256(_gammaWeights[i]) << (16 * (3 - i)));
		weights = val;
	}

	/**  
	 * @notice
	 * Allows owner to fetch ape coin fees. Owner gated
	 */
	function fetchApe() external onlyOwner {
		uint256 amount = fee;
		fee = 0;
		APE.transferFrom(address(smoothOperator), owner(), amount);
	}

	/**  
	 * @notice
	 * Allows a user to deposit NFTs into the contract
	 * @param _alphaIds Array of BAYC nfts to deposit
	 * @param _betaIds Array of MAYC nfts to deposit
	 * @param _gammaIds Array of BAKC nfts to deposit
	 */
	function depositNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external notPaused {
			_depositNfts(GAMMA, _gammaIds, msg.sender);
			_depositNfts(ALPHA, _alphaIds, msg.sender);
			_depositNfts(BETA, _betaIds, msg.sender);
		_mixExec();
	}

	/**  
	 * @notice
	 * Allows a user to deposit NFTs into the contract
	 * @param _alphaIds Array of BAYC nfts to deposit
	 * @param _betaIds Array of MAYC nfts to deposit
	 */
	function matchNftsSelf(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds) external notPaused {
			APE.transferFrom(msg.sender, address(smoothOperator),
				_alphaIds.length * ALPHA_SHARE  + _betaIds.length * BETA_SHARE);
			_matchSelf(ALPHA, _alphaIds, 1, msg.sender);
			_matchSelf(BETA, _betaIds, 0, msg.sender);
	}

	/**  
	 * @notice
	 * Allows a user withdraw their NFTs that aren't matched
	 * @param _alphaIds Array of BAYC nfts to withdraw
	 * @param _betaIds Array of MAYC nfts to withdraw
	 * @param _gammaIds Array of BAKC nfts to withdraw
	 */
	function withdrawNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external {
			_withdrawNfts(GAMMA, _gammaIds, msg.sender);
			_withdrawNfts(ALPHA, _alphaIds, msg.sender);
			_withdrawNfts(BETA, _betaIds, msg.sender);
	}

	/**  
	 * @notice
	 * Allows a user to claim rewards from an array of matches they are involved with
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _claim Boolean to set if the users withdraws rewards now or not
	 */
	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds, uint256 _claim) external {
		uint256 _fee;
		for (uint256 i = 0 ; i < _matchIds.length; i++)
			_fee += _claimRewardsFromMatch(_matchIds[i]);
		_handleFeeAndReturn(_fee, address(0), 0);
		if (_claim == 1)
			_claimTokens(msg.sender);
		else if (_claim > 1) {
			uint256 totalApe = _claimTokensForMatcher(msg.sender);
			vault.permissionnedDepositFor(totalApe, msg.sender);
		}
	}

	/**  
	 * @notice
	 * Allows a user to break matches they are involved with to recuperate their asset(s)
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _breakAll Array of booleans indicating to break the whole match or just the dog agreement
	 */
	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external {
		uint256 _fee;
		uint256 _doglessMatchCounter = doglessMatchCounter;
		uint256 toReturn;
		uint256 toReturnToVault;
		for (uint256 i = 0; i < _matchIds.length; i++) {
			(uint256 newFee, uint256 doglessOutcome, uint256 _toReturn, uint256 _toVault) = _breakMatch(_matchIds[i], _breakAll[i], _doglessMatchCounter);
			_doglessMatchCounter = doglessOutcome;
			_fee += newFee;
			toReturn += _toReturn;
			toReturnToVault += _toVault;
		}
		doglessMatchCounter = _doglessMatchCounter;
		_handleFeeAndReturn(_fee, msg.sender, toReturn);
		_handleFeeAndReturn(0, address(vault), toReturnToVault);
	}

	/**  
	 * @notice
	 * Allows a user to swap their asset in a match with another one that currently exists in the contract
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _swapSetup Array of boolean indicating what the user wants swap in the match
	 */
	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[3][] memory _swapSetup) external {
		uint256 _totalFee;
		uint256 toReturnToUser;
		for (uint256 i = 0; i < _matchIds.length; i++) {
			(uint256 realisedFee, uint256 _toReturnToUser) = _smartBreakMatch(_matchIds[i], toReturnToUser, _swapSetup[i]);
			_totalFee += realisedFee;
			toReturnToUser += _toReturnToUser;
		}
		_handleFeeAndReturn(_totalFee, address(0), 0);
		if (toReturnToUser > 0)
			vault.borrowAndWithdrawExactFor(toReturnToUser, msg.sender);
	}

	// INTERNAL

	/**  
	 * @notice
	 * Internal function that claims tokens for a user
	 * @param _user User to send rewards to
	 */
	function _claimTokens(address _user) internal {
		uint256 rewards = payments[_user];
		if (rewards > 0) {
			payments[_user] = 0;
			APE.transferFrom(address(smoothOperator) ,_user, rewards);
		}
	}

	/**  
	 * @notice
	 * Internal function that claims tokens for a user
	 * @param _user User to send rewards to
	 */
	function _claimTokensForMatcher(address _user) internal returns (uint256 rewards) {
		rewards = payments[_user];
		if (rewards > 0) {
			payments[_user] = 0;
			APE.transferFrom(address(smoothOperator), address(this), rewards);
		}
	}

	/**  
	 * @notice
	 * Interncl function that claims tokens from a match
	 * @param _matchId Match ID to claim from
	 */
	function _claimRewardsFromMatch(uint256 _matchId) internal returns(uint256 _fee) {
		(GreatMatch memory _match, address[4] memory adds) = _checkMatch(_matchId);

		bool claimGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool claimPrimary = msg.sender == adds[0] || msg.sender == adds[1];
		address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
		uint256 ids = _match.ids;
		(uint256 totalPrimary, uint256 totalGamma) = smoothOperator.claim(primary, ids & 0xffffffffffff, ids >> 48,
			claimGamma && claimPrimary ? 2 : (claimGamma ? 0 : 1));
		_fee += _handleRewards(totalPrimary, totalGamma, adds, primary == address(ALPHA));	
	}

	/**  
	 * @notice
	 * Internal function that claims tokens from a match
	 * @param _matchId Match ID to claim from
	 * @param _swapSetup Boolean array indicating what the user wants swap in the match
	 */
	function _smartBreakMatch(uint256 _matchId, uint256 _borrowed, bool[3] memory _swapSetup) internal returns(uint256 _fee, uint256 toReturnToUser) {
		(GreatMatch memory _match, address[4] memory adds) = _checkMatch(_matchId);
		
		for (uint256 i; i < 3; i++)
			_swapSetup[i] = _swapSetup[i] && msg.sender == adds[i];
		uint256 ids = _match.ids;
		address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
		uint256 totalPrimary;
		uint256 totalGamma;
		(totalPrimary, totalGamma, toReturnToUser) = _smartSwap(_swapSetup, ids, primary, _matchId, _borrowed, msg.sender);
		_fee += _handleRewards(totalPrimary, totalGamma, adds, primary == address(ALPHA));	
	}

	/**  
	 * @notice
	 * Internal function that handles swapping an asset of a match with another in the contract
	 * @param _swapSetup Boolean array indicating what the user wants swap in the match
	 * @param _ids Ids of primary asset and dog 
	 * @param _primary Contract address of the primary asset
	 * @param _matchId Match ID to execurte the swap
	 * @param _user User to swap out
	 */
	function _smartSwap(
		bool[3] memory _swapSetup,
		uint256 _ids,
		address _primary,
		uint256 _matchId,
		uint256 _borrowed,
		address _user) internal returns (uint256 totalPrimary, uint256 totalGamma, uint256 toReturnToUser) {
		// swap doggo out
		if (_swapSetup[2]) {
			require(GAMMA.balanceOf(address(this)) > 0, "!dog");
			uint256 id = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			matches[_matchId].ids = uint96((_ids & 0xffffffffffff) | (id << 48)); // swap gamma ids
			matches[_matchId].doggoOwner = assetToUser[address(GAMMA)][id]; // swap gamma owner
			delete assetToUser[address(GAMMA)][_ids >> 48];
			GAMMA.transferFrom(address(this), address(smoothOperator), id);
			totalGamma = smoothOperator.swapDoggoNft(_primary, _ids & 0xffffffffffff,  id, _ids >> 48, _user);
			_ids = (_ids & 0xffffffffffff) | (id << 48);
		}
		// swap primary nft out
		if (_swapSetup[0]) {
			require(IERC721Enumerable(_primary).balanceOf(address(this)) > 0, "!prim");
			uint256 id = IERC721Enumerable(_primary).tokenOfOwnerByIndex(address(this), 0);
			matches[_matchId].ids = uint96(((_ids >> 48) << 48) | id); // swap primary ids
			matches[_matchId].primaryOwner = assetToUser[_primary][id]; // swap primary owner
			delete assetToUser[_primary][_ids & 0xffffffffffff];
			IERC721Enumerable(_primary).transferFrom(address(this), address(smoothOperator), id);
			(totalPrimary, totalGamma) = smoothOperator.swapPrimaryNft(_primary, id, _ids & 0xffffffffffff, _user, _ids >> 48);
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		if (_swapSetup[1]) {
			require (matches[_matchId].self, "!self");
			uint256 liquid = vault.liquid() - _borrowed;
			uint256 share = _primary == address(ALPHA) ? ALPHA_SHARE : BETA_SHARE;
			if (liquid > 0) liquid--;
			require(liquid >= share, "prim share");

			matches[_matchId].self = false;
			toReturnToUser = share;
			(totalPrimary,) = smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, 1);
		}
	}

	/**  
	 * @notice
	 * Internal function that breaks a match
	 * @param _matchId Match ID to break
	 * @param _breakAll Boolean indicating if we break the whole match or just the dogs
	 */
	function _breakMatch(uint256 _matchId, bool _breakAll, uint256 _doglessMatchCounter) internal 
		returns(
			uint256 _fee,
			uint256 doglessOutcome,
			uint256 toReturn,
			uint256 toReturnToVault){
		(GreatMatch memory _match, address[4] memory adds) = _checkMatch(_matchId);
		bool breakGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool primaryOwner = msg.sender == adds[0] || msg.sender == adds[1];
		doglessOutcome = _doglessMatchCounter;

		_breakAll = primaryOwner ? _breakAll : false;
		if(breakGamma && !_breakAll) {
			uint256 realisedFee;
			(realisedFee, toReturnToVault) = _breakDogMatch(_matchId, _doglessMatchCounter, adds);
			_fee += realisedFee;
			doglessOutcome++;
		}
		else {
			uint256 tokenId = _match.ids;
			uint256 totalPrimary;
			uint256 totalGamma;
			(totalPrimary, totalGamma, toReturn, toReturnToVault) = smoothOperator.uncommitNFTs(_match, msg.sender);
			if (msg.sender == adds[0])
				delete assetToUser[_match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA)][tokenId & 0xffffffffffff];
			if (msg.sender == adds[2] && tokenId >> 48 > 0)
				delete assetToUser[address(GAMMA)][tokenId >> 48];
			if (adds[2] == address(0)) {
				doglessOutcome--;
				doglessMatches[_match.doglessIndex >> 1] = doglessMatches[doglessMatchCounter - 1];
				delete doglessMatches[doglessMatchCounter - 1];
			}
			delete matches[_matchId];
			_fee += _handleRewards(totalPrimary, totalGamma, adds, _match.doglessIndex & 1 == 1);	
		}
	}

	/**  
	 * @notice
	 * Internal function that breaks the dog agreement in a match
	 * @param _matchId Match ID to break
	 */
	function _breakDogMatch(uint256 _matchId, uint256 _doglessMatchCounter, address[4] memory _adds) internal returns(uint256, uint256){
		(uint256 totalGamma, uint256 toReturnToVault) = _unbindDoggoFromMatchId(_matchId, msg.sender, _doglessMatchCounter);
		return (_processRewards(totalGamma, _adds, msg.sender, 0), toReturnToVault);
	}

	function _handleRewards(uint256 _totalPrimary, uint256 _totalGamma, address[4] memory _adds, bool alpha) internal returns(uint256 _fee) {
		if (_totalPrimary > 0)
			_fee += _processRewards(_totalPrimary, _adds, msg.sender, alpha ? 2 : 1);
		if (_totalGamma > 0)
			_fee += _processRewards(_totalGamma, _adds, msg.sender, 0);
	}

	/**  
	 * @notice
	 * Internal function that handles the payment from a match to the users involved
	 * @param _total Amount of tokens to distribute to users
	 * @param _adds Array of users involved
	 * @param _user Initial caller of the execution
	 * @param _offset Offset to right bit shift to get weights (BAYC = 2 | MAYC = 1 | BAKC = 0)
	 */
	function _processRewards(uint256 _total, address[4] memory _adds, address _user, uint256 _offset) internal returns(uint256 _fee){
		uint128[4] memory splits = _smartSplit(uint128(_total), _adds, _offset, weights);
		for (uint256 i = 0 ; i < 4; i++)
			if (splits[i] > 0) {
				// If you own both primary nft and deposit token, no fee charged
				if ((i == 0 || i == 1) && _user == _adds[0] && _user == _adds[1] && _offset > 0)
					payments[_adds[i]] += splits[i];
				else {
					_fee += splits[i] * FEE / DENOMINATOR;
					payments[_adds[i]] += splits[i] - (splits[i] * FEE / DENOMINATOR);
				}
			}
	}

	/**  
	 * @notice
	 * Internal function that handles the payment split of a given reward
	 * @param _total Amount of tokens to distribute to users
	 * @param _adds Array of users involved
	 * @param _offset Offset to right bit shift to get weights (BAYC = 2 | MAYC = 1 | BAKC = 0)
	 * @param _weight Value holding the split ratios of primary and dog claims
	 */
	function _smartSplit(uint128 _total, address[4] memory _adds, uint256 _offset, uint256 _weight) internal pure returns(uint128[4] memory splits) {
		uint256 i = 0;
		splits = _getWeights(_offset, _weight);
		uint128 sum  = splits[0] + splits[1] + splits[2] + splits[3];

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

	/**
	 * @notice
	 * Internal function that checks if borrowing from compounder is possible
	 * @param _nft Asset we are dealing with
	 */
	function mixCount(IERC721Enumerable _nft) internal returns(uint256, uint256) {
		uint256 balNft = _nft.balanceOf(address(this));
		uint256 gammaShare = GAMMA_SHARE;
		if (balNft == 0)
			return (0,0);
		uint256 _doglessCount = doglessMatchCounter;
		uint256 liquid = vault.liquid();
		if (liquid > 0) liquid--;
		if (_nft == GAMMA) {
			uint256 available = _min(liquid / gammaShare, _min(balNft, _doglessCount));
			if (available > 0)
				vault.borrow(available * gammaShare);
			return (available, 0);
		}
		else {
			uint256 share = _nft == ALPHA ? ALPHA_SHARE : BETA_SHARE;
			uint256 available = _min(liquid / share, balNft);
			uint256 dogBalance = GAMMA.balanceOf(address(this));
			uint256 dogAvailable = _min((liquid - available * share) / gammaShare, _min(dogBalance, balNft));
			if (available > 0)
				vault.borrow(available * share + dogAvailable * gammaShare);
			return (available, dogAvailable);
		}
	}

	/**
	 * @notice
	 * Internal function that matches user's nfts with user's ape coins
	 * @param _primary Contract address of the primary asser
	 * @param _tokenIds Array of token IDs
	 * @param _type primary asset type
	 * @param _user User to whom attribute the NFTs
	 */
	function _matchSelf(
		IERC721Enumerable _primary,
		uint256[] calldata _tokenIds,
		uint8 _type,
		address _user) internal {
		uint256 _matchCounter = matchCounter;
		uint256 _doglessCounter = doglessMatchCounter;

		for (uint256 i = 0; i < _tokenIds.length ; i++) {
			assetToUser[address(_primary)][_tokenIds[i]] == _user;
			doglessMatches[_doglessCounter] = _matchCounter;
			matches[_matchCounter++] = GreatMatch(
				true,
				uint96((_doglessCounter++ << 1) | _type),
				uint96(_tokenIds[i]),
				_user,
				address(0)
			);
			_primary.transferFrom(_user, address(smoothOperator), _tokenIds[i]);
			smoothOperator.commitNFTs(address(_primary), _tokenIds[i], 0);
		}
		doglessMatchCounter = _doglessCounter;
		matchCounter = _matchCounter;
	}

	/**  
	 * @notice
	 * Internal function that handles the pairing of primary assets with tokens if they exist
	 * @param _primary Contract address of the primary asset
	 * @param _type Type of primary asset
	 */
	function _mixAndMatch(
		IERC721Enumerable _primary,
		uint8 _type) internal {
		uint256 _matchCounter = matchCounter;
		MatchingParams memory p = MatchingParams(doglessMatchCounter,0,0, false);
		(p.toMatch, p.gammaCount) = mixCount(_primary);

		for (uint256 i = 0; i < p.toMatch ; i++) {
			uint256 gammaId = 0;
			uint256 id = _primary.tokenOfOwnerByIndex(address(this), 0);
			p.gamma = i < p.gammaCount;
			if (p.gamma)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			else
				doglessMatches[p.dogCounter++] = _matchCounter;
			matches[_matchCounter++] = GreatMatch(
				false,
				p.gamma ? _type : uint96(((p.dogCounter - 1) << 1) | _type),
				uint96((gammaId << 48) + id),
				assetToUser[address(_primary)][id],
				p.gamma ? assetToUser[address(GAMMA)][gammaId] : address(0)
			);
			_primary.transferFrom(address(this), address(smoothOperator), id);
			if (p.gamma)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			smoothOperator.commitNFTs(address(_primary), id, gammaId);
		}
		doglessMatchCounter = p.dogCounter;
		matchCounter = _matchCounter;
	}

	/**
	 * @notice
	 * Internal function that handles the pairing of DOG assets with tokens if they exist to an existing dogless match
	 */
	function _bindDoggoToMatchId() internal {
		(uint256 toBind,) = mixCount(GAMMA);
		if (toBind == 0) return;
		uint256 doglessIndex = doglessMatchCounter - 1;

		for (uint256 i = 0; i < toBind; i++) {
			GreatMatch storage _match = matches[doglessMatches[doglessIndex - i]];
			uint256 gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
			delete doglessMatches[doglessIndex - i];
			_match.ids |= uint96(gammaId << 48);
			_match.doggoOwner = assetToUser[address(GAMMA)][gammaId];
			_match.doglessIndex &= 1;
			GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			smoothOperator.bindDoggoToExistingPrimary(primary, _match.ids & 0xffffffffffff, gammaId);
		}
		doglessMatchCounter -= toBind;
	}

	/**
	 * @notice
	 * Internal function that handles matching Yuga assets with ape coins
	 */
	function _mixExec() internal {
		_mixAndMatch(ALPHA, 1);
		_mixAndMatch(BETA, 0);
		_bindDoggoToMatchId();
	}

	/**
	 * @notice
	 * Internal function that checks requirements of a match
	 * @param _matchId Match ID to check correct requirements
	 */
	function _checkMatch(uint256 _matchId) internal view returns(GreatMatch memory, address[4] memory) {
		GreatMatch memory _match = matches[_matchId];
		address[4] memory adds = [_match.primaryOwner,
								  _match.self ? _match.primaryOwner : address(vault),
								  _match.doggoOwner,
								  _match.doggoOwner != address(0) ? address(vault) : address(0)];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!mtch");
		return(_match, adds);
	}

	/**
	 * @notice
	 * Internal function that handles unbinding a dog from a match
	 * @param _matchId Match ID to remove the dog from
	 * @param _caller Initial caller of this execution
	 */
	function _unbindDoggoFromMatchId(uint256 _matchId, address _caller, uint256 _doglessMatchCounter) internal returns(uint256 totalGamma, uint256 toReturn) {
		GreatMatch storage _match = matches[_matchId];
		address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
		address dogOwner = _match.doggoOwner;
		uint256 ids = _match.ids;
		(totalGamma, toReturn) = smoothOperator.unbindDoggoFromExistingPrimary(
			primary,
			ids & 0xffffffffffff,
			ids >> 48,
			dogOwner,
			_caller);
		if (dogOwner == _caller)	
			delete assetToUser[address(GAMMA)][ids >> 48];
		_match.doggoOwner = address(0);
		_match.doglessIndex |= uint96(_doglessMatchCounter << 1);
		doglessMatches[_doglessMatchCounter] = _matchId;
		_match.ids = uint96(ids & 0xffffffffffff);
	}

	/**
	 * @notice
	 * Internal function that deposits NFTs for a user
	 * @param _nft Contract address of the nft
	 * @param _tokenIds Array of token IDs
	 * @param _user User to whom attribute the NFTs
	 */
	function _depositNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
		uint256 poolId = _nft == ALPHA ? 1 : (_nft == BETA ? 2 : 3);
		for (uint256 i = 0; i < _tokenIds.length; i++) {
			IApeStaking.Position memory pos = APE_STAKING.nftPosition(poolId, _tokenIds[i]);
			require (pos.stakedAmount == 0, "commtd");
			require(_nft.ownerOf(_tokenIds[i]) == _user, "!ownr");
			// EmperorTomatoKetchup, you can't use your #0
			if (poolId == 3 && _tokenIds[i] == 0) revert();
			assetToUser[address(_nft)][_tokenIds[i]] = _user;
			_nft.transferFrom(_user, address(this), _tokenIds[i]);
		}
	}

	/**
	 * @notice
	 * Internal function that withdraws NFTs for a user
	 * @param _nft Contract address of the nft
	 * @param _tokenIds Array of token IDs
	 * @param _user User to whom withdraw the NFTs
	 */
	function _withdrawNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
		for (uint256 i = 0; i < _tokenIds.length; i++) {
			require(assetToUser[address(_nft)][_tokenIds[i]] == _user, "!ownr");
			delete assetToUser[address(_nft)][_tokenIds[i]];
			_nft.transferFrom(address(this), _user, _tokenIds[i]);
		}
	}

	function _handleFeeAndReturn(uint256 _fee, address _user, uint256 _amountToReturn) internal {
		if (_fee > 0)
			fee += _fee;
		if (_amountToReturn > 0) {
			if (_user != address(vault)) {
				APE.transferFrom(address(smoothOperator), _user, _amountToReturn);
			}
			else {
				smoothOperator.repayDebt(address(vault), _amountToReturn);
				vault.repay(_amountToReturn);
			}
		}
	}

	function _min(uint256 _a, uint256 _b) internal pure returns (uint256) {
		return _a > _b ? _b : _a;
	}

	/**
	 * @notice
	 * Internal function that fetches the split ratio of a given claim (primary or dog)
	 * @param _offset Offset to right bit shift to get weights (BAYC = 2 | MAYC = 1 | BAKC = 0)
	 * @param _weight Value holding the split ratios
	 */
	function _getWeights(uint256 _offset, uint256 _weight) internal pure returns(uint128[4] memory _weights) {
		uint256 mask = 0xffffffffffffffff;
		uint256 _uint16Mask = 0xffff;

		_weight = (_weight >> (64 * _offset)) & mask;
		_weights[0] = uint128((_weight >> (16 * 3)) & _uint16Mask);
		_weights[1] = uint128((_weight >> (16 * 2)) & _uint16Mask);
		_weights[2] = uint128((_weight >> (16 * 1)) & _uint16Mask);
		_weights[3] = uint128((_weight >> (16 * 0)) & _uint16Mask);
	}
}