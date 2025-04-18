"""
Wallet management form definitions for the Solana Airdrop Bot web interface.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from utils import validate_solana_address

class WalletForm(FlaskForm):
    """Wallet address form"""
    address = StringField('Wallet Address', validators=[DataRequired(), Length(min=32, max=44)])
    label = StringField('Label (Optional)', validators=[Length(max=64)])
    submit = SubmitField('Add Wallet')
    
    def validate_address(self, address):
        """Validate Solana wallet address format"""
        if not validate_solana_address(address.data):
            raise ValidationError('Invalid Solana wallet address format.')

class SendTokensForm(FlaskForm):
    """Form for sending tokens to a wallet"""
    token_mint = StringField('Token Mint Address', validators=[DataRequired(), Length(min=32, max=44)])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    decimals = IntegerField('Token Decimals', validators=[DataRequired(), NumberRange(min=0, max=9)])
    submit = SubmitField('Send Tokens')
    
    def validate_token_mint(self, token_mint):
        """Validate token mint address format"""
        if not validate_solana_address(token_mint.data):
            raise ValidationError('Invalid token mint address format.')

class WithdrawTokensForm(FlaskForm):
    """Form for withdrawing tokens from a wallet with fee"""
    token_mint = StringField('Token Mint Address', validators=[DataRequired(), Length(min=32, max=44)])
    amount = FloatField('Amount to Withdraw', validators=[DataRequired(), NumberRange(min=0.001)])
    decimals = IntegerField('Token Decimals', validators=[DataRequired(), NumberRange(min=0, max=9)])
    destination_address = StringField('Destination Wallet Address', validators=[DataRequired(), Length(min=32, max=44)])
    fee_percentage = FloatField('Fee Percentage', default=0.05, validators=[NumberRange(min=0.01, max=0.15)])
    wallet_id = HiddenField()
    submit = SubmitField('Withdraw Tokens')
    
    def validate_token_mint(self, token_mint):
        """Validate token mint address format"""
        if not validate_solana_address(token_mint.data):
            raise ValidationError('Invalid token mint address format.')
            
    def validate_destination_address(self, destination_address):
        """Validate destination wallet address format"""
        if not validate_solana_address(destination_address.data):
            raise ValidationError('Invalid destination wallet address format.')
