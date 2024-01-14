#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.common import (
    check_database,
    check_version,
    get_user_choice,
    isPercentage
)

from constants.constants import (
    CHAIN_DATA,
    EXIT_POOL,
    FULL_COIN_LOOKUP,
    JOIN_POOL,
    ULUNA,
    UOSMO,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
)

from classes.wallet import UserWallet
from classes.wallets import UserWallets
from classes.liquidity_transaction import LiquidityTransaction

def get_send_to_address(user_wallets:UserWallet):
    """
    Show a simple list address from what is found in the user_config file
    """

    label_widths:list = []

    label_widths.append(len('Number'))
    label_widths.append(len('Wallet name'))

    for wallet_name in user_wallets:
        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)
                
    # Generic string we use for padding purposes
    padding_str:str   = ' ' * 100
    header_string:str = ' Number |'

    if label_widths[1] > len('Wallet name'):
        header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' | Address                                      '
    else:
        header_string +=  ' Wallet name | Address                                      '

    horizontal_spacer:str = '-' * len(header_string)

    # Create default variables and values
    wallets_to_use:dict   = {}
    user_wallet:dict      = {}
    recipient_address:str = ''

    while True:

        count:int            = 0
        wallet_numbers:dict  = {}
        wallets_by_name:dict = {}

        print ('\n' + horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for wallet_name in user_wallets:
            wallet:UserWallet = user_wallets[wallet_name]

            count += 1
            wallet_numbers[count] = wallet
            wallets_by_name[wallet.name.lower()] = count

            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            wallet_name_str    = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]
            wallet_address:str = wallet.address
            
            print (f"{count_str}{glyph} | {wallet_name_str} | {wallet_address}")
            
        print (horizontal_spacer + '\n')

        print ('You can send to an address in your config file by typing the wallet name or number.')
        print ('You can also send to a completely new address by entering the wallet address.\n')

        answer:str = input("What is the address you are sending to? (or type 'X' to continue, or 'Q' to quit) ").lower()
        
        # Check if someone typed the name of a wallet
        if answer in wallets_by_name.keys():
            answer = str(wallets_by_name[answer])
        
        if answer.isdigit() and int(answer) in wallet_numbers:

            wallets_to_use:dict = {}

            key:str = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
        else:
            # check if this is an address we support:
            prefix:str = wallet.getPrefix(answer)

            if prefix in wallet.getSupportedPrefixes():
                recipient_address:str = answer
                break
            
        if answer == USER_ACTION_CONTINUE:
            if len(wallets_to_use) > 0:
                break
            else:
                print ('\nPlease select a wallet first.\n')

        if answer == USER_ACTION_QUIT:
            break

    # Get the first (and only) wallet from the list
    if len(wallets_to_use) > 0:
        for item in wallets_to_use:
            user_wallet:UserWallet = wallets_to_use[item]
            recipient_address:str  = user_wallet.address
            break
    
    return recipient_address, answer

from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins

