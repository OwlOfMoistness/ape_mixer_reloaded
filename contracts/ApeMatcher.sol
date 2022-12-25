pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./Pausable.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";

contract ApeMatcher is Pausable, IApeMatcher {

	uint256 constant public FEE = 40; // 4%
	uint256 constant public DENOMINATOR = 1000;

	// IApeStaking public immutable APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	// IERC721Enumerable public immutable ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	// IERC721Enumerable public immutable BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	// IERC721Enumerable public immutable GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	// IERC20 public immutable APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	IApeStaking public APE_STAKING;
	IERC721Enumerable public ALPHA;
	IERC721Enumerable public BETA;
	IERC721Enumerable public GAMMA;
	IERC20 public APE;

	uint256 constant ALPHA_SHARE = 10094 ether; //bayc
	uint256 constant BETA_SHARE = 2042 ether; // mayc
	uint256 constant GAMMA_SHARE = 856 ether; // dog

	uint256 public fee;
	uint256 public weights;
	mapping(address => mapping(uint256 => address)) public assetToUser;

	uint256 public matchCounter;
	uint256 public doglessMatchCounter;

	uint256 public alphaSpentCounter;
	uint256 public betaSpentCounter;
	uint256 public gammaSpentCounter;

	uint256 public alphaDepositCounter;
	uint256 public betaDepositCounter;
	uint256 public gammaDepositCounter;

	uint256 public alphaCurrentTotalDeposits;
	uint256 public betaCurrentTotalDeposits;
	uint256 public gammaCurrentTotalDeposits;
	mapping(uint256 => mapping(uint256 => DepositPosition)) public depositPosition;

	mapping(uint256 => GreatMatch) public matches;
	mapping(uint256 => uint256) public doglessMatches;
	mapping(address => uint256) public payments;

	ISmoothOperator public smoothOperator; // add interface to our smooth operator

	constructor(address a,address b,address c,address d,address e) {
		ALPHA = IERC721Enumerable(a);
		BETA = IERC721Enumerable(b);
		GAMMA = IERC721Enumerable(c);
		APE = IERC20(d);
		APE_STAKING = IApeStaking(e);
	}

	modifier onlyOperator() {
		require(msg.sender == address(smoothOperator), "!smooooth");
		_;
	}

	/**  
	 * @notice
	 * Set the contract to handle NFTs and Ape coins. Can be called only once. Owner gated
	 * @param _operator contract address of the operator
	 */
	function setOperator(address _operator) external onlyOwner {
		require(address(smoothOperator) == address(0));
		smoothOperator = ISmoothOperator(_operator);
	}

	/**  
	 * @notice
	 * Updates the weights that dictates how rewards are split. Owner gated
	 * @param _primaryWeights Array containing the weights for primary splits
	  * @param _dogWeights Array containing the weights for secondary splits
	 */
	function updateWeights(uint32[4] calldata _primaryWeights, uint32[4] calldata _dogWeights) external onlyOwner {
		require(_primaryWeights[0] + _primaryWeights[1] + _primaryWeights[2] + _primaryWeights[3] == 1000);
		require(_primaryWeights[2] + _primaryWeights[3] == 0);
		require(_dogWeights[0] + _dogWeights[1] + _dogWeights[2] + _dogWeights[3] == 1000);

		uint256 val;
		for(uint256 i = 0; i < 4 ; i++)
			val |= (uint256(_primaryWeights[i]) << (32 * (7 - i))) + (uint256(_dogWeights[i]) << (32 * (3 - i)));
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
		if (_gammaIds.length > 0)
			_depositNfts(GAMMA, _gammaIds, msg.sender);
		if (_alphaIds.length > 0) {
			_depositNfts(ALPHA, _alphaIds, msg.sender);
			_mixAndMatch(ALPHA, ALPHA_SHARE, alphaSpentCounter);
		}
		if (_betaIds.length > 0) {
			_depositNfts(BETA, _betaIds, msg.sender);
			_mixAndMatch(BETA, BETA_SHARE, betaSpentCounter);
		}
		_bindDoggoToMatchId();
	}

	/**  
	 * @notice
	 * Allows the operator to deposit the tokens of a user. Used when a match is broken
	 * @param _depositAmounts Array of amounts of deposits of each tranche to deposit
	 * @param _user User to deposit to
	 */
	function depositApeTokenForUser(uint32[3] calldata _depositAmounts, address _user) external override onlyOperator {
		uint256 totalDeposit = 0;
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		for(uint256 i = 0; i < 3; i++) {
			totalDeposit += depositValues[i] * uint256(_depositAmounts[i]);
			if (_depositAmounts[i] > 0)
				_handleDeposit(depositValues[i], _depositAmounts[i], _user);
			// TODO emit event somehow
		}
		_mixAndMatch(ALPHA, ALPHA_SHARE, alphaSpentCounter);
		_mixAndMatch(BETA, BETA_SHARE, betaSpentCounter);
		_bindDoggoToMatchId();
	}

	/**  
	 * @notice
	 * Allows a user to deposit ape coins into the contract
	 * @param _depositAmounts Array of amounts of deposits of each tranche to deposit
	 */
	function depositApeToken(uint32[3] calldata _depositAmounts) external notPaused {
		uint256 totalDeposit = 0;
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		for(uint256 i = 0; i < 3; i++) {
			totalDeposit += depositValues[i] * uint256(_depositAmounts[i]);
			if (_depositAmounts[i] > 0)
				_handleDeposit(depositValues[i], _depositAmounts[i], msg.sender);
			// TODO emit event somehow
		}
		if (totalDeposit > 0) {
			APE.transferFrom(msg.sender, address(smoothOperator), totalDeposit);
			_mixAndMatch(ALPHA, ALPHA_SHARE, alphaSpentCounter);
			_mixAndMatch(BETA, BETA_SHARE, betaSpentCounter);
			_bindDoggoToMatchId();
		}
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
		if (_gammaIds.length > 0)
			_withdrawNfts(GAMMA, _gammaIds, msg.sender);
		if (_alphaIds.length > 0)
			_withdrawNfts(ALPHA, _alphaIds, msg.sender);
		if (_betaIds.length > 0)
			_withdrawNfts(BETA, _betaIds, msg.sender);
	}

	/**  
	 * @notice
	 * Allows a user withdraw their ape coin deposits that haven't been consumed
	 * @param _depositAlpha Array of deposit IDs of the BAYC tranche
	 * @param _depositGamma Array of deposit IDs of the MAYC tranche
	 * @param _depositGamma Array of deposit IDs of the BAKC tranche
	 */
	function withdrawApeToken(
		DepositWithdrawals[] calldata _depositAlpha,
		DepositWithdrawals[] calldata _depositBeta,
		DepositWithdrawals[] calldata _depositGamma) external {
		uint256 amountToReturn = 0;
		for (uint256 i = 0 ; i < _depositAlpha.length; i++) {
			if (i < _depositAlpha.length - 1)
				require(_depositAlpha[i].depositId > _depositAlpha[i + 1].depositId);
			amountToReturn += _verifyAndReturnDepositValue(0, _depositAlpha[i].depositId, _depositAlpha[i].amount, msg.sender);
		}
		for (uint256 i = 0 ; i < _depositBeta.length; i++) {
			if (i < _depositBeta.length - 1)
				require(_depositBeta[i].depositId > _depositBeta[i + 1].depositId);
			amountToReturn += _verifyAndReturnDepositValue(1, _depositBeta[i].depositId, _depositBeta[i].amount, msg.sender);
		}
		for (uint256 i = 0 ; i < _depositGamma.length; i++) {
			if (i < _depositGamma.length - 1)
				require(_depositGamma[i].depositId > _depositGamma[i + 1].depositId);
			amountToReturn += _verifyAndReturnDepositValue(2, _depositGamma[i].depositId, _depositGamma[i].amount, msg.sender);
		}
		APE.transferFrom(address(smoothOperator), msg.sender, amountToReturn);
	}

	/**  
	 * @notice
	 * Allows a user to claim any outstanding amount of rewards
	 */
	function claimTokens() external {
		_claimTokens(msg.sender);
	}

	/**  
	 * @notice
	 * Allows a user to claim rewards from an array of matches they are involved with
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _claim Boolean to set if the users withdraws rewards now or not
	 */
	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds, bool _claim) external {
		uint256 _fee;
		for(uint256 i = 0 ; i < _matchIds.length; i++)
			_fee += _claimRewardsFromMatch(_matchIds[i]);
		_handleFee(_fee);
		if (_claim)
			_claimTokens(msg.sender);
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
		for (uint256 i = 0; i < _matchIds.length; i++) {
			(uint256 newFee, uint256 doglessOutcome) = _breakMatch(_matchIds[i], _breakAll[i], _doglessMatchCounter);
			if (doglessOutcome == 1)
				_doglessMatchCounter++;
			else if (doglessOutcome == 2)
				_doglessMatchCounter--;
			_fee += newFee;
		}
		doglessMatchCounter = _doglessMatchCounter;
		_handleFee(_fee);
	}

	/**  
	 * @notice
	 * Allows a user to break matches they are involved with to recuperate their asset(s).
	 * Only dogs and dog toke deposits can be removed
	 * @param _matchIds Array of match IDs a user is involved with 
	 */
	function batchBreakDogMatch(uint256[] calldata _matchIds) external {
		uint256 _fee;
		uint256 _doglessMatchCounter = doglessMatchCounter;
		for (uint256 i = 0; i < _matchIds.length; i++)
			_fee += _breakDogMatch(_matchIds[i], _doglessMatchCounter++);
		doglessMatchCounter = _doglessMatchCounter;
		_handleFee(_fee);
	}

	/**  
	 * @notice
	 * Allows a user to swap their asset in a match with another one that currently exists in the contract
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _swapSetup Array of boolean indicating what the user wants swap in the match
	 */
	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[4][] memory _swapSetup) external {
		uint256 _totalFee;
		uint256 toReturn;
		for (uint256 i = 0; i < _matchIds.length; i++) {
			uint256 _fee;
			(_fee, toReturn) = _smartBreakMatch(_matchIds[i], _swapSetup[i]);
			_totalFee += _fee;
		}
		APE.transferFrom(address(smoothOperator),msg.sender, toReturn);
		_handleFee(_totalFee);
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
	 * Interncl function that claims tokens from a match
	 * @param _matchId Match ID to claim from
	 */
	function _claimRewardsFromMatch(uint256 _matchId) internal returns(uint256 _fee) {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!match");

		bool claimGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool claimPrimary = msg.sender == adds[0] || msg.sender == adds[1];
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		uint256 ids = _match.ids;
		(uint256 total, uint256 totalGamma) = smoothOperator.claim(primary, ids & 0xffffffffffff, ids >> 48,
			claimGamma && claimPrimary ? 2 : (claimGamma ? 0 : 1));
		if (total > 0)
			_fee += _processRewards(total, adds, msg.sender, false);
		if (totalGamma > 0)
			_fee += _processRewards(totalGamma, adds, msg.sender, true);
	}

	/**  
	 * @notice
	 * Internal function that claims tokens from a match
	 * @param _matchId Match ID to claim from
	 * @param _swapSetup Boolean array indicating what the user wants swap in the match
	 */
	function _smartBreakMatch(uint256 _matchId, bool[4] memory _swapSetup) internal returns(uint256 _fee, uint256 toReturn) {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!match");
		
		for (uint256 i; i < 4; i++)
			_swapSetup[i] = _swapSetup[i] && msg.sender == adds[i];
		uint256 ids = _match.ids;
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		uint256 totalPrimary;
		uint256 totalGamma;
		(totalPrimary, totalGamma, toReturn) = _smartSwap(_swapSetup, ids, primary, _matchId, msg.sender);
		if (totalPrimary > 0)
			_fee += _processRewards(totalPrimary, adds, msg.sender, false);
		if (totalGamma > 0)
			_fee += _processRewards(totalGamma, adds, msg.sender, true);
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
		bool[4] memory _swapSetup,
		uint256 _ids,
		address _primary,
		uint256 _matchId,
		address _user) internal returns (uint256 totalPrimary, uint256 totalGamma, uint256 toReturn) {
		// swap primary nft out
		if (_swapSetup[0]) {
			require(IERC721Enumerable(_primary).balanceOf(address(this)) > 0, "ApeMatcher: !primary asset");
			uint256 id = IERC721Enumerable(_primary).tokenOfOwnerByIndex(address(this), 0);
			uint256 oldId = _ids & 0xffffffffffff;
			matches[_matchId].ids = uint96(((_ids >> 48) << 48) | id); // swap primary ids
			matches[_matchId].primaryOwner = assetToUser[_primary][id]; // swap primary owner
			delete assetToUser[_primary][oldId];
			IERC721Enumerable(_primary).transferFrom(address(this), address(smoothOperator), id);
			(totalPrimary, totalGamma) = smoothOperator.swapPrimaryNft(_primary, id, oldId, _user, _ids >> 48);
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		if (_swapSetup[1]) {
			if (_primary == address(ALPHA)) {
				require(alphaCurrentTotalDeposits > 0, "ApeMatcher: !alpha deposits");
				DepositPosition storage pos = depositPosition[ALPHA_SHARE][alphaSpentCounter]; 
				matches[_matchId].primaryTokensOwner = pos.depositor; // swap primary token owner
				if (pos.count == 1)
					delete depositPosition[ALPHA_SHARE][alphaSpentCounter++];
				else
					pos.count--;
				alphaCurrentTotalDeposits--;
			}
			else {
				require(betaCurrentTotalDeposits > 0, "ApeMatcher: !beta deposits");
				DepositPosition storage pos = depositPosition[BETA_SHARE][betaSpentCounter];
				matches[_matchId].primaryTokensOwner = pos.depositor; // swap primary token owner
				if (pos.count == 1)
					delete depositPosition[BETA_SHARE][betaSpentCounter++];
				else
					pos.count--;
				betaCurrentTotalDeposits--;
			}
			toReturn += _primary == address(ALPHA) ? ALPHA_SHARE : BETA_SHARE;
			(totalPrimary,) = smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, 1);
		}
		// swap doggo out
		if (_swapSetup[2]) {
			require(GAMMA.balanceOf(address(this)) > 0, "ApeMatcher: !dog asset");
			uint256 id = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			uint256 oldId = _ids >> 48;
			matches[_matchId].ids = uint96((_ids & 0xffffffffffff) | (id << 48)); // swap gamma ids
			matches[_matchId].doggoOwner = assetToUser[address(GAMMA)][id]; // swap gamma owner
			delete assetToUser[address(GAMMA)][oldId];
			GAMMA.transferFrom(address(this), address(smoothOperator), id);
			totalGamma = smoothOperator.swapDoggoNft(_primary, _ids & 0xffffffffffff,  id, oldId, _user);
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		if (_swapSetup[3]) {
			require(gammaCurrentTotalDeposits > 0, "ApeMatcher: !dog deposit");
			DepositPosition storage pos = depositPosition[GAMMA_SHARE][gammaSpentCounter];
			matches[_matchId].doggoTokensOwner = pos.depositor; // swap gamma token owner
			if (pos.count == 1)
					delete depositPosition[GAMMA_SHARE][gammaSpentCounter++];
			else
				pos.count--;
			gammaCurrentTotalDeposits--;
			toReturn += GAMMA_SHARE;
			(,totalGamma) = smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, 0);
		}
	}

	/**  
	 * @notice
	 * Internal function that breaks a match
	 * @param _matchId Match ID to break
	 * @param _breakAll Boolean indicating if we break the whole match or just the dogs
	 */
	function _breakMatch(uint256 _matchId, bool _breakAll, uint256 _doglessMatchCounter) internal returns(uint256 _fee, uint256 doglessOutcome){
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!match");
		bool breakGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool primaryOwner = msg.sender == adds[0] || msg.sender == adds[1];
		_breakAll = primaryOwner ? _breakAll : false;
		if(breakGamma && !_breakAll) {
			_fee += _breakDogMatch(_matchId, _doglessMatchCounter);
			doglessOutcome = 1;
		}
		else {
			uint256 tokenId = _match.ids;
			(uint256 total, uint256 totalGamma) = smoothOperator.uncommitNFTs(_match, msg.sender);
			if (msg.sender == adds[0])
				delete assetToUser[_match.primary == 1 ? address(ALPHA) : address(BETA)][tokenId & 0xffffffffffff];
			if (msg.sender == adds[2] && tokenId >> 48 > 0)
				delete assetToUser[address(GAMMA)][tokenId >> 48];
			if (adds[2] == address(0)) {
				doglessOutcome = 2;
				doglessMatches[_match.doglessIndex] = doglessMatches[doglessMatchCounter - 1];
				delete doglessMatches[doglessMatchCounter - 1];
			}
			delete matches[_matchId];
			_fee += _processRewards(total, adds, msg.sender, false);
			if (totalGamma > 0)
				_fee += _processRewards(totalGamma, adds, msg.sender, true);
		}
	}

	/**  
	 * @notice
	 * Internal function that breaks the dog agreement in a match
	 * @param _matchId Match ID to break
	 */
	function _breakDogMatch(uint256 _matchId, uint256 _doglessMatchCounter) internal returns(uint256){
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[2] || msg.sender == adds[3], "!dog match");

		uint256 totalGamma = _unbindDoggoFromMatchId(_matchId, msg.sender, _doglessMatchCounter);
		return _processRewards(totalGamma, adds, msg.sender, true);
	}

	/**  
	 * @notice
	 * Internal function that handles the payment from a match to the users involved
	 * @param _total Amount of tokens to distribute to users
	 * @param _adds Array of users involved
	 * @param _user Initial caller of the execution
	 * @param _claimGamma Boolean indicating if the reward came from a primary of dog claim
	 */
	function _processRewards(uint256 _total, address[4] memory _adds, address _user, bool _claimGamma) internal returns(uint256 _fee){
		uint128[4] memory splits = _smartSplit(uint128(_total), _adds, _claimGamma, weights);
		for (uint256 i = 0 ; i < 4; i++)
			if (splits[i] > 0) {
				// If you own both primary nft and deposit token, no fee charged
				if ((i == 0 || i == 1) && _user == _adds[0] && _user == _adds[1] && !_claimGamma)
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
	 * @param _claimGamma Boolean indicating if the reward came from a primary of dog claim
	 * @param _weight Value holding the split ratios of primary and dog claims
	 */
	function _smartSplit(uint128 _total, address[4] memory _adds, bool _claimGamma, uint256 _weight) internal pure returns(uint128[4] memory splits) {
		uint256 i = 0;
		splits = _getWeights(_claimGamma, _weight);
		uint128 sum  = 0;
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

	/**  
	 * @notice
	 * Internal function that handles the pairing of primary assets with tokens if they exist
	 * @param _primary Contract address of the primary asset
	 * @param _primaryShare Amount pf tokens required to stake with primary asset
	 * @param _primarySpentCounter Index of token deposit of primary asset
	 */
	function _mixAndMatch(
		IERC721Enumerable _primary,
		uint256 _primaryShare,
		uint256 _primarySpentCounter) internal {
		uint256 _gammaSpentCounter = gammaSpentCounter;
		uint256 gammaCount = _min(GAMMA.balanceOf(address(this)), gammaCurrentTotalDeposits);
		uint256[3] memory _matchCounters = [doglessMatchCounter, matchCounter, _min(_primary.balanceOf(address(this)), _primary == ALPHA ? alphaCurrentTotalDeposits : betaCurrentTotalDeposits)];
		DepositPosition memory primaryPos = DepositPosition(
				depositPosition[_primaryShare][_primarySpentCounter].count,
				depositPosition[_primaryShare][_primarySpentCounter].depositor);
		DepositPosition memory gammaPos = DepositPosition(
				depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
				depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);

		if (_primary == ALPHA)
			alphaCurrentTotalDeposits -= _matchCounters[2];
		else
			betaCurrentTotalDeposits -= _matchCounters[2];
		gammaCurrentTotalDeposits -= _min(_matchCounters[2], gammaCount);
		for (uint256 i = 0; i < _matchCounters[2] ; i++) {
			uint256 gammaId = 0;
			uint256 id = _primary.tokenOfOwnerByIndex(address(this), 0);
			if (i < gammaCount)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			else
				doglessMatches[_matchCounters[0]++] = _matchCounters[1];
			matches[_matchCounters[1]++] = GreatMatch(
				true,
				_primary == ALPHA ? uint8(1) : uint8(2),
				uint32(block.timestamp),
				i < gammaCount ? 0 : uint96(_matchCounters[0] - 1),
				uint96((gammaId << 48) + id),
				assetToUser[address(_primary)][id],
				primaryPos.depositor,
				i < gammaCount ? assetToUser[address(GAMMA)][gammaId] : address(0),
				i < gammaCount ? gammaPos.depositor : address(0)
			);
			primaryPos.count--;
			if (i < gammaCount)
				gammaPos.count--;
			if (primaryPos.count == 0) {
				delete depositPosition[_primaryShare][_primarySpentCounter++];
				primaryPos = DepositPosition(
					depositPosition[_primaryShare][_primarySpentCounter].count,
					depositPosition[_primaryShare][_primarySpentCounter].depositor);
			}
			if (gammaPos.count == 0 && i < gammaCount) {
				delete depositPosition[GAMMA_SHARE][_gammaSpentCounter++];
				gammaPos = DepositPosition(
					depositPosition[GAMMA_SHARE][_gammaSpentCounter].count,
					depositPosition[GAMMA_SHARE][_gammaSpentCounter].depositor);
			}
			_primary.transferFrom(address(this), address(smoothOperator), id);
			if (i < gammaCount)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			smoothOperator.commitNFTs(address(_primary), id, gammaId);
		}
		if (_primary == ALPHA)
			alphaSpentCounter = _primarySpentCounter;
		else
			betaSpentCounter = _primarySpentCounter;
		gammaSpentCounter = _gammaSpentCounter;
		depositPosition[_primaryShare][_primarySpentCounter].count = primaryPos.count;
		depositPosition[GAMMA_SHARE][_gammaSpentCounter].count = gammaPos.count;
		doglessMatchCounter = _matchCounters[0];
		matchCounter = _matchCounters[1];
	}

	/**
	 * @notice
	 * Internal function that handles the pairing of DOG assets with tokens if they exist to an existing dogless match
	 */
	function _bindDoggoToMatchId() internal {
		uint256 toBind = _min(doglessMatchCounter, _min(GAMMA.balanceOf(address(this)), gammaCurrentTotalDeposits));
		if (toBind == 0) return;
		uint256 doglessIndex = doglessMatchCounter - 1;
		DepositPosition memory gammaPos = DepositPosition(
				depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
				depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);

		gammaCurrentTotalDeposits -= toBind;
		for (uint256 i = 0; i < toBind; i++) {
			GreatMatch storage _match = matches[doglessMatches[doglessIndex - i]];
			uint256 gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
			delete doglessMatches[doglessIndex - i];
			_match.ids |= uint96(gammaId << 48);
			_match.doggoOwner = assetToUser[address(GAMMA)][gammaId];
			_match.doggoTokensOwner = gammaPos.depositor;
			_match.doglessIndex = 0;
			GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			smoothOperator.bindDoggoToExistingPrimary(primary, _match.ids & 0xffffffffffff, gammaId);
			if (--gammaPos.count == 0) {
				delete depositPosition[GAMMA_SHARE][gammaSpentCounter++];
				gammaPos = DepositPosition(
					depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
					depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);
			}
		}
		doglessMatchCounter -= toBind;
		depositPosition[GAMMA_SHARE][gammaSpentCounter].count = gammaPos.count;
	}

	/**
	 * @notice
	 * Internal function that handles unbinding a dog from a match
	 * @param _matchId Match ID to remove the dog from
	 * @param _caller Initial caller of this execution
	 */
	function _unbindDoggoFromMatchId(uint256 _matchId, address _caller, uint256 _doglessMatchCounter) internal returns(uint256 totalGamma) {
		GreatMatch storage _match = matches[_matchId];
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		address dogOwner = _match.doggoOwner;
		uint256 ids = _match.ids;
		totalGamma = smoothOperator.unbindDoggoFromExistingPrimary(
			primary,
			ids & 0xffffffffffff,
			ids >> 48,
			dogOwner,
			_match.doggoTokensOwner,
			_caller);
		if (dogOwner == _caller)	
			delete assetToUser[address(GAMMA)][ids >> 48];
		_match.doggoOwner = address(0);
		_match.doggoTokensOwner = address(0);
		_match.doglessIndex = uint96(_doglessMatchCounter);
		doglessMatches[_doglessMatchCounter] = _matchId;
		_match.ids = uint96(ids & 0xffffffffffff);
	}

	/**
	 * @notice
	 * Internal function that handles deposits for a user
	 * @param _type Deposit type (bayc/mayc/bakc)
	 * @param _amount Amount of deposits
	 * @param _user User to whom attribute the deposits
	 */
	function _handleDeposit(uint256 _type, uint32 _amount, address _user) internal {
		if (_type == ALPHA_SHARE) {
			depositPosition[ALPHA_SHARE][alphaDepositCounter++] = DepositPosition(_amount, _user);
			alphaCurrentTotalDeposits += _amount;
		}
		else if (_type == BETA_SHARE) {
			depositPosition[BETA_SHARE][betaDepositCounter++] =  DepositPosition(_amount, _user);
			betaCurrentTotalDeposits += _amount;
		}
		else if (_type == GAMMA_SHARE) {
			depositPosition[GAMMA_SHARE][gammaDepositCounter++] =  DepositPosition(_amount, _user);
			gammaCurrentTotalDeposits += _amount;
		}
	}

	/**
	 * @notice
	 * Internal function that handles deposits for a user
	 * @param _type Deposit type (bayc/mayc/bakc)
	 * @param _index Index of deposits
	 * @param _amount Amount of deposits to return
	 * @param _user User to whom attribute the deposits
	 */
	function _verifyAndReturnDepositValue(
		uint256 _type,
		uint256 _index,
		uint32 _amount,
		address _user) internal returns (uint256){
		uint256 count;
		if (_type == 0) {
			require(alphaDepositCounter > _index, "ApeMatcher: deposit !exist");
			require(alphaSpentCounter <= _index, "ApeMatcher: deposit consumed"); 
			require(depositPosition[ALPHA_SHARE][_index].depositor == _user, "ApeMatcher: Not owner of deposit");
			count = depositPosition[ALPHA_SHARE][_index].count;
			require(_amount <= count, "ApeMatcher: !amount");

			alphaCurrentTotalDeposits -= _amount;
			if (count == _amount) {
				depositPosition[ALPHA_SHARE][_index] = depositPosition[ALPHA_SHARE][alphaDepositCounter - 1];
				delete depositPosition[ALPHA_SHARE][alphaDepositCounter-- - 1];
			}
			else
				depositPosition[ALPHA_SHARE][_index].count -= _amount;
			return ALPHA_SHARE * _amount;
		}
		else if (_type == 1) {
			require(betaDepositCounter > _index, "ApeMatcher: deposit !exist");
			require(betaSpentCounter <= _index, "ApeMatcher: deposit consumed");
			require(depositPosition[BETA_SHARE][_index].depositor == _user, "ApeMatcher: Not owner of deposit");
			count = depositPosition[BETA_SHARE][_index].count;
			require(_amount <= count, "ApeMatcher: !amount");

			betaCurrentTotalDeposits -= _amount;
			if (count == _amount) {
				depositPosition[BETA_SHARE][_index] = depositPosition[BETA_SHARE][betaDepositCounter - 1];
				delete depositPosition[BETA_SHARE][betaDepositCounter-- - 1];
			}
			else
				depositPosition[BETA_SHARE][_index].count -= _amount;
			return BETA_SHARE * _amount;
		}
		else if (_type == 2) {
			require(gammaDepositCounter > _index, "ApeMatcher: deposit !exist");
			require(gammaSpentCounter <= _index, "ApeMatcher: deposit consumed");
			require(depositPosition[GAMMA_SHARE][_index].depositor == _user, "ApeMatcher: Not owner of deposit");
			count = depositPosition[GAMMA_SHARE][_index].count;
			require(_amount <= count, "ApeMatcher: !amount");

			gammaCurrentTotalDeposits -= _amount;
			if (count == _amount) {
				depositPosition[GAMMA_SHARE][_index] = depositPosition[GAMMA_SHARE][gammaDepositCounter - 1];
				delete depositPosition[GAMMA_SHARE][gammaDepositCounter-- - 1];
			}
			else
				depositPosition[GAMMA_SHARE][_index].count -= _amount;
			return GAMMA_SHARE * _amount;
		}
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
		for(uint256 i = 0; i < _tokenIds.length; i++) {
			IApeStaking.Position memory pos = APE_STAKING.nftPosition(poolId, _tokenIds[i]);
			require (pos.stakedAmount == 0, "ApeMatcher: NFT already commited");
			require(_nft.ownerOf(_tokenIds[i]) == _user, "ApeMatcher: !owner");
			// EmperorTomatoKetchup, you can't use your #0
			if (_nft == GAMMA && _tokenIds[i] == 0) revert();
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
			require(assetToUser[address(_nft)][_tokenIds[i]] == _user, "ApeMatcher: !owner");
			delete assetToUser[address(_nft)][_tokenIds[i]];
			_nft.transferFrom(address(this), _user, _tokenIds[i]);
		}
	}

	function _handleFee(uint256 _fee) internal {
		if (_fee > 0)
			fee += _fee;
	}

	function _min(uint256 _a, uint256 _b) internal pure returns (uint256) {
		return _a > _b ? _b : _a;
	}

	/**
	 * @notice
	 * Internal function that fetches the split ratio of a given claim (primary or dog)
	 * @param _claimGamma Boolean that indicates if this is a dog claim or not
	 * @param _weight Value holding the split ratios
	 */
	function _getWeights(bool _claimGamma, uint256 _weight) internal pure returns(uint128[4] memory _weights) {
		uint256 dogMask = (2 << 128) - 1;
		uint256 _uint32Mask = (2 << 32) - 1;
		if (_claimGamma)
			_weight &= dogMask;
		else
			_weight >>= 128;
		_weights[0] = uint128((_weight >> (32 * 3)) & _uint32Mask);
		_weights[1] = uint128((_weight >> (32 * 2)) & _uint32Mask);
		_weights[2] = uint128((_weight >> (32 * 1)) & _uint32Mask);
		_weights[3] = uint128((_weight >> (32 * 0)) & _uint32Mask);
	}
}