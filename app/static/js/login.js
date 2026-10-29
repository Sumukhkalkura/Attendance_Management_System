"use strict";

const form = document.getElementById("loginForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const loginButton = document.getElementById("loginButton");
const errorBox = document.getElementById("loginError");
const errorText = document.getElementById("loginErrorText");
const passwordToggle = document.getElementById("passwordToggle");

function showError(message) {
    errorText.textContent = message;
    errorBox.hidden = false;
}

passwordToggle.addEventListener("click", () => {
    const reveal = passwordInput.type === "password";
    passwordInput.type = reveal ? "text" : "password";
    passwordToggle.setAttribute("aria-pressed", String(reveal));
    passwordToggle.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
    document.getElementById("eyeShow").hidden = reveal;
    document.getElementById("eyeHide").hidden = !reveal;
    passwordInput.focus();
});

for (const input of [usernameInput, passwordInput]) {
    input.addEventListener("input", () => {
        input.removeAttribute("aria-invalid");
        errorBox.hidden = true;
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.hidden = true;

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    usernameInput.toggleAttribute("aria-invalid", !username);
    passwordInput.toggleAttribute("aria-invalid", !password);

    if (!username || !password) {
        showError("Please enter both your username and password.");
        (username ? passwordInput : usernameInput).focus();
        return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "Signing in...";

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "same-origin",
            body: JSON.stringify({ username, password })
        });

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            showError(result.error || "Invalid username or password.");
            passwordInput.select();
            return;
        }

        // The server sends each role to its own dashboard.
        window.location.href = "/dashboard";

    } catch (error) {
        showError("Unable to connect to the server. Please try again.");
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Sign in";
    }
});
