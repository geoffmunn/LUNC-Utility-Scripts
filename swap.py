#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.common import (
    check_database,
    check_version
)

from constants.constants import (
    FULL_COIN_LOOKUP,
    USER_ACTION_QUIT
)

from classes.swap_transaction import swap_coins
from classes.transaction_core import TransactionResult
from classes.wallets import UserWallets

from terra_classic_sdk.core.coin import Coin
#from hashlib import sha256

def main():

    # Check if there is a new version we should be using
    check_version()
    check_database()

    # Get the user wallets
    wallets = UserWallets()
    user_wallets = wallets.loadUserWallets()

    if user_wallets is None:  
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    if len(user_wallets) > 0:
        print (f'You can make swaps on the following wallets:')

        wallet, answer = wallets.getUserSinglechoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", 'X' to continue, or 'Q' to quit: ")

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    # List all the coins in this wallet, with the amounts available:
    print ('\nWhat coin do you want to swap FROM?')
    coin_count:int = 0
    for coin in wallet.balances:
        if coin in FULL_COIN_LOOKUP:
            coin_count += 1

    coin_from, answer, null_value = wallet.getCoinSelection("Select a coin number 1 - " + str(coin_count) + ", 'X' to continue, or 'Q' to quit: ", wallet.balances)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    available_balance:float = wallet.formatUluna(wallet.balances[coin_from], coin_from)
    print (f'This coin has a maximum of {available_balance} {FULL_COIN_LOOKUP[coin_from]} available.')
    swap_uluna = wallet.getUserNumber("How much do you want to swap? (Or type 'Q' to quit) ", {'max_number': float(available_balance), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': coin_from})

    if swap_uluna == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    print ('\nWhat coin do you want to swap TO?')
    coin_to, answer, estimated_amount = wallet.getCoinSelection("Select a coin number 1 - " + str(len(FULL_COIN_LOOKUP)) + ", 'X' to continue, or 'Q' to quit: ", wallet.balances, False, {'denom':coin_from, 'amount':swap_uluna})

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    estimated_amount = str(("%.6f" % (estimated_amount)).rstrip('0').rstrip('.'))

    swap_coin:Coin = wallet.createCoin(coin_from, swap_uluna)
    transaction_result:TransactionResult = swap_coins(wallet, swap_coin, coin_to, estimated_amount, True)
    transaction_result.showResults()
    
    # # Create the swap object
    # swap_tx = SwapTransaction().create(seed = wallet.seed, denom = wallet.denom)

    # # Assign the details:
    # swap_tx.balances           = wallet.balances
    # swap_tx.swap_amount        = int(swap_uluna)
    # swap_tx.swap_denom         = coin_from
    # swap_tx.swap_request_denom = coin_to
    # swap_tx.sender_address     = wallet.address
    # swap_tx.sender_prefix      = wallet.getPrefix(wallet.address)
    # swap_tx.wallet_denom       = wallet.denom

    # # Bump up the gas adjustment - it needs to be higher for swaps it turns out
    # swap_tx.terra.gas_adjustment = float(GAS_ADJUSTMENT_SWAPS)

    # # Set the contract based on what we've picked
    # # As long as the swap_denom and swap_request_denom values are set, the correct contract should be picked
    # use_market_swap:bool  = swap_tx.setContract()
    # is_offchain_swap:bool = swap_tx.isOffChainSwap()

    # if is_offchain_swap == True:
    #     # This is an off-chain swap. Something like LUNC(terra)->OSMO or LUNC(Osmosis) -> wETH
    #     result = swap_tx.offChainSimulate()

    #     if result == True:
    #         print (f'You will be swapping {wallet.formatUluna(swap_uluna, coin_from, False)} {FULL_COIN_LOOKUP[coin_from]} for approximately {estimated_amount} {FULL_COIN_LOOKUP[coin_to]}')
    #         print (swap_tx.readableFee())

    #         user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

    #         if user_choice == False:
    #             exit()

    #         result = swap_tx.offChainSwap()
    # else:
    #     if use_market_swap == True:
    #         # uluna -> umnt, uluna -> ujpy etc
    #         # This is for terra-native swaps ONLY
    #         result = swap_tx.marketSimulate()
    #         if result == True:
    #             print (f'You will be swapping {wallet.formatUluna(swap_uluna, coin_from, False)} {FULL_COIN_LOOKUP[coin_from]} for approximately {estimated_amount} {FULL_COIN_LOOKUP[coin_to]}')
    #             print (swap_tx.readableFee())
    #             user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

    #             if user_choice == False:
    #                 exit()

    #             result = swap_tx.marketSwap()
    #     else:
    #         # This is for uluna -> uusd swaps ONLY. We use the contract addresses to support this
    #         result = swap_tx.simulate()

    #         if result == True:
    #             print (f'You will be swapping {wallet.formatUluna(swap_uluna, coin_from, False)} {FULL_COIN_LOOKUP[coin_from]} for approximately {estimated_amount} {FULL_COIN_LOOKUP[coin_to]}')
    #             print (swap_tx.readableFee())
    #             user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

    #             if user_choice == False:
    #                 exit()

    #             result = swap_tx.swap()
    
    # if result == True:
    #     swap_tx.broadcast()

    #     if swap_tx.broadcast_result is not None and swap_tx.broadcast_result.code == 32:
    #         while True:
    #             print (' 🛎️  Boosting sequence number and trying again...')

    #             swap_tx.sequence = swap_tx.sequence + 1
    #             swap_tx.simulate()
    #             print (swap_tx.readableFee())

    #             swap_tx.swap()
    #             swap_tx.broadcast()

    #             if swap_tx is None:
    #                 break

    #             # Code 32 = account sequence mismatch
    #             if swap_tx.broadcast_result.code != 32:
    #                 break

    #     if swap_tx.broadcast_result is None or swap_tx.broadcast_result.is_tx_error():
    #         if swap_tx.broadcast_result is None:
    #             print (' 🛎️  The swap transaction failed, no broadcast object was returned.')
    #         else:
    #             print (' 🛎️  The swap transaction failed, an error occurred:')
    #             if swap_tx.broadcast_result.raw_log is not None:
    #                 print (f' 🛎️  {swap_tx.broadcast_result.raw_log}')
    #             else:
    #                 print ('No broadcast log was available.')
    #     else:
    #         if swap_tx.result_received is not None:
    #             print (f' ✅ Swapped amount: {wallet.formatUluna(swap_tx.swap_amount, swap_tx.swap_denom)} {FULL_COIN_LOOKUP[swap_tx.swap_denom]}')
    #             print (f' ✅ Received amount: {wallet.formatUluna(swap_tx.result_received.amount, swap_tx.swap_request_denom)} {FULL_COIN_LOOKUP[swap_tx.swap_request_denom]}')
    #             print (f' ✅ Tx Hash: {swap_tx.broadcast_result.txhash}')
        
    # else:
    #     print (' 🛎️  The swap transaction could not be completed')

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()