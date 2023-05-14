#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from getpass import getpass

from utility_classes import (
    get_user_choice,
    isPercentage,
    UserConfig,
    Wallets,
    Wallet
)

from utility_constants import (
    ASTROPORT_UUSD_TO_ULUNA_ADDRESS,
    COIN_DIVISOR,
    GAS_ADJUSTMENT_INCREMENT,
    MAX_GAS_ADJUSTMENT,
    USER_ACTION_ALL,
    USER_ACTION_CONTINUE,
    USER_ACTION_CLEAR,
    USER_ACTION_DELEGATE,
    USER_ACTION_QUIT,
    USER_ACTION_SWAP,
    USER_ACTION_SWAP_DELEGATE,
    USER_ACTION_WITHDRAW,
    USER_ACTION_WITHDRAW_DELEGATE,
    WITHDRAWAL_REMAINDER
)

def get_user_multichoice(question:str, user_wallets:dict) -> dict|str:
    """
    Get multiple user selections from a list.
    This is a custom function because the options are specific to this list.
    """

    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Wallet name'))
    label_widths.append(len('LUNC'))
    label_widths.append(len('USTC'))
    label_widths.append(len('Available'))

    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]

        # Get the delegations and balances for this wallet
        delegations = wallet.getDelegations()
        balances    = wallet.getBalances()

        # Initialise the reward values
        ulunc_reward:int = 0
        ustc_reward:int  = 0

        for validator in delegations:
            if 'uluna' in delegations[validator]['rewards']:
                ulunc_reward += float(wallet.formatUluna(delegations[validator]['rewards']['uluna'], False))
                                    
            if 'uusd' in delegations[validator]['rewards']:
                ustc_reward += float(wallet.formatUluna(delegations[validator]['rewards']['uusd'], False))

        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        if len(str(ulunc_reward)) > label_widths[2]:
            label_widths[2] = len(str(ulunc_reward))

        if len(str(ustc_reward)) > label_widths[3]:
            label_widths[3] = len(str(ustc_reward))

        if 'uluna' in balances:
            formatted_val = str(wallet.formatUluna(balances['uluna'], False))
            if len(formatted_val) > label_widths[4]:
                label_widths[4] = len(formatted_val)

    padding_str = ' ' * 100

    header_string = ' Number |'

    if label_widths[1] > len('Wallet name'):
        header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' '
    else:
        header_string +=  ' Wallet name '

    if label_widths[4] > len('Available'):
        header_string += '| Available' + padding_str[0:label_widths[4] - len('Available')] + ' '
    else:
        header_string += '| Available '

    if label_widths[2] > len('LUNC'):
        header_string += '| LUNC' + padding_str[0:label_widths[2] - len('LUNC')] + ' '
    else:
        header_string += '| LUNC'

    if label_widths[3] > len('USTC'):
        header_string += '| USTC' + padding_str[0:label_widths[3] - len('USTC')] + ' '
    else:
        header_string += '| USTC '

    horizontal_spacer = '-' * len(header_string)

    wallets_to_use = {}
    while True:

        count = 0
        wallet_numbers = {}

        print (horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for wallet_name in user_wallets:
            wallet:Wallet = user_wallets[wallet_name]
            delegations   = wallet.getDelegations()
            balances      = wallet.getBalances()

            count += 1
            wallet_numbers[count] = wallet
                
            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = '  '

            count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
            wallet_name_str = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]  

            uluna_reward:int  = 0
            uluna_balance:int = 0
            ustc_reward:int   = 0
            
            for validator in delegations:
                if 'uluna' in delegations[validator]['rewards']:
                    uluna_reward += delegations[validator]['rewards']['uluna']
                if 'uusd' in delegations[validator]['rewards']:
                    ustc_reward += delegations[validator]['rewards']['uusd']

            lunc_str = str(wallet.formatUluna(uluna_reward, False))
            if label_widths[2] - len(str(lunc_str)) > 0:
                lunc_str += padding_str[0:(label_widths[2] - (len(str(lunc_str))))]
            
            if 'uluna' in wallet.balances:
                uluna_balance = str(wallet.formatUluna(wallet.balances['uluna'], False))
                if label_widths[4] - len(str(uluna_balance)) > 0:
                    uluna_balance += padding_str[0:(label_widths[4] - (len(str(uluna_balance))))]
            else:
                uluna_balance = padding_str[0:label_widths[4]]

            if 'uusd' in wallet.balances:
                ustc_str = str(wallet.formatUluna(ustc_reward, False))
                if label_widths[3] - len(str(ustc_str)) > 0:
                    ustc_str += padding_str[0:(label_widths[3] - (len(str(ustc_str))))]
            else:
                ustc_str = padding_str[0:label_widths[3]]

            print (f"{count_str}{glyph} | {wallet_name_str} | {uluna_balance} | {lunc_str} | {ustc_str}")
            
        print (horizontal_spacer + '\n')
            
        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) in wallet_numbers:
            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
            
        if answer == USER_ACTION_CLEAR:
            wallets_to_use = {}
        
        if answer == USER_ACTION_ALL:
            wallets_to_use = {}
            for wallet_name in user_wallets:
                wallets_to_use[wallet_name] = user_wallets[wallet_name]

        if answer == USER_ACTION_CONTINUE:
            break

        if answer == USER_ACTION_QUIT:
            break

    return wallets_to_use, answer
    
