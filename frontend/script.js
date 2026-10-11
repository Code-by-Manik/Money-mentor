const API_URL = "http://127.0.0.1:8000";


// ================================
// HELPERS (rendering only)
// ================================

const inrFormatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
});

function formatMoney(value) {
    return inrFormatter.format(Number(value) || 0);
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[char]));
}

function titleCase(value) {
    return String(value || "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}

function formatDate(isoDate) {
    const parts = String(isoDate || "").split("-");
    if (parts.length !== 3) return escapeHtml(isoDate || "");
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const month = months[Number(parts[1]) - 1];
    return month ? `${Number(parts[2])} ${month} ${parts[0]}` : escapeHtml(isoDate);
}

function setGreeting() {
    const hour = new Date().getHours();
    const greeting =
        hour < 12 ? "Good morning" :
        hour < 17 ? "Good afternoon" :
        "Good evening";
    document.getElementById("greeting").textContent = greeting;
}


// ================================
// LOAD SUMMARY
// ================================

async function loadSummary() {
    try {
        const startDate =
            document.getElementById("start-date").value;

        const endDate =
            document.getElementById("end-date").value;

        let url = `${API_URL}/summary`;

        const params = new URLSearchParams();

        if (startDate) {
            params.append("start_date", startDate);
        }

        if (endDate) {
            params.append("end_date", endDate);
        }

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(
                `Server error: ${response.status}`
            );
        }

        const data = await response.json();

        document.getElementById("total-received").textContent =
            formatMoney(data.total_inflow);

        document.getElementById("total-paid").textContent =
            formatMoney(data.total_outflow);

        const netElement = document.getElementById("net-amount");

        netElement.textContent = formatMoney(data.net_amount);

        netElement.classList.toggle("negative", data.net_amount < 0);

        document.getElementById("summary-count").textContent =
            data.transaction_count;

    } catch (error) {

        console.error(
            "Error loading summary:",
            error
        );
    }
}


// ================================
// LOAD TRANSACTIONS
// ================================

async function loadTransactions() {
    try {
        const startDate = document.getElementById("start-date").value;
        const endDate = document.getElementById("end-date").value;


        let url = `${API_URL}/transactions`;

        const params = new URLSearchParams();

        if (startDate) {
            params.append("start_date", startDate);
        }

        if (endDate) {
            params.append("end_date", endDate);
        }

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const transactions = await response.json();

        const container =
            document.getElementById("transactions-container");

        const transactionCount =
            document.getElementById("transaction-count");

        container.innerHTML = "";


        // No transactions
        if (transactions.length === 0) {

            transactionCount.textContent = "0 transactions";

            container.innerHTML = `
                <p class="loading">No transactions found.</p>
            `;

            return;
        }


        // Update transaction count
        transactionCount.textContent =
            `${transactions.length} transaction${
                transactions.length === 1 ? "" : "s"
            }`;


        // Display transactions
        const rows = transactions.map(transaction => {

            const description =
                escapeHtml(
                    transaction.merchant ||
                    transaction.description ||
                    "No description"
                );

            const category = titleCase(transaction.category) || "Uncategorized";

            const type = titleCase(transaction.transaction_type);

            const direction = escapeHtml(transaction.direction);

            const sign = transaction.direction === "outflow" ? "-" : "+";

            const date = formatDate(transaction.transaction_date);

            return `
            <tr class="tx-row ${direction}">
                <td class="col-date tx-date">${date}</td>
                <td class="col-desc">
                    <div class="tx-desc">
                        <span class="avatar" aria-hidden="true">${escapeHtml(category.charAt(0))}</span>
                        <span>${description}</span>
                    </div>
                    <div class="meta-mobile">${date} · ${escapeHtml(category)} · ${escapeHtml(type)}</div>
                </td>
                <td class="col-category"><span class="pill">${escapeHtml(category)}</span></td>
                <td class="col-type transaction-type">${escapeHtml(type)}</td>
                <td class="col-amount">
                    <span class="transaction-amount ${direction}">${sign}${formatMoney(transaction.amount)}</span>
                </td>
            </tr>`;
        }).join("");

        container.innerHTML = `
            <div class="table-wrap">
                <table class="tx-table">
                    <thead>
                        <tr>
                            <th scope="col">Date</th>
                            <th scope="col">Description</th>
                            <th scope="col">Category</th>
                            <th scope="col">Type</th>
                            <th scope="col" class="col-amount">Amount</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;

    } catch (error) {

        console.error(
            "Error loading transactions:",
            error
        );

        document.getElementById("transactions-container").innerHTML = `
            <p class="loading error">Unable to load transactions.</p>
        `;
    }
}


// ================================
// LOAD CATEGORY ANALYTICS
// (endpoint keeps its legacy name: /summary/apps)
// ================================

async function loadAppAnalytics() {

    try {

        const startDate =
            document.getElementById("start-date").value;

        const endDate =
            document.getElementById("end-date").value;

        let url = `${API_URL}/summary/apps`;

        const params = new URLSearchParams();

        if (startDate) {
            params.append("start_date", startDate);
        }

        if (endDate) {
            params.append("end_date", endDate);
        }

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(
                `Server error: ${response.status}`
            );
        }

        const data = await response.json();

        const container =
            document.getElementById(
                "app-analytics-container"
            );

        container.innerHTML = "";

        // Hide categories with nothing in them (e.g. "income" has no spend)
        const categories = Object.entries(data)
            .filter(([, stats]) =>
                stats.total_spent > 0 || stats.transaction_count > 0
            )
            .sort((a, b) => b[1].total_spent - a[1].total_spent);

        if (categories.length === 0) {

            container.innerHTML = `
                <p class="loading">
                    No analytics data found.
                </p>
            `;

            return;
        }

        const maxSpent = Math.max(
            ...categories.map(([, stats]) => stats.total_spent)
        ) || 1;

        categories.forEach(([category, stats]) => {

            const name = titleCase(category);

            const share = Math.round((stats.total_spent / maxSpent) * 100);

            const analyticsElement =
                document.createElement("div");

            analyticsElement.classList.add(
                "category-row"
            );

            analyticsElement.innerHTML = `
                <span class="avatar" aria-hidden="true">${escapeHtml(name.charAt(0))}</span>

                <div class="category-main">
                    <div class="category-name">${escapeHtml(name)}</div>
                    <div class="bar" aria-hidden="true"><span style="width:${share}%"></span></div>
                </div>

                <div class="category-figures">
                    <div class="category-amount">${formatMoney(stats.total_spent)}</div>
                    <div class="category-count">
                        ${stats.transaction_count}
                        transaction${
                            stats.transaction_count === 1
                                ? ""
                                : "s"
                        }
                    </div>
                </div>
            `;

            container.appendChild(
                analyticsElement
            );
        });

    } catch (error) {

        console.error(
            "Error loading app analytics:",
            error
        );

        document.getElementById(
            "app-analytics-container"
        ).innerHTML = `
            <p class="loading error">
                Unable to load analytics.
            </p>
        `;
    }
}


// ================================
// SYNC TRANSACTIONS
// ================================

async function syncTransactions() {

    const button =
        document.getElementById("sync-button");

    const status =
        document.getElementById("sync-status");

    try {

        button.disabled = true;
        button.textContent = "Syncing...";

        status.textContent =
            "Checking existing sync...";

        status.className =
            "sync-status";

        // --------------------------------
        // CHECK FOR EXISTING CONSENT
        // --------------------------------

        let consentId =
            localStorage.getItem("upi_tracker_consent_id");


        // --------------------------------
        // CREATE CONSENT ONLY IF NEEDED
        // --------------------------------

        if (!consentId) {

            status.textContent =
                "Creating consent...";

            const consentResponse =
                await fetch(
                    `${API_URL}/aa/create-consent`,
                    {
                        method: "POST"
                    }
                );

            if (!consentResponse.ok) {
                throw new Error(
                    `Consent error: ${consentResponse.status}`
                );
            }

            const consentData =
                await consentResponse.json();

            consentId =
                consentData.consent.id;

            // Remember this consent
            localStorage.setItem(
                "upi_tracker_consent_id",
                consentId
            );
        }


        // --------------------------------
        // APPROVE CONSENT
        // --------------------------------

        status.textContent =
            "Approving consent...";

        const approveResponse =
            await fetch(
                `${API_URL}/aa/callback?consentId=${encodeURIComponent(
                    consentId
                )}&status=APPROVED&mode=mock`
            );

        if (!approveResponse.ok) {
            throw new Error(
                `Approval error: ${approveResponse.status}`
            );
        }


        // --------------------------------
        // FETCH TRANSACTIONS
        // --------------------------------

        status.textContent =
            "Fetching transactions...";

        const fetchResponse =
            await fetch(
                `${API_URL}/aa/fetch-data?consent_id=${encodeURIComponent(
                    consentId
                )}`,
                {
                    method: "POST"
                }
            );

        if (!fetchResponse.ok) {
            throw new Error(
                `Fetch error: ${fetchResponse.status}`
            );
        }

        const fetchData =
            await fetchResponse.json();


        // --------------------------------
        // SUCCESS
        // --------------------------------

        status.textContent =
            fetchData.message ||
            "Transactions synced successfully!";

        status.className =
            "sync-status success";


        // --------------------------------
        // REFRESH DASHBOARD
        // --------------------------------

        await loadSummary();

        await loadTransactions();

        await loadAppAnalytics();


    } catch (error) {

        console.error(
            "Sync error:",
            error
        );

        status.textContent =
            "Failed to sync transactions.";

        status.className =
            "sync-status error";


    } finally {

        button.disabled = false;

        button.textContent =
            "Sync Transactions";
    }
}


// ================================
// APPLY FILTERS
// ================================

function applyFilters() {

    loadSummary();

    loadTransactions();

    loadAppAnalytics();
}


// ================================
// FILTER EVENT LISTENERS
// ================================

document
    .getElementById("start-date")
    .addEventListener("change", applyFilters);

document
    .getElementById("end-date")
    .addEventListener("change", applyFilters);

document
    .getElementById("clear-filters")
    .addEventListener("click", () => {

        ["start-date", "end-date"]
            .forEach(id => {
                document.getElementById(id).value = "";
            });

        applyFilters();
    });




// ================================
// UPLOAD CSV STATEMENT
// ================================

async function uploadStatement() {

    const fileInput =
        document.getElementById("statement-file");

    const button =
        document.getElementById("upload-button");

    const status =
        document.getElementById("upload-status");

    const file = fileInput.files[0];

    if (!file) {
        status.textContent =
            "Please select a CSV file first.";

        status.className =
            "sync-status error";

        return;
    }

    try {

        button.disabled = true;
        button.textContent = "Uploading...";

        status.textContent =
            "Uploading statement...";

        status.className =
            "sync-status";

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        const response =
            await fetch(
                `${API_URL}/statements/import-csv?account_id=1&statement_id=1`,
                {
                    method: "POST",
                    body: formData
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                `Server error: ${response.status}`
            );
        }

        status.textContent =
            `${data.message}. Imported ${data.transaction_count} transactions.`;

        status.className =
            "sync-status success";

        fileInput.value = "";

        updateFileName();

        // Refresh the dashboard so imported data appears immediately
        applyFilters();

    } catch (error) {

        console.error(
            "Upload error:",
            error
        );

        status.textContent =
            error.message ||
            "Failed to upload statement.";

        status.className =
            "sync-status error";

    } finally {

        button.disabled = false;

        button.textContent =
            "Upload Statement";
    }
}


// ================================
// UPLOAD BUTTON
// ================================

document
    .getElementById("upload-button")
    .addEventListener(
        "click",
        uploadStatement
    );


// ================================
// DROPZONE (visual layer over #statement-file)
// ================================

const statementInput = document.getElementById("statement-file");
const dropzone = document.getElementById("dropzone");
const fileNameLabel = document.getElementById("file-name");

function updateFileName() {

    const file = statementInput.files[0];

    fileNameLabel.textContent = file ? file.name : "No file selected";

    dropzone.classList.toggle("has-file", Boolean(file));

    if (file) {
        const status = document.getElementById("upload-status");
        status.textContent = "Ready to upload.";
        status.className = "sync-status";
    }
}

statementInput.addEventListener("change", updateFileName);

["dragenter", "dragover"].forEach(eventName => {
    dropzone.addEventListener(eventName, event => {
        event.preventDefault();
        dropzone.classList.add("is-dragging");
    });
});

["dragleave", "drop"].forEach(eventName => {
    dropzone.addEventListener(eventName, event => {
        event.preventDefault();
        dropzone.classList.remove("is-dragging");
    });
});

dropzone.addEventListener("drop", event => {

    const file = event.dataTransfer.files[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".csv")) {
        const status = document.getElementById("upload-status");
        status.textContent = "Only .csv files are supported.";
        status.className = "sync-status error";
        return;
    }

    statementInput.files = event.dataTransfer.files;

    updateFileName();
});


// ================================
// SIDEBAR: highlight the section in view
// ================================

const navAnchors = [...document.querySelectorAll(".nav-link[href^='#']")];

const sectionObserver = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if (!entry.isIntersecting) return;

        navAnchors.forEach(link => {

            const isActive =
                link.getAttribute("href") === `#${entry.target.id}`;

            link.classList.toggle("active", isActive);

            if (isActive) {
                link.setAttribute("aria-current", "true");
            } else {
                link.removeAttribute("aria-current");
            }
        });
    });

}, { rootMargin: "-30% 0px -60% 0px" });

navAnchors.forEach(link => {

    const target = document.querySelector(link.getAttribute("href"));

    if (target) sectionObserver.observe(target);
});


// ================================
// INITIAL LOAD
// ================================

setGreeting();

loadSummary();

loadTransactions();

loadAppAnalytics();