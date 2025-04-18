"""
Database models for the Solana Airdrop Bot
"""
from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from utils import validate_solana_address, format_solana_address

class User(UserMixin, db.Model):
    """User model for authentication and admin management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    telegram_id = db.Column(db.String(64), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with wallet addresses
    wallet_addresses = db.relationship('WalletAddress', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password against stored hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class WalletAddress(db.Model):
    """Solana wallet address model"""
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(44), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    label = db.Column(db.String(64), nullable=True)
    is_validated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, address, user_id, label=None):
        """Initialize wallet address with validation"""
        self.address = address
        self.user_id = user_id
        self.label = label
        
        # Validate address on creation
        if validate_solana_address(address):
            self.is_validated = True
            
    @property
    def formatted_address(self):
        """Return formatted address for display"""
        return format_solana_address(self.address)
    
    def __repr__(self):
        return f'<WalletAddress {self.formatted_address}>'

class AirdropEvent(db.Model):
    """Model for tracking airdrop events"""
    id = db.Column(db.Integer, primary_key=True)
    token_mint = db.Column(db.String(44), nullable=False)
    token_amount = db.Column(db.Float, nullable=False)
    token_decimals = db.Column(db.Integer, default=0)
    started_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with transaction records
    transactions = db.relationship('AirdropTransaction', backref='event', lazy=True)
    
    @property
    def success_count(self):
        """Count successful transactions"""
        return sum(1 for tx in self.transactions if tx.status == 'success')
    
    @property
    def failure_count(self):
        """Count failed transactions"""
        return sum(1 for tx in self.transactions if tx.status == 'failed')
    
    @property
    def pending_count(self):
        """Count pending transactions"""
        return sum(1 for tx in self.transactions if tx.status == 'pending')
        
    def __repr__(self):
        return f'<AirdropEvent {self.id} - {self.token_mint}>'

class AirdropTransaction(db.Model):
    """Model for tracking individual airdrop transactions"""
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('airdrop_event.id'), nullable=False)
    wallet_address = db.Column(db.String(44), nullable=False)
    transaction_signature = db.Column(db.String(90), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<AirdropTransaction {self.status} - {self.wallet_address}>'
