/* Shared helpers for every dashboard page: API calls, DOM building,
   toasts, confirmation dialogs, section navigation and logout. */

"use strict";

const App = (() => {
    // -----------------------------------------------------------------
    // API
    // -----------------------------------------------------------------

    // Call the Flask API with the session cookie. Returns parsed JSON or
    // throws an Error carrying the backend's error message.
    async function api(path, { method = "GET", body } = {}) {
        let response;

        try {
            response = await fetch(path, {
                method,
                credentials: "same-origin",
                headers: body === undefined ? {} : { "Content-Type": "application/json" },
                body: body === undefined ? undefined : JSON.stringify(body)
            });
        } catch (networkError) {
            throw new Error("Unable to reach the server. Check that Flask is running.");
        }

        if (response.status === 401) {
            window.location.href = "/login";
            throw new Error("Your session has expired. Please sign in again.");
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            const error = new Error(data.error || `Request failed (${response.status})`);
            error.status = response.status;
            throw error;
        }

        return data;
    }

    // -----------------------------------------------------------------
    // DOM helpers (textContent only, so data is never parsed as HTML)
    // -----------------------------------------------------------------

    function el(tag, props = {}, ...children) {
        const node = document.createElement(tag);

        for (const [key, value] of Object.entries(props)) {
            if (value === undefined || value === null || value === false) continue;
            if (key === "className") node.className = value;
            else if (key === "text") node.textContent = value;
            else if (key === "dataset") Object.assign(node.dataset, value);
            else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
            else node.setAttribute(key, value === true ? "" : value);
        }

        for (const child of children.flat()) {
            if (child === null || child === undefined || child === false) continue;
            node.append(child instanceof Node ? child : String(child));
        }

        return node;
    }

    const $ = (selector, root = document) => root.querySelector(selector);

    function icon(name) {
        const holder = document.querySelector(`#iconTemplates`).content
            .querySelector(`[data-icon="${name}"] svg`);
        return holder ? holder.cloneNode(true) : document.createTextNode("");
    }

    function iconButton(name, label, onClick, variant = "btn-ghost") {
        return el("button", {
            type: "button",
            className: `btn ${variant} btn-sm btn-icon`,
            title: label,
            "aria-label": label,
            onclick: onClick
        }, icon(name));
    }

    function avatarCell(name, sub) {
        return el("div", { className: "cell-user" },
            el("span", { className: "avatar", text: (name || "?").slice(0, 1) }),
            el("div", {},
                el("div", { text: name }),
                sub ? el("div", { className: "muted", text: sub }) : null
            )
        );
    }

    function badge(text, tone) {
        return el("span", { className: `badge badge-${tone}`, text });
    }

    const STATUS_TONES = { Present: "green", Absent: "red", Late: "amber" };

    function statusBadge(status) {
        return badge(status, STATUS_TONES[status] || "gray");
    }

    function roleBadge(role) {
        const tones = { admin: "blue", teacher: "amber", student: "gray" };
        return badge(role.charAt(0).toUpperCase() + role.slice(1), tones[role] || "gray");
    }

    function percentTone(value) {
        if (value >= 75) return "good";
        if (value >= 60) return "warn";
        return "bad";
    }

    // Percentage bar; width is set through the CSSOM, which the CSP allows.
    function progress(value, hasData = true) {
        if (!hasData) {
            return el("span", { className: "muted", text: "No records yet" });
        }

        const bar = el("div", { className: `progress-bar ${percentTone(value)}` });
        requestAnimationFrame(() => { bar.style.width = `${Math.min(value, 100)}%`; });

        return el("div", { className: "progress" },
            el("div", { className: "progress-track" }, bar),
            el("span", { className: "progress-value", text: `${formatPercent(value)}` })
        );
    }

    function formatPercent(value) {
        return `${Number.isInteger(value) ? value : value.toFixed(1)}%`;
    }

    function formatDate(isoDate) {
        const [year, month, day] = isoDate.split("-").map(Number);
        return new Date(year, month - 1, day).toLocaleDateString(undefined, {
            weekday: "short", day: "numeric", month: "short", year: "numeric"
        });
    }

    function todayIso() {
        const now = new Date();
        const offset = now.getTimezoneOffset() * 60000;
        return new Date(now - offset).toISOString().slice(0, 10);
    }

    // -----------------------------------------------------------------
    // Table states
    // -----------------------------------------------------------------

    function stateBlock(kind, title, message) {
        const iconName = kind === "error" ? "alert" : kind === "empty" ? "info" : null;
        return el("div", { className: `state ${kind === "error" ? "state-error" : ""}` },
            kind === "loading" ? el("div", { className: "spinner" }) : icon(iconName),
            title ? el("strong", { text: title }) : null,
            message ? el("span", { text: message }) : null
        );
    }

    function stateRow(tbody, columns, kind, title, message) {
        tbody.replaceChildren(
            el("tr", {}, el("td", { colspan: columns }, stateBlock(kind, title, message)))
        );
    }

    function fillRows(tbody, columns, rows, emptyTitle, emptyMessage) {
        if (rows.length === 0) {
            stateRow(tbody, columns, "empty", emptyTitle, emptyMessage);
            return;
        }

        tbody.replaceChildren(...rows.map((cells) =>
            el("tr", {}, ...cells.map((cell) =>
                cell instanceof HTMLTableCellElement ? cell : el("td", {}, cell)
            ))
        ));
    }

    function fillSelect(select, items, { placeholder, value = "id", label = "name" } = {}) {
        const previous = select.value;
        select.replaceChildren(
            ...(placeholder !== undefined ? [el("option", { value: "", text: placeholder })] : []),
            ...items.map((item) => el("option", { value: item[value], text: item[label] }))
        );
        if ([...select.options].some((option) => option.value === previous)) {
            select.value = previous;
        }
    }

    // -----------------------------------------------------------------
    // Feedback: toasts, button loading, confirm dialog
    // -----------------------------------------------------------------

    function toast(message, kind = "success") {
        const node = el("div", { className: `toast ${kind}`, role: "status" },
            icon(kind === "error" ? "alert" : "check"),
            el("span", { text: message })
        );

        $("#toasts").append(node);

        setTimeout(() => {
            node.classList.add("leaving");
            setTimeout(() => node.remove(), 250);
        }, kind === "error" ? 5000 : 3200);
    }

    async function withLoading(button, task) {
        const original = [...button.childNodes].map((node) => node.cloneNode(true));
        button.disabled = true;
        button.replaceChildren(el("span", { className: "spinner" }), "Working...");

        try {
            return await task();
        } finally {
            button.disabled = false;
            button.replaceChildren(...original);
        }
    }

    function confirmAction({ title, message, confirmLabel = "Confirm", danger = true }) {
        const dialog = $("#confirmDialog");
        $("#confirmTitle").textContent = title;
        $("#confirmMessage").textContent = message;

        const button = $("#confirmButton");
        button.textContent = confirmLabel;
        button.className = `btn ${danger ? "btn-danger" : "btn-primary"}`;

        dialog.returnValue = "";
        dialog.showModal();

        return new Promise((resolve) => {
            dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), { once: true });
        });
    }

    // Wire a <dialog> containing a form: open() resets it, submit runs
    // onSubmit and keeps the dialog open with the error if it fails.
    // onSubmit may return "keep-open" to stay open after success.
    function formDialog(dialog, onSubmit) {
        const form = $("form", dialog);
        const errorBox = $(".form-error", dialog);
        const submit = $("button[type=submit]", dialog);

        dialog.querySelectorAll("[data-close]").forEach((button) =>
            button.addEventListener("click", () => dialog.close())
        );

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            errorBox.textContent = "";

            if (!form.reportValidity()) return;

            try {
                const result = await withLoading(submit, () => onSubmit(form));
                if (result !== "keep-open") dialog.close();
            } catch (error) {
                errorBox.textContent = error.message;
            }
        });

        return {
            open(prepare) {
                form.reset();
                errorBox.textContent = "";
                if (prepare) prepare(form);
                dialog.showModal();
            }
        };
    }

    // -----------------------------------------------------------------
    // Section navigation (hash based) and sidebar
    // -----------------------------------------------------------------

    function initSections(sections, onShow) {
        const links = document.querySelectorAll(".nav-link[data-section]");
        const sidebar = $("#sidebar");
        const backdrop = $("#sidebarBackdrop");
        const toggle = $("#menuToggle");
        const loaded = new Set();

        function setSidebar(open) {
            sidebar.classList.toggle("open", open);
            backdrop.hidden = !open;
            toggle.setAttribute("aria-expanded", String(open));
        }

        toggle.addEventListener("click", () => setSidebar(!sidebar.classList.contains("open")));
        backdrop.addEventListener("click", () => setSidebar(false));

        function show() {
            const name = location.hash.slice(1);
            const current = sections[name] ? name : Object.keys(sections)[0];

            for (const key of Object.keys(sections)) {
                document.getElementById(`section-${key}`).hidden = key !== current;
            }

            links.forEach((link) => {
                const active = link.dataset.section === current;
                link.classList.toggle("active", active);
                if (active) link.setAttribute("aria-current", "page");
                else link.removeAttribute("aria-current");
            });

            $("#pageTitle").textContent = sections[current].title;
            $("#pageSubtitle").textContent = sections[current].subtitle || "";
            document.title = `${sections[current].title} | Attendance Management System`;
            setSidebar(false);

            onShow(current, !loaded.has(current));
            loaded.add(current);
        }

        window.addEventListener("hashchange", show);
        show();
    }

    // -----------------------------------------------------------------
    // Logout (FR-15)
    // -----------------------------------------------------------------

    const logoutButton = $("#logoutButton");

    if (logoutButton) {
        logoutButton.addEventListener("click", async () => {
            const ok = await confirmAction({
                title: "Log out?",
                message: "You will need to sign in again to continue.",
                confirmLabel: "Log out",
                danger: false
            });

            if (!ok) return;

            try {
                await api("/api/logout", { method: "POST" });
            } catch (error) {
                // The session is gone either way; continue to the login page.
            }
            window.location.href = "/login";
        });
    }

    return {
        api, el, $, icon, iconButton, avatarCell, badge, statusBadge, roleBadge,
        progress, percentTone, formatPercent, formatDate, todayIso,
        stateBlock, stateRow, fillRows, fillSelect,
        toast, withLoading, confirmAction, formDialog, initSections
    };
})();
