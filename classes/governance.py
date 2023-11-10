#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json

from constants.constants import (
    CHAIN_DATA,
    GAS_ADJUSTMENT,
    MAX_VALIDATOR_COUNT,
    ULUNA,
    USER_ACTION_QUIT,
    PROPOSAL_STATUS_VOTING_PERIOD
    
)

from classes.wallet import UserWallet
from classes.terra_instance import TerraInstance
from classes.transaction_core import TransactionCore

from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.params import PaginationOptions
from terra_classic_sdk.core.gov import MsgVote, Proposal
from terra_classic_sdk.key.mnemonic import MnemonicKey
from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.core.broadcast import (
    BlockTxBroadcastResult,
    TxLog
)
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.fee import Fee

class Governance(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(Governance, self).__init__(*args, **kwargs)

        self.account_number:int = None
        self.address:str        = None
        self.fee:Fee            = None
        self.gas_list:json      = None
        self.gas_limit:str      = 'auto'
        self.proposal_id:int    = None
        self.terra:LCDClient    = None
        self.user_vote:int      = None
        self.sequence:int       = None

    def create(self):
        """
        Create a basic terra LCDClient object
        """

        # Defaults to uluna/terra
        self.terra = TerraInstance().create()

        return self
    
    def getUserSingleChoice(self, question:str):
        """
        Get a single user selection from a list.
        This is a custom function because the options are specific to this list.
        """

        # Get the active proposals:
        proposals:dict = self.proposals()

        # Get the longest proposal name:
        label_widths:list = []

        label_widths.append(len('Number'))
        label_widths.append(len('ID'))
        label_widths.append(len('Title'))
        
        for proposal in proposals:
            if len(str(proposal['id'])) > label_widths[1]:
                label_widths[1] = len(str(proposal['id']))

        for proposal in proposals:
            if len(str(proposal['title'])) > label_widths[2]:
                label_widths[2] = len(str(proposal['title']))

        padding_str:str   = ' ' * 100
        header_string:str = ' Number'
        # Add the other columns to the header string
        header_string += ' | ID' + padding_str[0:label_widths[1] - len('ID')]
        header_string += ' | Title' + padding_str[0:label_widths[2] - len('Title')]

        horizontal_spacer:str = '-' * (len(header_string) + 2)

        proposal_to_use:int = 0
        while True:
            count:int = 0

            print (horizontal_spacer)
            print (header_string)
            print (horizontal_spacer)

            for proposal in proposals:
                count += 1
                
                glyph:str = '  '
                if count == proposal_to_use:
                    glyph = '✅'
                
                count_str:str          =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
                proposal_id_str:str    = str(proposal['id']) + padding_str[0:label_widths[1] - len(str(proposal['id']))]
                proposal_title_str:str = proposal['title'] + padding_str[0:label_widths[2] - len(proposal['title'])]
                
                print (f"{count_str}{glyph} | {proposal_id_str} | {proposal_title_str}")

            print (horizontal_spacer + '\n')

            answer:str = input(question).lower()
            
            if answer.isdigit() and (0 < int(answer) < (len(proposals) + 1)):
                proposal_to_use = int(answer)

            if answer == 'x':
                if proposal_to_use > 0:
                    break
                else:
                    print ('\nPlease select a proposal first.\n')

            if answer == USER_ACTION_QUIT:
                break

        return proposals[proposal_to_use - 1], answer
    
    # def proposal(self, proposal_id:int) -> dict:
    #     """
    #     Get the details of the supplied proposal ID
    #     """

    #     proposal = self.terra.gov.proposal(proposal_id)

    #     print (self.terra.gov.tally(proposal_id))

    #     self.terra.gov.votes()

    #     #print (self.terra.gov.votes(10983))

    def proposals(self) -> list:
        """
        Create a dictionary of all the active proposals
        """
        
        proposal_list:list = []
        
        # The parameters we pass. You can do pagination & filters at the same time apparently.
        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        proposal_params:dict     = {'proposal_status': PROPOSAL_STATUS_VOTING_PERIOD}

        # Pass the parameters in the correct order:
        result, pagination = self.terra.gov.proposals(proposal_params, pagOpt)

        proposal:Proposal
        for proposal in result:
            if type(proposal) == Proposal:
                proposal_list.append({'id': proposal.proposal_id, 'title': proposal.content.title, 'content': proposal.content.description, 'voting_start': proposal.voting_start_time, 'voting_end': proposal.voting_end_time})

        while pagination["next_key"] is not None:
            pagOpt              = PaginationOptions(key = pagination["next_key"])
            result, pagination  = self.terra.gov.proposals(proposal_params, pagOpt)
            for proposal in result:
                if type(proposal) == Proposal:
                    proposal_list.append({'id': proposal.proposal_id, 'title': proposal.content.title, 'content': proposal.content.description, 'voting_start': proposal.voting_start_time, 'voting_end': proposal.voting_end_time})

        return proposal_list
    
    def simulate(self):
        """
        Simulate a vote so we can get the fee details.
        """

        # Reset these values in case this is a re-used object:
        self.account_number:int = self.current_wallet.account_number()
        self.fee:Fee            = None
        self.gas_limit:str      = 'auto'
        self.sequence:int       = self.current_wallet.sequence()
        
        # Perform the swap as a simulation, with no fee details
        self.vote()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            self.fee = self.calculateFee(requested_fee = requested_fee, specific_denom = ULUNA)
            
            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom

            new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})
                
            requested_fee.amount = new_coin
            
            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            return True
        else:
            return False
        
    def update(self, seed:str):
        """
        Update this object with the wallet details that we want to cast votes on.
        This allows us to reuse the existing Terra connection.
        """

        # Create the wallet based on the calculated key
        prefix              = CHAIN_DATA[ULUNA]['bech32_prefix']
        current_wallet_key:MnemonicKey  = MnemonicKey(mnemonic = seed, prefix = prefix)
        self.current_wallet = self.terra.wallet(current_wallet_key)
        
        self.address = current_wallet_key.acc_address

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        #self.tax_rate = self.taxRate()

        return self
    
    def vote(self):

        #self.account_number:int = self.current_wallet.account_number()
        #self.sequence:int       = self.current_wallet.sequence()

        msg = MsgVote(
            proposal_id=self.proposal_id,
            voter=self.address,
            option=self.user_vote
        )
            
        options = CreateTxOptions(
            account_number = str(self.account_number),
            gas            = self.gas_limit,
            gas_prices     = self.gas_list,
            #gas_adjustment = int(GAS_ADJUSTMENT),
            fee            = self.fee,
            msgs           = [msg],
            sequence       = str(self.sequence)
        )

        # This process often generates sequence errors. If we get a response error, then
        # bump up the sequence number by one and try again.
        while True:
            try:
                tx:Tx = self.current_wallet.create_and_sign_tx(options)
                break
            except LCDResponseError as err:
                if 'account sequence mismatch' in err.message:
                    self.sequence    = self.sequence + 1
                    options.sequence = self.sequence
                    print (' 🛎️  Boosting sequence number')
                else:
                    print (' 🛑 An unexpected error occurred in the off-chain send function:')
                    print (err)
                    break
            except Exception as err:
                print (' 🛑 An unexpected error occurred in the off-chain send function:')
                print (err)
                break

        # Store the transaction
        self.transaction = tx

        print (self.transaction)

        return True