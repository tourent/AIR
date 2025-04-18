/**
 * Main JavaScript for Solana Airdrop Bot
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Copy wallet address to clipboard
    const copyButtons = document.querySelectorAll('.copy-address');
    copyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const address = this.getAttribute('data-address');
            navigator.clipboard.writeText(address).then(() => {
                // Change button text temporarily
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="bi bi-check-circle"></i> Copied!';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    });

    // Handle airdrop progress updates if on the airdrop page
    const airdropProgress = document.getElementById('airdropProgress');
    if (airdropProgress) {
        updateAirdropProgress();
    }

    // Handle countdown timers
    const countdownElements = document.querySelectorAll('[data-countdown]');
    if (countdownElements.length > 0) {
        countdownElements.forEach(element => {
            updateCountdown(element);
            // Update every second
            setInterval(() => updateCountdown(element), 1000);
        });
    }
});

function updateCountdown(element) {
    const targetDate = new Date(element.getAttribute('data-countdown')).getTime();
    const now = new Date().getTime();
    const distance = targetDate - now;

    if (distance < 0) {
        element.innerHTML = 'Expired';
        return;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    element.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
}

function updateAirdropProgress() {
    const airdropId = document.getElementById('airdropProgress').getAttribute('data-airdrop-id');
    if (!airdropId) return;

    // Fetch the current progress
    fetch(`/api/airdrops/${airdropId}/status`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'completed') {
                document.getElementById('progressBar').style.width = '100%';
                document.getElementById('progressStatus').innerHTML = 'Completed';
                return;
            }

            const total = data.total || 0;
            const completed = data.completed || 0;
            const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

            document.getElementById('progressBar').style.width = `${percentage}%`;
            document.getElementById('progressStatus').innerHTML = 
                `${completed} of ${total} transactions (${percentage}%)`;

            // If not completed, check again in 3 seconds
            if (data.status !== 'completed') {
                setTimeout(updateAirdropProgress, 3000);
            }
        })
        .catch(error => {
            console.error('Error updating airdrop progress:', error);
            // Try again in 5 seconds on error
            setTimeout(updateAirdropProgress, 5000);
        });
}

// Confirmation dialogs
function confirmAction(message, formId) {
    if (confirm(message || 'Are you sure you want to perform this action?')) {
        document.getElementById(formId).submit();
    }
    return false;
}

// Toggle visibility of a DOM element
function toggleElement(id) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.toggle('d-none');
    }
}
