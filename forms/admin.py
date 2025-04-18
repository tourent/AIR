"""
Admin form definitions for the Solana Airdrop Bot web interface.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError, URL
from utils import validate_solana_address

class SolanaConfigForm(FlaskForm):
    """Solana configuration form"""
    spl_token_mint = StringField('SPL Token Mint Address', validators=[DataRequired(), Length(min=32, max=44)])
    spl_token_amount = FloatField('Default Token Amount', validators=[DataRequired(), NumberRange(min=0)])
    spl_token_decimals = IntegerField('Token Decimals', validators=[DataRequired(), NumberRange(min=0, max=9)])
    solana_rpc = StringField('Solana RPC URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Update Solana Config')
    
    def validate_spl_token_mint(self, spl_token_mint):
        """Validate SPL token mint address format"""
        if not validate_solana_address(spl_token_mint.data):
            raise ValidationError('Invalid SPL token mint address format.')

class TelegramConfigForm(FlaskForm):
    """Telegram bot configuration form"""
    bot_username = StringField('Bot Username', validators=[DataRequired(), Length(min=5)])
    admin_user_ids = StringField('Admin User IDs (comma-separated)', validators=[DataRequired()])
    submit = SubmitField('Update Telegram Config')

class AirdropForm(FlaskForm):
    """Form for starting an airdrop"""
    token_mint = StringField('Token Mint Address', validators=[DataRequired(), Length(min=32, max=44)])
    amount = FloatField('Amount Per Wallet', validators=[DataRequired(), NumberRange(min=0)])
    decimals = IntegerField('Token Decimals', validators=[DataRequired(), NumberRange(min=0, max=9)])
    message = TextAreaField('Airdrop Message (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Start Airdrop')
    
    def validate_token_mint(self, token_mint):
        """Validate token mint address format"""
        if not validate_solana_address(token_mint.data):
            raise ValidationError('Invalid token mint address format.')