def main():

    # Check if there is a new version we should be using
    check_version()
    check_database()

    # Get the user wallets
    wallets           = UserWallets()
    user_wallets:dict = wallets.loadUserWallets(filter = [CHAIN_DATA[UOSMO]['bech32_prefix']])

    if len(user_wallets) > 0:
        print (f'You can join or exit liquidity pools on the following wallets:')

        wallet, answer = wallets.getUserSinglechoice(f"Select a wallet number 1 - {str(len(user_wallets))}, 'X' to continue, or 'Q' to quit: ")

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    denom:str = ULUNA

    print ('Loading pool list, please wait...')
    
    # Create the send tx object
    liquidity_tx = LiquidityTransaction().create(wallet.seed, wallet.denom)

    user_pool, answer = liquidity_tx.getPoolSelection('What pool do you want to use? ', wallet, ULUNA)

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    

    # Populate it with the details we have so far:
    liquidity_tx.balances        = wallet.balances
    liquidity_tx.pool_id         = user_pool
    liquidity_tx.pools           = wallet.pools
    liquidity_tx.sender_address  = wallet.address
    liquidity_tx.source_channel  = CHAIN_DATA[wallet.denom]['ibc_channels'][ULUNA]
    liquidity_tx.wallet_denom    = wallet.denom

    # Are we joining aliquidity pool, or exiting?
    join_or_exit = get_user_choice('Do you want to join (J) a liquidity pool, or exit (E)? ', [JOIN_POOL, EXIT_POOL])

    if join_or_exit == JOIN_POOL:
        print (f"The {wallet.name} wallet holds {wallet.formatUluna(wallet.balances[denom], denom)} {FULL_COIN_LOOKUP[denom]}")
        print (f"NOTE: You can send the entire value of this wallet by typing '100%' - no minimum amount will be retained.")

        uluna_amount:int       = wallet.getUserNumber('How much are you sending? ', {'max_number': float(wallet.formatUluna(wallet.balances[denom], denom, False)), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': True, 'keep_minimum': False, 'target_denom': denom})
        liquidity_tx.amount_in = uluna_amount

    else:
        # This is the exit pool logic
        # Get the assets for the summary list
        pool_assets:dict  = liquidity_tx.getPoolAssets()
        asset_values:dict = liquidity_tx.getAssetValues(pool_assets)
        total_value:float = 0

        print ('This pool holds:\n')
        for asset_denom in pool_assets:
            print (' *  ' + str(round(pool_assets[asset_denom], 2)) + ' ' + FULL_COIN_LOOKUP[asset_denom] + ' $' + str(round(asset_values[asset_denom],2)))
            total_value += asset_values[asset_denom]

        total_value = round(total_value, 2)

        print (f'Total value: ${total_value}')

        print ('\nHow much do you want to withdraw?')
        print ('You can type a percentage (eg 50%), or an exact amount of LUNC.')

        user_withdrawal:str = wallet.getUserNumber('How much LUNC are you withdrawing? ', {'max_number': float(pool_assets[ULUNA]), 'min_number': 0, 'percentages_allowed': True, 'convert_percentages': False, 'keep_minimum': False, 'target_denom': ULUNA})
        
        if isPercentage(user_withdrawal):
            amount_out:float = float(user_withdrawal[:-1]) / 100
        
        liquidity_tx.amount_out = amount_out

    #denom, answer, null_value = wallet.getCoinSelection(f"Select a coin number 1 - {str(len(FULL_COIN_LOOKUP))} that you want to send, 'X' to continue, or 'Q' to quit: ", wallet.balances)

    #if answer == USER_ACTION_QUIT:
    #    print (' 🛑 Exiting...\n')
    #    exit()

    # Populate it with remaining required details:
    liquidity_tx.liquidity_denom  = denom
    
    # Simulate it
    if join_or_exit == JOIN_POOL:
        result = liquidity_tx.joinSimulate()
    else:
        result = liquidity_tx.exitSimulate()
    
    if result == True:

        if join_or_exit == JOIN_POOL:
            print (f'You are about to add {wallet.formatUluna(uluna_amount, denom)} {FULL_COIN_LOOKUP[denom]} to Pool #{liquidity_tx.pool_id}')
        else:
            print (f'You are about to withdraw some stuff @TODO FIX ME')

        print (liquidity_tx.readableFee())

        user_choice = get_user_choice('Do you want to continue? (y/n) ', [])

        if user_choice == False:
            exit()

        # Now we know what the fee is, we can do it again and finalise it
        if join_or_exit == JOIN_POOL:
            result = liquidity_tx.joinPool()
        else:
            result = liquidity_tx.exitPool()
            
        if result == True:
            liquidity_tx.broadcast()

            if liquidity_tx.broadcast_result is not None and liquidity_tx.broadcast_result.code == 32:
                while True:
                    print (' 🛎️  Boosting sequence number and trying again...')

                    liquidity_tx.sequence = liquidity_tx.sequence + 1
                    
                    if join_or_exit == JOIN_POOL:
                        liquidity_tx.joinSimulate()
                        liquidity_tx.joinPool()
                    else:
                        liquidity_tx.exitSimulate()
                        liquidity_tx.exitPool()

                    liquidity_tx.broadcast()

                    if liquidity_tx is None:
                        break

                    # Code 32 = account sequence mismatch
                    if liquidity_tx.broadcast_result.code != 32:
                        break

            if liquidity_tx.broadcast_result is None or liquidity_tx.broadcast_result.is_tx_error():
                if liquidity_tx.broadcast_result is None:
                    print (' 🛎️  The liquidity transaction failed, no broadcast object was returned.')
                else:
                    print (' 🛎️  The liquidity transaction failed, an error occurred:')
                    if liquidity_tx.broadcast_result.raw_log is not None:
                        print (f' 🛎️  Error code {liquidity_tx.broadcast_result.code}')
                        print (f' 🛎️  {liquidity_tx.broadcast_result.raw_log}')
                    else:
                        print ('No broadcast log was available.')
            else:
                if liquidity_tx.result_received is not None:
                    if join_or_exit == JOIN_POOL:
                        print (f' ✅ Sent amount into pool #{liquidity_tx.pool_id}: {wallet.formatUluna(liquidity_tx.result_sent, liquidity_tx.liquidity_denom)} {FULL_COIN_LOOKUP[liquidity_tx.liquidity_denom]}')
                        print (f' ✅ Joined amount: {wallet.formatUluna(liquidity_tx.result_received.amount, liquidity_tx.liquidity_denom)} {FULL_COIN_LOOKUP[liquidity_tx.liquidity_denom]}')
                    else:
                        print (f' ✅ Withdrawn amount from pool #{liquidity_tx.pool_id}: {wallet.formatUluna(liquidity_tx.result_sent, liquidity_tx.liquidity_denom)} {FULL_COIN_LOOKUP[liquidity_tx.liquidity_denom]}')
                        print (f' ✅ Received coins: ')
                        received_coin:Coin
                        for received_coin in liquidity_tx.result_received:
                            print (' *  ' + wallet.formatUluna(received_coin.amount, received_coin.denom, True))
                    print (f' ✅ Tx Hash: {liquidity_tx.broadcast_result.txhash}')
        else:
            print (' 🛎️  The liquidity transaction could not be completed')

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()