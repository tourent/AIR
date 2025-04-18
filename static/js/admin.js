/**
 * Admin functionality for the Solana Airdrop Bot dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Process airdrop button functionality
    const processButtons = document.querySelectorAll('.process-airdrop-btn');
    
    if (processButtons) {
        processButtons.forEach(button => {
            button.addEventListener('click', async function(e) {
                e.preventDefault();
                
                const airdropId = this.getAttribute('data-airdrop-id');
                const confirmMsg = 'Are you sure you want to process this airdrop? This will send tokens to all registered wallets.';
                
                if (confirm(confirmMsg)) {
                    try {
                        // Set button to loading state
                        this.disabled = true;
                        this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Processing...';
                        
                        // Make API request to process airdrop
                        const response = await fetch(`/api/airdrop/${airdropId}/process`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            // Show success message
                            alert('Airdrop process started successfully!');
                            // Reload page to see updated status
                            window.location.reload();
                        } else {
                            // Show error message
                            alert(`Error: ${data.error || 'Failed to process airdrop'}`);
                            // Reset button
                            this.disabled = false;
                            this.innerHTML = '<i class="fas fa-paper-plane me-2"></i> Process Airdrop';
                        }
                    } catch (error) {
                        console.error('Error processing airdrop:', error);
                        alert('An error occurred while processing the airdrop.');
                        // Reset button
                        this.disabled = false;
                        this.innerHTML = '<i class="fas fa-paper-plane me-2"></i> Process Airdrop';
                    }
                }
            });
        });
    }
    
    // Admin login button highlight effect
    const adminLoginBtn = document.querySelector('a[href*="admin_login"]');
    if (adminLoginBtn) {
        adminLoginBtn.addEventListener('mouseenter', function() {
            this.classList.add('btn-secondary');
            this.classList.remove('btn-outline-secondary');
        });
        
        adminLoginBtn.addEventListener('mouseleave', function() {
            this.classList.add('btn-outline-secondary');
            this.classList.remove('btn-secondary');
        });
    }
});