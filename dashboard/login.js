/**
 * Athena SCIP - Login Page Logic
 */

// Use window objects - NO DECLARATIONS
const supabaseClient = window.supabaseClient;

let isSignupMode = false;

const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const toggleAction = document.getElementById('toggleAction');
const backToLoginBtn = document.getElementById('backToLoginBtn');
const messageDiv = document.getElementById('message');
const infoBox = document.getElementById('infoBox');
const loginBtn = document.getElementById('loginBtn');
const signupBtn = document.getElementById('signupBtn');

function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = 'message ' + type;
}

function hideMessage() {
    messageDiv.className = 'message';
    messageDiv.textContent = '';
}

function toggleMode() {
    isSignupMode = !isSignupMode;
    if (isSignupMode) {
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
        toggleAction.textContent = '← Back to Login';
        if (infoBox) infoBox.classList.add('show');
        hideMessage();
    } else {
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
        toggleAction.textContent = 'Create an account';
        if (infoBox) infoBox.classList.remove('show');
        hideMessage();
    }
}

if (toggleAction) toggleAction.addEventListener('click', toggleMode);
if (backToLoginBtn) backToLoginBtn.addEventListener('click', toggleMode);

// LOGIN
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideMessage();

        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        if (!email || !password) {
            showMessage('Please enter both email and password.', 'error');
            return;
        }

        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="loading-spinner"></span> Logging in...';

        try {
            const { data, error } = await supabaseClient.auth.signInWithPassword({
                email: email,
                password: password
            });

            if (error) {
                let errorMsg = error.message;
                if (error.message.includes('Invalid login credentials')) {
                    errorMsg = '❌ Invalid email or password. Please check and try again.';
                } else if (error.message.includes('Email not confirmed')) {
                    errorMsg = '❌ Please confirm your email first. Check your inbox for the confirmation link.';
                }
                showMessage(errorMsg, 'error');
            } else {
                showMessage('✅ Login successful! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            }
        } catch (err) {
            console.error('❌ Login error:', err);
            showMessage('An unexpected error occurred. Please try again.', 'error');
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    });
}

// SIGNUP
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideMessage();

        const email = document.getElementById('signupEmail').value.trim();
        const password = document.getElementById('signupPassword').value;

        if (!email || !password) {
            showMessage('Please enter both email and password.', 'error');
            return;
        }

        if (password.length < 8) {
            showMessage('Password must be at least 8 characters.', 'error');
            return;
        }

        signupBtn.disabled = true;
        signupBtn.innerHTML = '<span class="loading-spinner"></span> Creating account...';

        try {
            const { data, error } = await supabaseClient.auth.signUp({
                email: email,
                password: password,
                options: {
                    emailRedirectTo: window.location.origin + '/secure-login.html'
                }
            });

            if (error) {
                showMessage('❌ ' + error.message, 'error');
            } else if (data.user) {
                showMessage('✅ Account created! Check your email (including spam) for confirmation link.', 'success');
                setTimeout(() => {
                    toggleMode();
                    document.getElementById('email').value = email;
                }, 4000);
            } else {
                showMessage('✅ Account created! Please check your email for confirmation.', 'success');
            }
        } catch (err) {
            console.error('❌ Signup error:', err);
            showMessage('An unexpected error occurred. Please try again.', 'error');
        } finally {
            signupBtn.disabled = false;
            signupBtn.textContent = 'Create Account';
        }
    });
}

// Check if already logged in
async function checkSession() {
    try {
        const { data: { session } } = await supabaseClient.auth.getSession();
        if (session) {
            window.location.href = 'index.html';
        }
    } catch (err) {
        console.error('Session check error:', err);
    }
}
checkSession();