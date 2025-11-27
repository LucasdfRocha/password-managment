// Globals and DOM references
const API_BASE = "http://localhost:8000/api";

let sessionToken = null;
let masterPasswordPlain = null;
let currentUserId = null;
let currentUsername = null;

const statusEl = document.getElementById('status');
const loginSection = document.getElementById('login-section');
const appSection = document.getElementById('app-section');

// Login form elements
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const btnLogin = document.getElementById('btn-login');
const btnToggleRegister = document.getElementById('btn-toggle-register');
const togglePasswordBtn = document.getElementById('toggle-password');

// Register form elements
const registerUsernameInput = document.getElementById('register-username');
const registerEmailInput = document.getElementById('register-email');
const registerPasswordInput = document.getElementById('register-password');
const btnRegister = document.getElementById('btn-register');
const btnToggleLogin = document.getElementById('btn-toggle-login');
const toggleRegisterPasswordBtn = document.getElementById('toggle-register-password');

const btnLogout = document.getElementById('btn-logout');
const currentUsernameSpan = document.getElementById('current-username');

const formCreatePassword = document.getElementById('form-create-password');
const tbodyPasswords = document.getElementById('passwords-table-body');
const searchInput = document.getElementById('search-passwords');
const emptyState = document.getElementById('empty-state');
const customPasswordInput = document.getElementById('custom-password');
const passwordStrengthBar = document.getElementById('password-strength-bar');
const passwordStrengthText = document.getElementById('password-strength-text');

const btnWalletExport = document.getElementById('btn-wallet-export');
const btnWalletImport = document.getElementById('btn-wallet-import');
const walletFileInput = document.getElementById('wallet-file-input');

let allPasswords = [];

// expose some globals explicitly for clarity
window.API_BASE = API_BASE;
window.sessionToken = sessionToken;
window.masterPasswordPlain = masterPasswordPlain;
window.allPasswords = allPasswords;