def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    if decrypt_password == '':
        print (' 🛑 Exiting...')
        exit()
        
    # Get the desired actions
    print ('\nWhat action do you want to take?\n')
    print ('  (W)  Withdraw rewards')
    print ('  (S)  Swap coins')
    print ('  (D)  Delegate')
    print ('  (A)  All of the above')
    print ('  (WD) Withdraw & Delegate')
    print ('  (SD) Swap & Delegate')
    print ('  (Q)  Quit\n')

    user_action = get_user_choice('Pick an option: ', [
        USER_ACTION_WITHDRAW,
        USER_ACTION_SWAP,
        USER_ACTION_DELEGATE,
        USER_ACTION_ALL,
        USER_ACTION_WITHDRAW_DELEGATE,
        USER_ACTION_SWAP_DELEGATE,
        USER_ACTION_QUIT
    ])

    if user_action == USER_ACTION_QUIT:
        print (' 🛑 Exiting...')
        exit()
        
    # Get the user config file contents
    user_config:str = UserConfig().contents()
    if user_config == '':
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script.')
        exit()

    print ('Decrypting and validating wallets - please wait...\n')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    
    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    # Get the balances on each wallet (for display purposes)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        delegations = wallet.getDelegations()
        
    action_string = ''
    if user_action == USER_ACTION_WITHDRAW:
        action_string = 'withdraw rewards'
    if user_action == USER_ACTION_SWAP:
        action_string = 'swap USTC for LUNC'
    if user_action == USER_ACTION_DELEGATE:
        action_string = 'delegate all available funds'
    if user_action == USER_ACTION_WITHDRAW_DELEGATE:
        action_string = 'withdraw rewards and delegate everything'
    if user_action == USER_ACTION_SWAP_DELEGATE:
        action_string = 'swap USTC for LUNC and delegate everything'
    if user_action == USER_ACTION_ALL:
        action_string = 'withdraw rewards, swap USTC for LUNC, and then delegate everything'

    if action_string == '':
        print (' 🛑 No recognised action to complete, exiting...')
        exit()

    if len(user_wallets) > 0:
        print (f'You can {action_string} on the following wallets:')

        user_wallets,answer = get_user_multichoice(f"Select a wallet number 1 - {str(len(user_wallets))}, or 'A' to add all of them, 'C' to clear the list, 'X' to continue, or 'Q' to quit: ", user_wallets)

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.")
        exit()

    print (f'\nYou are about to {action_string} on the following wallets:\n')
    for wallet_name in user_wallets:
        print (f' * {wallet_name}')

    continue_action = get_user_choice('\nDo you want to continue? (y/n) ', [])
    if continue_action == False:
        print (' 🛑 Exiting...')
        exit()

    # Now start doing stuff
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]

        print ('####################################')
        print (f'Accessing the {wallet.name} wallet...')

        delegations = wallet.getDelegations()
        for validator in delegations:

            if 'uluna' in delegations[validator]['rewards']:
                print ('\n------------------------------------')
                print (f"The {delegations[validator]['validator_name']} validator has a {delegations[validator]['commission']}% commission.")

                if user_action in [USER_ACTION_WITHDRAW, USER_ACTION_WITHDRAW_DELEGATE, USER_ACTION_ALL]:

                    print ('Starting withdrawals...')

                    uluna_reward:int = delegations[validator]['rewards']['uluna']

                    # Only withdraw the staking rewards if the rewards exceed the threshold (if any)
                    if uluna_reward > wallet.delegations['threshold']:

                        print (f'Withdrawing {wallet.formatUluna(uluna_reward, False)} rewards')

                        # Update the balances so we know what we have to pay the fee with
                        wallet.getBalances(True)

                        # Set up the withdrawal object
                        withdrawal_tx = wallet.withdrawal().create(delegations[validator]['delegator'], delegations[validator]['validator'])

                        # Simulate it
                        result = withdrawal_tx.simulate()

                        if result == True:

                            print (withdrawal_tx.readableFee())

                            # Now we know what the fee is, we can do it again and finalise it
                            result = withdrawal_tx.withdraw()

                            if result == True:
                                withdrawal_tx.broadcast()
                            
                                if withdrawal_tx.broadcast_result.code == 11:
                                    while True:
                                        print (' 🛎️  Increasing the gas adjustment fee and trying again')
                                        withdrawal_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
                                        print (f' 🛎️  Gas adjustment value is now {withdrawal_tx.terra.gas_adjustment}')
                                        withdrawal_tx.simulate()
                                        print (withdrawal_tx.readableFee())
                                        withdrawal_tx.withdraw()
                                        withdrawal_tx.broadcast()

                                        if withdrawal_tx.broadcast_result is None:
                                            break

                                        #if withdrawal_tx.broadcast_result.code != 11:
                                        if withdrawal_tx.broadcast_result.code == 0:
                                            break

                                        # if withdrawal_tx.broadcast_result.code == 32:
                                        #     withdrawal_tx.sequence = withdrawal_tx.sequence + 1
                                        #     #self.sequence    = self.sequence + 1
                                        #     #options.sequence = self.sequence
                                        #     withdrawal_tx.
                                        #     print (' 🛎️  Boosting sequence number')
                                        # else:
                                        #     print (err)
                                        #     break

                                        if withdrawal_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
                                            break
                                        
                                if withdrawal_tx.broadcast_result.is_tx_error():
                                    print (' 🛎️  The withdrawal failed, an error occurred:')
                                    print (f' 🛎️  {withdrawal_tx.broadcast_result.raw_log}')
                            
                                else:
                                    print (f' ✅ Withdrawn amount: {wallet.formatUluna(uluna_reward, True)}')
                                    print (f' ✅ Tx Hash: {withdrawal_tx.broadcast_result.txhash}')
                        else:
                            print (' 🛎️  The withdrawal could not be completed')
                    else:
                        print (' 🛎️  The amount of LUNC in this wallet does not exceed the withdrawal threshold')

            # Swap any uusd coins for uluna
            if user_action in [USER_ACTION_SWAP, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:

                if wallet.allow_swaps == True:
                    print ('\n------------------------------------')
                    print ('Starting swaps...')

                    # Update the balances so we know we have the correct amount
                    wallet.getBalances(True)
                    
                    # We are only supporting swaps with uusd (USTC) at the moment
                    if 'uusd' in wallet.balances:
                        swap_amount = wallet.balances['uusd']

                        if swap_amount > 0:
                            print (f'Swapping {wallet.formatUluna(swap_amount, False)} USTC for LUNC')

                            # Set up the basic swap object
                            swaps_tx = wallet.swap().create()

                            # Populate the basic details.
                            swaps_tx.swap_amount = swap_amount
                            swaps_tx.swap_denom  = 'uusd'
                            swaps_tx.contract    = ASTROPORT_UUSD_TO_ULUNA_ADDRESS

                            # Simulate it so we can get the fee
                            result = swaps_tx.simulate()

                            if result == True:
                            
                                print (swaps_tx.readableFee())
                                
                                result = swaps_tx.swap()

                                if result == True:
                                    swaps_tx.broadcast()

                                    if swaps_tx.broadcast_result.code == 11:
                                        while True:
                                            print (' 🛎️  Increasing the gas adjustment fee and trying again')
                                            swaps_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
                                            print (f' 🛎️  Gas adjustment value is now {swaps_tx.terra.gas_adjustment}')
                                            swaps_tx.simulate()
                                            print (swaps_tx.readableFee())
                                            swaps_tx.swap()
                                            swaps_tx.broadcast()

                                            if swaps_tx.broadcast_result is None:
                                                break

                                            if swaps_tx.broadcast_result.code != 11:
                                                break

                                            if swaps_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
                                                break
                                            
                                    if swaps_tx.broadcast_result.is_tx_error():
                                        print (' 🛎️ The swap failed, an error occurred:')
                                        print (f' 🛎️  {swaps_tx.broadcast_result.raw_log}')
                                
                                    else:
                                        print (f' ✅ Swap successfully completed')
                                        print (f' ✅ Tx Hash: {swaps_tx.broadcast_result.txhash}')
                                else:
                                    print (' 🛎️  Swap transaction could not be completed')
                        else:
                            print (' 🛎️  Swap amount is not greater than zero')
                    else:
                        print (' 🛎️  No UST in the wallet to swap!')
                else:
                    print ('\n------------------------------------')
                    print ('Swaps not allowed on this wallet')

            # Redelegate anything we might have
            if user_action in [USER_ACTION_DELEGATE, USER_ACTION_WITHDRAW_DELEGATE, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:
                
                # Only delegate if the wallet is configured for delegations
                if 'delegate' in wallet.delegations:       

                    print ('\n------------------------------------')
                    print ('Starting delegations...')

                    # Update the balances after having done withdrawals and swaps
                    wallet.getBalances(True)

                    if 'uluna' in wallet.balances:     

                        # Figure out how much to delegate based on the user settings
                        uluna_balance = int(wallet.balances['uluna'])
                        
                        if isPercentage(wallet.delegations['delegate']):
                            percentage:int = int(str(wallet.delegations['delegate']).strip(' ')[0:-1]) / 100
                            delegated_uluna:int = int(uluna_balance * percentage)
                        else:
                            delegated_uluna:int = int(str(wallet.delegations['delegate']).strip(' '))

                        # Adjust this so we have the desired amount still remaining
                        delegated_uluna = int(delegated_uluna - ((WITHDRAWAL_REMAINDER) * COIN_DIVISOR))

                        if delegated_uluna > 0 and delegated_uluna <= wallet.balances['uluna']:
                            print (f'Delegating {wallet.formatUluna(delegated_uluna, True)}')

                            # Create the delegation object
                            delegation_tx = wallet.delegate().create()

                            # Assign the details:
                            delegation_tx.delegator_address = delegations[validator]['delegator']
                            delegation_tx.validator_address = delegations[validator]['validator']
                            delegation_tx.delegated_uluna   = delegated_uluna

                            # Simulate it
                            result = delegation_tx.simulate(delegation_tx.delegate)

                            if result == True:
                                    
                                print (delegation_tx.readableFee())
                                
                                # Now we know what the fee is, we can do it again and finalise it
                                result = delegation_tx.delegate()
                                
                                if result == True:
                                    delegation_tx.broadcast()

                                    if delegation_tx.broadcast_result.code == 11:
                                        while True:
                                            print (' 🛎️  Increasing the gas adjustment fee and trying again')
                                            delegation_tx.terra.gas_adjustment += GAS_ADJUSTMENT_INCREMENT
                                            print (f' 🛎️  Gas adjustment value is now {delegation_tx.terra.gas_adjustment}')
                                            delegation_tx.simulate(delegation_tx.delegate)
                                            print (delegation_tx.readableFee())
                                            delegation_tx.delegate()
                                            delegation_tx.broadcast()

                                            if delegation_tx.broadcast_result is None:
                                                break

                                            if delegation_tx.broadcast_result.code != 11:
                                                break

                                            if delegation_tx.terra.gas_adjustment >= MAX_GAS_ADJUSTMENT:
                                                break
                                        
                                    if delegation_tx.broadcast_result.is_tx_error():
                                        print (' 🛎️ The delegation failed, an error occurred:')
                                        print (f' 🛎️  {delegation_tx.broadcast_result.raw_log}')
                                    else:
                                        print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                                        print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
                                else:
                                    print (' 🛎️  The delegation could not be completed')
                            else:
                                print ('🛎️  The delegation could not be completed')
                        else:
                            if delegated_uluna <= 0:
                                print (' 🛎️  Delegation error: the delegated amount is not greater than zero')
                            else:
                                print (f' 🛎️  Delegation error: the delegated amount of {wallet.formatUluna(delegated_uluna, True)} exceeds the available amount of {wallet.formatUluna(uluna_balance, True)}')
                    else:
                        print (' 🛎️  No LUNC to delegate!')
                else:
                    print ('This wallet is not configured for delegations')

            print (' 💯 All actions on this validator are complete.')
            print ('------------------------------------')

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()