"""
Route definitions for the Solana Airdrop Bot web interface
"""
import os
import uuid
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, WalletAddress, AirdropEvent, AirdropTransaction
from app import db
import logging
import config
from datetime import datetime
from forms.auth import LoginForm, AdminLoginForm, RegistrationForm
from forms.wallet import WalletForm, SendTokensForm, WithdrawTokensForm
from forms.admin import SolanaConfigForm, TelegramConfigForm, AirdropForm

# Configure logging
logger = logging.getLogger(__name__)

# Initialize login manager
login_manager = LoginManager()

def register_routes(app):
    """Register all routes with the Flask application"""
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Home/Landing page
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data if hasattr(form, 'remember_me') else False)
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
                
        return render_template('auth/login.html', form=form)
    
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Admin login with fixed credentials"""
        if current_user.is_authenticated and current_user.is_admin:
            return redirect(url_for('admin_airdrops'))
        
        form = AdminLoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            
            # Fixed admin credentials
            if username == "admin" and password == "798521346":
                # Look for an existing admin account or create one
                admin = User.query.filter_by(username="admin").first()
                
                if not admin:
                    # Create the admin account with fixed credentials
                    admin = User(
                        username="admin",
                        email="admin@example.com",
                        is_admin=True
                    )
                    # Set the provided password
                    admin.set_password("798521346")
                    db.session.add(admin)
                    db.session.commit()
                elif not admin.is_admin:
                    # Ensure the admin flag is set
                    admin.is_admin = True
                    db.session.commit()
                
                login_user(admin)
                flash('Admin access granted!', 'success')
                return redirect(url_for('admin_airdrops'))
            else:
                flash('Invalid admin credentials', 'danger')
        
        return render_template('auth/admin_login.html', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            # Create new user
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            
            # First user becomes admin
            if User.query.count() == 0:
                user.is_admin = True
                
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('auth/register.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    # User dashboard
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get user's wallet addresses
        wallets = WalletAddress.query.filter_by(user_id=current_user.id).all()
        
        # For admins, get recent airdrop events
        recent_airdrops = []
        if current_user.is_admin:
            recent_airdrops = AirdropEvent.query.order_by(
                AirdropEvent.created_at.desc()
            ).limit(5).all()
        
        return render_template(
            'dashboard.html', 
            wallets=wallets,
            recent_airdrops=recent_airdrops
        )
    
    # Wallet management
    @app.route('/wallets', methods=['GET'])
    @login_required
    def wallets():
        user_wallets = WalletAddress.query.filter_by(user_id=current_user.id).all()
        return render_template('wallets/list.html', wallets=user_wallets)
    
    @app.route('/wallets/add', methods=['GET', 'POST'])
    @login_required
    def add_wallet():
        form = WalletForm()
        if form.validate_on_submit():
            address = form.address.data
            label = form.label.data
            
            # Validate address format
            from utils import validate_solana_address
            if address and not validate_solana_address(address):
                flash('Invalid Solana wallet address', 'danger')
                return render_template('wallets/add.html', form=form)
            
            # Check if wallet already exists for this user
            existing_wallet = WalletAddress.query.filter_by(
                address=address,
                user_id=current_user.id
            ).first()
            
            if existing_wallet:
                flash('This wallet address is already registered', 'warning')
                return redirect(url_for('wallets'))
            
            # Create new wallet
            wallet = WalletAddress(
                address=address,
                user_id=current_user.id,
                label=label
            )
            
            db.session.add(wallet)
            db.session.commit()
            
            flash('Wallet address added successfully', 'success')
            return redirect(url_for('wallets'))
            
        return render_template('wallets/add.html', form=form)
    
    @app.route('/wallets/<int:wallet_id>/delete', methods=['POST'])
    @login_required
    def delete_wallet(wallet_id):
        wallet = WalletAddress.query.get_or_404(wallet_id)
        
        # Ensure user owns this wallet
        if wallet.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('wallets'))
        
        db.session.delete(wallet)
        db.session.commit()
        
        flash('Wallet address deleted', 'success')
        return redirect(url_for('wallets'))
        
    @app.route('/wallets/<int:wallet_id>/send', methods=['GET', 'POST'])
    @login_required
    def send_tokens(wallet_id):
        wallet = WalletAddress.query.get_or_404(wallet_id)
        
        # Ensure user owns this wallet
        if wallet.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('wallets'))
        
        # Initialize the form
        form = SendTokensForm()
        
        if form.validate_on_submit():
            token_mint = form.token_mint.data
            amount = form.amount.data
            decimals = form.decimals.data
            
            # Validate sender wallet is configured
            if not config.SENDER_SECRET_KEY:
                flash('Sender wallet not configured. Cannot send tokens.', 'danger')
                return render_template('wallets/send_tokens.html', wallet=wallet, form=form)
            
            try:
                # Process the token transaction
                # Use original format string if available, otherwise fall back to parsed version
                sender_key = config.SENDER_SECRET_KEY_ORIGINAL or config.SENDER_SECRET_KEY
                
                # Import here to avoid circular import
                from utils import process_airdrop_transaction
                import asyncio
                
                # Ensure all parameters are not None with defaults
                safe_token_mint = token_mint or config.SPL_TOKEN_MINT
                safe_amount = amount if amount is not None else config.SPL_TOKEN_AMOUNT
                safe_decimals = decimals if decimals is not None else config.SPL_TOKEN_DECIMALS

                # Run the async transaction in the synchronous Flask context
                result = asyncio.run(process_airdrop_transaction(
                    wallet_address=wallet.address,
                    token_mint=safe_token_mint,
                    token_amount=float(safe_amount),
                    token_decimals=int(safe_decimals),
                    sender_secret_key=sender_key
                ))
                
                if result['success']:
                    # Create a record of the transaction
                    airdrop = AirdropEvent(
                        token_mint=token_mint,
                        token_amount=amount,
                        token_decimals=decimals,
                        started_by=current_user.id
                    )
                    db.session.add(airdrop)
                    db.session.commit()
                    
                    # Create transaction record
                    transaction = AirdropTransaction(
                        event_id=airdrop.id,
                        wallet_address=wallet.address,
                        transaction_signature=result['signature'],
                        status='success',
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(transaction)
                    db.session.commit()
                    
                    flash(f'Successfully sent {amount} tokens to your wallet!', 'success')
                    return redirect(url_for('wallets'))
                else:
                    flash(f'Failed to send tokens: {result["error"]}', 'danger')
            except Exception as e:
                flash(f'Error sending tokens: {str(e)}', 'danger')
                logger.exception("Error sending tokens")
                
        return render_template('wallets/send_tokens.html', wallet=wallet, form=form)
    
    # Admin routes
    @app.route('/admin/users', methods=['GET', 'POST'])
    @login_required
    def admin_users():
        # Ensure user is admin
        if not current_user.is_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        
        # Handle POST actions (e.g., toggle admin)
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'toggle_admin':
                user_id = request.form.get('user_id')
                user = User.query.get_or_404(int(user_id))
                
                # Don't allow removing admin from yourself
                if user.id == current_user.id:
                    flash('You cannot remove admin privileges from yourself.', 'danger')
                else:
                    user.is_admin = not user.is_admin
                    db.session.commit()
                    flash(f'{"Admin privileges granted to" if user.is_admin else "Admin privileges removed from"} {user.username}.', 'success')
                
                return redirect(url_for('admin_users'))
        
        users = User.query.all()
        return render_template('admin/users.html', users=users)
    
    @app.route('/admin/airdrops', methods=['GET', 'POST'])
    @login_required
    def admin_airdrops():
        # Ensure user is admin
        if not current_user.is_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        
        # Handle POST request (new airdrop)
        if request.method == 'POST':
            token_mint = request.form.get('token_mint', config.SPL_TOKEN_MINT)
            amount = float(request.form.get('amount', config.SPL_TOKEN_AMOUNT))
            decimals = int(request.form.get('decimals', config.SPL_TOKEN_DECIMALS))
            message = request.form.get('message', '')
            
            # Validate sender wallet is configured
            if not config.SENDER_SECRET_KEY:
                flash('Sender wallet not configured. Cannot start airdrop.', 'danger')
                return redirect(url_for('admin_airdrops'))
            
            # Get all registered wallets
            wallets = WalletAddress.query.all()
            
            if not wallets:
                flash('No wallets registered for airdrop.', 'warning')
                return redirect(url_for('admin_airdrops'))
            
            # Create airdrop event
            airdrop = AirdropEvent(
                token_mint=token_mint,
                token_amount=amount,
                token_decimals=decimals,
                started_by=current_user.id
            )
            db.session.add(airdrop)
            db.session.commit()
            
            # Start airdrop processing in background
            import threading
            from utils import process_airdrop_transaction
            import asyncio
            
            def process_airdrops():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                for wallet in wallets:
                    # Create transaction record
                    transaction = AirdropTransaction(
                        event_id=airdrop.id,
                        wallet_address=wallet.address,
                        status='pending'
                    )
                    db.session.add(transaction)
                    db.session.commit()
                    
                    # Process transaction
                    try:
                        # Ensure all parameters are not None with defaults
                        safe_token_mint = token_mint or config.SPL_TOKEN_MINT
                        safe_amount = amount if amount is not None else config.SPL_TOKEN_AMOUNT
                        safe_decimals = decimals if decimals is not None else config.SPL_TOKEN_DECIMALS
                        
                        result = loop.run_until_complete(process_airdrop_transaction(
                            wallet_address=wallet.address,
                            token_mint=safe_token_mint,
                            token_amount=float(safe_amount),
                            token_decimals=int(safe_decimals),
                            sender_secret_key=config.SENDER_SECRET_KEY
                        ))
                        
                        # Update transaction record
                        transaction.status = 'success' if result['success'] else 'failed'
                        transaction.transaction_signature = result.get('signature', None)
                        transaction.error_message = result.get('error', None)
                        transaction.completed_at = datetime.utcnow()
                        db.session.commit()
                        
                    except Exception as e:
                        logger.error(f"Error processing airdrop to {wallet.address}: {e}")
                        transaction.status = 'failed'
                        transaction.error_message = str(e)
                        transaction.completed_at = datetime.utcnow()
                        db.session.commit()
                
                logger.info(f"Airdrop {airdrop.id} completed")
                
            # Start processing in a background thread
            thread = threading.Thread(target=process_airdrops)
            thread.daemon = True
            thread.start()
            
            flash(f'Started airdrop of {amount} tokens to {len(wallets)} wallets.', 'success')
            return redirect(url_for('admin_airdrops'))
        
        airdrops = AirdropEvent.query.order_by(AirdropEvent.created_at.desc()).all()
        form = AirdropForm(
            token_mint=config.SPL_TOKEN_MINT,
            amount=config.SPL_TOKEN_AMOUNT,
            decimals=config.SPL_TOKEN_DECIMALS
        )
        return render_template('admin/airdrops.html', airdrops=airdrops, form=form)
    
    @app.route('/admin/settings', methods=['GET'])
    @login_required
    def admin_settings():
        # Ensure user is admin
        if not current_user.is_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        
        # Initialize the forms with current values for editing
        solana_form = SolanaConfigForm(
            spl_token_mint=config.SPL_TOKEN_MINT,
            spl_token_amount=config.SPL_TOKEN_AMOUNT,
            spl_token_decimals=config.SPL_TOKEN_DECIMALS,
            solana_rpc=config.SOLANA_RPC
        )
        
        # Initialize the telegram form
        telegram_form = TelegramConfigForm(
            bot_username=config.BOT_USERNAME,
            admin_user_ids=','.join(config.ADMIN_USER_IDS) if isinstance(config.ADMIN_USER_IDS, list) else config.ADMIN_USER_IDS
        )
        
        return render_template('admin/settings.html', 
                               solana_form=solana_form,
                               telegram_form=telegram_form)
    
    @app.route('/admin/settings/solana', methods=['POST'])
    @login_required
    def admin_update_solana_config():
        # Ensure user is admin
        if not current_user.is_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        
        # Initialize the form with the submitted data
        solana_form = SolanaConfigForm()
        
        if solana_form.validate_on_submit():
            # Update the configuration values
            updates = {
                "SPL_TOKEN_MINT": solana_form.spl_token_mint.data,
                "SPL_TOKEN_AMOUNT": solana_form.spl_token_amount.data,
                "SPL_TOKEN_DECIMALS": solana_form.spl_token_decimals.data,
                "SOLANA_RPC": solana_form.solana_rpc.data
            }
            
            # Use the config module's update_config function to update and save
            config.update_config(updates)
            
            flash('Solana configuration updated successfully', 'success')
        else:
            for field, errors in solana_form.errors.items():
                for error in errors:
                    flash(f'{getattr(solana_form, field).label.text}: {error}', 'danger')
        
        return redirect(url_for('admin_settings'))
        
    @app.route('/admin/settings/telegram', methods=['POST'])
    @login_required
    def admin_update_telegram_config():
        # Ensure user is admin
        if not current_user.is_admin:
            flash('Access denied', 'danger')
            return redirect(url_for('dashboard'))
        
        # Initialize the form with the submitted data
        telegram_form = TelegramConfigForm()
        
        if telegram_form.validate_on_submit():
            # Update the configuration values
            updates = {
                "BOT_USERNAME": telegram_form.bot_username.data,
                "ADMIN_USER_IDS": telegram_form.admin_user_ids.data
            }
            
            # Use the config module's update_config function to update and save
            config.update_config(updates)
            
            flash('Telegram configuration updated successfully', 'success')
        else:
            for field, errors in telegram_form.errors.items():
                for error in errors:
                    flash(f'{getattr(telegram_form, field).label.text}: {error}', 'danger')
        
        return redirect(url_for('admin_settings'))
    
    # API endpoints
    @app.route('/api/airdrops/<int:airdrop_id>/status')
    @login_required
    def airdrop_status(airdrop_id):
        """Get the status of an airdrop"""
        airdrop = AirdropEvent.query.get_or_404(airdrop_id)
        
        # Ensure user is admin or is the one who started the airdrop
        if not current_user.is_admin and airdrop.started_by != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        transactions = AirdropTransaction.query.filter_by(event_id=airdrop_id).all()
        total = len(transactions)
        completed = sum(1 for tx in transactions if tx.status != 'pending')
        success = sum(1 for tx in transactions if tx.status == 'success')
        failed = sum(1 for tx in transactions if tx.status == 'failed')
        
        status = 'completed' if completed == total else 'in_progress'
        
        return jsonify({
            'airdrop_id': airdrop_id,
            'total': total,
            'completed': completed,
            'success': success,
            'failed': failed,
            'status': status,
            'progress_percentage': (completed / total * 100) if total > 0 else 0
        })
        
    # Wallet withdrawal functionality
    @app.route('/wallets/<int:wallet_id>/withdraw', methods=['GET', 'POST'])
    @login_required
    def withdraw_tokens(wallet_id):
        """Process a withdrawal request with fee"""
        wallet = WalletAddress.query.get_or_404(wallet_id)
        
        # Ensure user owns this wallet
        if wallet.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('wallets'))
        
        # Initialize the withdrawal form
        form = WithdrawTokensForm(wallet_id=wallet_id)
        
        # Pre-populate form with default values
        if request.method == 'GET':
            form.token_mint.data = config.SPL_TOKEN_MINT
            form.decimals.data = config.SPL_TOKEN_DECIMALS
            form.destination_address.data = config.SENDER_SECRET_KEY_ORIGINAL.split(':')[0] if ':' in config.SENDER_SECRET_KEY_ORIGINAL else ''
        
        if form.validate_on_submit():
            token_mint = form.token_mint.data
            amount = form.amount.data
            decimals = form.decimals.data
            destination_address = form.destination_address.data
            fee_percentage = form.fee_percentage.data
            
            # Add logger for debugging
            logger.debug(f"Form data: token_mint={token_mint}, amount={amount}, decimals={decimals}, destination={destination_address}, fee={fee_percentage}")
            
            try:
                # Import here to avoid circular import
                from utils import process_withdrawal_transaction
                import asyncio
                
                # Ensure all parameters are not None with defaults
                safe_token_mint = token_mint or config.SPL_TOKEN_MINT
                safe_amount = amount if amount is not None else 0.0
                safe_decimals = decimals if decimals is not None else config.SPL_TOKEN_DECIMALS
                safe_fee_percentage = fee_percentage if fee_percentage is not None else 0.05
                
                # Run the async transaction in the synchronous Flask context
                result = asyncio.run(process_withdrawal_transaction(
                    wallet_address=wallet.address,
                    token_mint=safe_token_mint,
                    token_amount=float(safe_amount),
                    token_decimals=int(safe_decimals),
                    fee_percentage=float(safe_fee_percentage),
                    receiver_secret_key=config.SENDER_SECRET_KEY
                ))
                
                if result['success']:
                    # Get values from the result or calculate them if not provided
                    fee_amount = result.get('fee_amount', float(safe_amount) * float(safe_fee_percentage))
                    net_amount = result.get('net_amount', float(safe_amount) - float(fee_amount))
                    
                    # Log transaction details
                    logger.info(f"Withdrawal processed: {safe_amount} tokens from {wallet.address} with {float(safe_fee_percentage)*100}% fee")
                    logger.info(f"Fee: {fee_amount}, Net amount: {net_amount}, Transaction: {result['signature']}")
                    
                    flash(f'Successfully withdrew {safe_amount} tokens with a fee of {fee_amount} tokens!', 'success')
                    return redirect(url_for('wallets'))
                else:
                    flash(f'Failed to process withdrawal: {result["error"]}', 'danger')
            except Exception as e:
                flash(f'Error processing withdrawal: {str(e)}', 'danger')
                logger.exception("Error processing withdrawal")
        
        return render_template('wallets/withdraw_tokens.html', wallet=wallet, form=form)
