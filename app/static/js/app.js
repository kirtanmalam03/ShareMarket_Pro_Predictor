/* ==========================================================================
   ShareMarket Pro Predictor - Client Application Script
   ========================================================================== */

let USD_TO_INR = 83.5;
let showINR = false;
let activeSymbol = "AAPL";
let currentLiveData = null;
let currentHistoricalData = null;
let currentPortfolioData = [];
let priceChart = null;
let volumeChart = null;

function qs(id) {
    return document.getElementById(id);
}

async function fetchINRRate() {
    try {
        const response = await fetch("https://api.exchangerate-api.com/v4/latest/USD");
        const data = await response.json();
        if (data.rates && data.rates.INR) {
            USD_TO_INR = data.rates.INR;
        }
    } catch (_error) {
        // Fallback default USD to INR exchange rate
    }
}

function convertToINR(amount) {
    return amount * USD_TO_INR;
}

function formatCurrency(amount) {
    const value = Number(amount || 0);
    if (showINR) {
        return `₹${convertToINR(value).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatVolume(volume) {
    const numeric = Number(volume || 0);
    if (numeric >= 10000000) return `${(numeric / 10000000).toFixed(2)} Cr`;
    if (numeric >= 100000) return `${(numeric / 100000).toFixed(2)} L`;
    if (numeric >= 1000000) return `${(numeric / 1000000).toFixed(2)} M`;
    if (numeric >= 1000) return `${(numeric / 1000).toFixed(1)} K`;
    return numeric.toLocaleString();
}

function setHidden(el, hide) {
    if (!el) return;
    if (hide) {
        el.classList.add("hidden");
    } else {
        el.classList.remove("hidden");
    }
}

async function getJSON(url) {
    const response = await fetch(url);
    const data = await response.json();
    if (!data.ok) {
        throw new Error(data.error || "Request failed");
    }
    return data.data;
}

function initThemeToggle() {
    const themeBtn = qs("themeBtn");
    const root = document.documentElement;
    if (!themeBtn) return;

    const saved = window.localStorage.getItem("smpp-theme");
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = saved || (prefersDark ? "dark" : "light");
    
    if (initialTheme === "dark") {
        root.classList.add("dark");
        const icon = themeBtn.querySelector("i");
        if (icon) icon.className = "fas fa-sun text-amber-400";
    } else {
        root.classList.remove("dark");
        const icon = themeBtn.querySelector("i");
        if (icon) icon.className = "fas fa-moon text-indigo-600";
    }

    themeBtn.addEventListener("click", () => {
        const isDark = root.classList.toggle("dark");
        window.localStorage.setItem("smpp-theme", isDark ? "dark" : "light");
        const icon = themeBtn.querySelector("i");
        if (icon) {
            icon.className = isDark ? "fas fa-sun text-amber-400" : "fas fa-moon text-indigo-600";
        }
        if (currentHistoricalData) updateCharts(currentHistoricalData);
    });
}

function initDialogSystem() {
    const overlay = qs("dialogOverlay");
    const titleEl = qs("dialogTitle");
    const messageEl = qs("dialogMessage");
    const inputWrap = qs("dialogInputWrapper");
    const inputEl = qs("dialogInput");
    const cancelBtn = qs("dialogCancelBtn");
    const okBtn = qs("dialogOkBtn");
    const closeBtn = qs("dialogCloseBtn");

    if (!overlay) return;

    let resolver = null;

    const closeDialog = (result = null) => {
        setHidden(overlay, true);
        if (resolver) {
            resolver(result);
            resolver = null;
        }
    };

    const openDialog = (config) => new Promise((resolve) => {
        resolver = resolve;
        titleEl.textContent = config.title || "Message";
        messageEl.textContent = config.message || "";
        okBtn.textContent = config.okText || "OK";
        cancelBtn.textContent = config.cancelText || "Cancel";
        setHidden(cancelBtn, !config.showCancel);
        setHidden(inputWrap, !config.showInput);
        inputEl.value = config.defaultValue || "";
        setHidden(overlay, false);
        if (config.showInput) {
            inputEl.focus();
            inputEl.select();
        } else {
            okBtn.focus();
        }
    });

    if (closeBtn) closeBtn.addEventListener("click", () => closeDialog(null));
    if (cancelBtn) cancelBtn.addEventListener("click", () => closeDialog(null));
    overlay.addEventListener("click", (event) => {
        if (event.target === overlay) closeDialog(null);
    });

    window.showAlertDialog = async (message, title = "Notice") => {
        okBtn.onclick = () => closeDialog(true);
        await openDialog({ title, message, showCancel: false, showInput: false });
        return true;
    };

    window.showConfirmDialog = async (message, title = "Please Confirm") => {
        okBtn.onclick = () => closeDialog(true);
        return openDialog({ title, message, showCancel: true, showInput: false });
    };

    window.showPromptDialog = async (message, defaultValue = "", title = "Input Required") => {
        okBtn.onclick = () => closeDialog(inputEl.value);
        return openDialog({
            title,
            message,
            showCancel: true,
            showInput: true,
            defaultValue
        });
    };
}

function updateStatsCards(live) {
    const target = qs("statsCards");
    if (!target || !live) return;

    const changePct = Number(live.change_percent || 0);
    const isUp = changePct >= 0;
    target.innerHTML = `
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Asset Symbol</p>
            <p class="text-xl font-heading font-extrabold text-slate-900 dark:text-slate-100 font-mono">${live.symbol || "-"}</p>
        </div>
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Live Price</p>
            <p class="text-xl font-heading font-extrabold text-slate-900 dark:text-slate-100 font-mono">${formatCurrency(live.price)}</p>
        </div>
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">24h Change</p>
            <p class="text-xl font-heading font-extrabold font-mono flex items-center gap-1 ${isUp ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}">
                <i class="fas ${isUp ? "fa-arrow-trend-up" : "fa-arrow-trend-down"} text-sm"></i>
                ${isUp ? "+" : ""}${changePct.toFixed(2)}%
            </p>
        </div>
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Volume</p>
            <p class="text-xl font-heading font-extrabold text-slate-900 dark:text-slate-100 font-mono">${formatVolume(live.volume)}</p>
        </div>
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Day Low / High</p>
            <p class="text-xs font-semibold text-slate-700 dark:text-slate-300 font-mono pt-1">${formatCurrency(live.day_low)} - ${formatCurrency(live.day_high)}</p>
        </div>
    `;
}

function updatePredictionPanel(prediction) {
    const panel = qs("predictionPanel");
    if (!panel || !prediction) return;

    const isUp = prediction.direction === "UP";
    panel.innerHTML = `
        <div class="p-3.5 rounded-xl ${isUp ? "bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300" : "bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 text-rose-800 dark:text-rose-300"} flex items-center justify-between">
            <div class="flex items-center gap-2.5">
                <i class="fas ${isUp ? "fa-circle-chevron-up text-emerald-600 dark:text-emerald-400" : "fa-circle-chevron-down text-rose-600 dark:text-rose-400"} text-2xl"></i>
                <div>
                    <span class="text-[11px] text-slate-500 dark:text-slate-400 block font-semibold uppercase">Signal Forecast</span>
                    <strong class="text-base font-heading font-extrabold">${isUp ? "BULLISH (UP)" : "BEARISH (DOWN)"}</strong>
                </div>
            </div>
            <span class="text-xs px-2.5 py-1 rounded-full font-mono font-bold ${isUp ? "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300" : "bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300"}">
                ${prediction.confidence}% Confidence
            </span>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs pt-1">
            <div class="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-0.5">
                <span class="text-slate-500 dark:text-slate-400 block text-[10px]">Up Probability</span>
                <strong class="text-emerald-600 dark:text-emerald-400 font-mono text-sm">${prediction.up_probability}%</strong>
            </div>
            <div class="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-0.5">
                <span class="text-slate-500 dark:text-slate-400 block text-[10px]">Down Probability</span>
                <strong class="text-rose-600 dark:text-rose-400 font-mono text-sm">${prediction.down_probability}%</strong>
            </div>
        </div>

        <div class="flex justify-between items-center text-xs p-2.5 rounded-lg bg-slate-100 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800">
            <span class="text-slate-500 dark:text-slate-400">Backtested Accuracy</span>
            <span class="font-mono font-bold text-indigo-600 dark:text-indigo-400">${prediction.model_accuracy}%</span>
        </div>
    `;

    const confidenceBar = qs("confidenceBar");
    const confidenceText = qs("confidenceText");
    if (confidenceBar) {
        const score = prediction.confidence || 0;
        confidenceBar.style.width = `${score}%`;
        confidenceBar.className = `h-full rounded-full transition-all duration-700 ${isUp ? "bg-gradient-to-r from-emerald-600 to-emerald-400" : "bg-gradient-to-r from-rose-600 to-rose-400"}`;
    }
    if (confidenceText) {
        confidenceText.textContent = `${prediction.confidence || 0}%`;
    }
}

function updateCharts(history) {
    if (!history || !qs("priceChart") || !qs("volumeChart")) return;
    if (priceChart) priceChart.destroy();
    if (volumeChart) volumeChart.destroy();

    const prices = showINR ? history.close.map(convertToINR) : history.close;
    const currencySymbol = showINR ? "₹" : "$";

    const isDarkMode = document.documentElement.classList.contains("dark");
    const gridColor = isDarkMode ? "rgba(255, 255, 255, 0.08)" : "rgba(226, 232, 240, 0.9)";
    const textColor = isDarkMode ? "#94a3b8" : "#475569";
    const tooltipBg = isDarkMode ? "rgba(15, 23, 42, 0.9)" : "rgba(255, 255, 255, 0.95)";
    const tooltipTitle = isDarkMode ? "#f8fafc" : "#0f172a";

    const priceCtx = qs("priceChart").getContext("2d");
    const priceGradient = priceCtx.createLinearGradient(0, 0, 0, 300);
    if (isDarkMode) {
        priceGradient.addColorStop(0, "rgba(99, 102, 241, 0.35)");
        priceGradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");
    } else {
        priceGradient.addColorStop(0, "rgba(99, 102, 241, 0.25)");
        priceGradient.addColorStop(1, "rgba(99, 102, 241, 0.02)");
    }

    priceChart = new Chart(priceCtx, {
        type: "line",
        data: {
            labels: history.dates,
            datasets: [{
                label: `${history.symbol} Close Price`,
                data: prices,
                borderColor: "#6366f1",
                borderWidth: 2.5,
                backgroundColor: priceGradient,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: "#38bdf8"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: tooltipBg,
                    titleColor: tooltipTitle,
                    bodyColor: tooltipTitle,
                    titleFont: { family: "Inter", size: 12 },
                    bodyFont: { family: "JetBrains Mono", size: 13, weight: "bold" },
                    padding: 10,
                    cornerRadius: 8,
                    borderColor: "rgba(99, 102, 241, 0.4)",
                    borderWidth: 1,
                    callbacks: {
                        label: (ctx) => ` Close: ${currencySymbol}${Number(ctx.raw).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { family: "Inter", size: 10 } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: {
                        color: textColor,
                        font: { family: "JetBrains Mono", size: 11 },
                        callback: (value) => `${currencySymbol}${Number(value).toLocaleString()}`
                    }
                }
            }
        }
    });

    const volCtx = qs("volumeChart").getContext("2d");
    volumeChart = new Chart(volCtx, {
        type: "bar",
        data: {
            labels: history.dates,
            datasets: [{
                label: "Volume",
                data: history.volume,
                backgroundColor: isDarkMode ? "rgba(6, 182, 212, 0.7)" : "rgba(99, 102, 241, 0.6)",
                hoverBackgroundColor: "#06b6d4",
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: tooltipBg,
                    titleColor: tooltipTitle,
                    bodyColor: tooltipTitle,
                    titleFont: { family: "Inter", size: 11 },
                    bodyFont: { family: "JetBrains Mono", size: 12 },
                    padding: 8,
                    callbacks: {
                        label: (ctx) => ` Volume: ${formatVolume(ctx.raw)}`
                    }
                }
            },
            scales: {
                x: { display: false },
                y: {
                    grid: { color: gridColor },
                    ticks: {
                        color: textColor,
                        font: { family: "JetBrains Mono", size: 9 },
                        callback: (value) => formatVolume(value)
                    }
                }
            }
        }
    });
}

async function loadDashboardData(symbol) {
    const loader = qs("dashboardLoader");
    try {
        setHidden(loader, false);
        activeSymbol = (symbol || activeSymbol || "AAPL").toUpperCase();
        const period = qs("periodSelect") ? qs("periodSelect").value : "3mo";

        const [history, live] = await Promise.all([
            getJSON(`/api/historical/${activeSymbol}?period=${period}`),
            getJSON(`/api/live/${activeSymbol}`)
        ]);

        currentHistoricalData = history;
        currentLiveData = live;
        updateCharts(history);
        updateStatsCards(live);

        setHidden(loader, true);

        const panel = qs("predictionPanel");
        if (panel) {
            panel.innerHTML = `
                <div class="flex items-center gap-2.5 text-xs text-indigo-600 dark:text-indigo-400 p-3 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/20">
                    <span class="loader loader-sm"></span>
                    <span>Calculating technical features & XGBoost prediction...</span>
                </div>
            `;
        }

        getJSON(`/api/predict/${activeSymbol}`)
            .then((prediction) => updatePredictionPanel(prediction))
            .catch(() => {
                if (panel) {
                    panel.innerHTML = `<div class="text-xs text-rose-600 dark:text-rose-400 p-2.5 rounded-lg bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20">Prediction model output temporarily unavailable.</div>`;
                }
            });
    } catch (error) {
        await window.showAlertDialog(error.message || "Failed to load stock data.", "Market Data Error");
    } finally {
        setHidden(loader, true);
    }
}

async function refreshMarketOverview() {
    const grid = qs("marketGrid");
    const loader = qs("marketOverviewLoader");
    if (!grid) return;

    try {
        setHidden(loader, false);
        const overview = await getJSON("/api/market/overview");
        const stocks = overview.stocks || [];
        grid.innerHTML = stocks.map((stock) => {
            const isUp = Number(stock.change_percent || 0) >= 0;
            return `
                <button class="section-card text-left hover:border-indigo-500/50 transition-all p-3 space-y-1 group" data-symbol="${stock.symbol}">
                    <div class="flex items-center justify-between">
                        <span class="font-mono font-bold text-sm text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">${stock.symbol}</span>
                        <span class="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${isUp ? "bg-emerald-100 dark:bg-emerald-500/15 text-emerald-800 dark:text-emerald-400" : "bg-rose-100 dark:bg-rose-500/15 text-rose-800 dark:text-rose-400"}">
                            ${isUp ? "+" : ""}${Number(stock.change_percent || 0).toFixed(2)}%
                        </span>
                    </div>
                    <p class="text-base font-mono font-extrabold text-slate-900 dark:text-slate-200">${formatCurrency(stock.price)}</p>
                </button>
            `;
        }).join("");

        grid.querySelectorAll("button[data-symbol]").forEach((btn) => {
            btn.addEventListener("click", () => {
                const symbol = btn.getAttribute("data-symbol");
                if (qs("symbolInput")) qs("symbolInput").value = symbol;
                loadDashboardData(symbol);
            });
        });
    } catch (_error) {
        grid.innerHTML = '<div class="col-span-full text-xs text-rose-600 dark:text-rose-400 p-3 rounded-lg bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20">Unable to update market overview grid right now.</div>';
    } finally {
        setHidden(loader, true);
    }
}

async function addFromDashboard() {
    const sharesText = await window.showPromptDialog("Enter number of shares to purchase", "1", "Add Position");
    if (!sharesText) return;

    const buyPriceText = await window.showPromptDialog("Enter purchase buy price per share", String(currentLiveData?.price || 0), "Add Position");
    if (!buyPriceText) return;

    const shares = parseInt(sharesText, 10);
    const buyPrice = parseFloat(buyPriceText);
    if (!Number.isFinite(shares) || shares <= 0 || !Number.isFinite(buyPrice) || buyPrice <= 0) {
        await window.showAlertDialog("Please enter valid share quantity and buy price.", "Invalid Input");
        return;
    }

    try {
        const response = await fetch("/api/portfolio/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: activeSymbol, shares, buy_price: buyPrice })
        });
        const result = await response.json();
        if (!result.ok) throw new Error(result.error || "Failed to add stock position.");
        await window.showAlertDialog(result.message || `${activeSymbol} added to portfolio.`, "Position Added");
    } catch (error) {
        await window.showAlertDialog(error.message || "Could not add to portfolio.", "Error");
    }
}

async function loadPortfolio() {
    const loader = qs("portfolioLoader");
    try {
        setHidden(loader, false);
        const portfolio = await getJSON("/api/portfolio");
        currentPortfolioData = portfolio || [];
        renderPortfolioTable(currentPortfolioData);
        renderPortfolioStats(currentPortfolioData);
    } catch (error) {
        await window.showAlertDialog(error.message || "Unable to load portfolio assets.", "Portfolio Error");
    } finally {
        setHidden(loader, true);
    }
}

function renderPortfolioTable(stocks) {
    const tbody = qs("portfolioTable");
    if (!tbody) return;
    if (!stocks.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center p-8 text-slate-500 dark:text-slate-400 text-sm">No positions in portfolio yet. Click "Add New Stock" above to get started.</td></tr>';
        return;
    }

    tbody.innerHTML = stocks.map((stock) => {
        const pl = Number(stock.profit_loss || 0);
        const isUp = pl >= 0;
        return `
            <tr class="hover:bg-slate-100 dark:hover:bg-slate-900/40 transition-colors">
                <td class="p-3.5">
                    <span class="font-mono font-extrabold text-sm text-slate-900 dark:text-slate-100">${stock.symbol}</span>
                </td>
                <td class="p-3.5 font-mono text-slate-800 dark:text-slate-200">${stock.shares}</td>
                <td class="p-3.5 font-mono text-slate-600 dark:text-slate-300">${formatCurrency(stock.buy_price)}</td>
                <td class="p-3.5 font-mono font-semibold text-slate-900 dark:text-slate-100">${formatCurrency(stock.current_price)}</td>
                <td class="p-3.5 font-mono font-bold text-slate-900 dark:text-slate-100">${formatCurrency(stock.current_value)}</td>
                <td class="p-3.5 font-mono font-bold ${isUp ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}">
                    ${isUp ? "+" : ""}${formatCurrency(pl)} (${Math.abs(Number(stock.profit_loss_percent || 0)).toFixed(2)}%)
                </td>
                <td class="p-3.5 text-right">
                    <button class="btn btn-ghost py-1 px-2.5 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10" data-remove-symbol="${stock.symbol}" title="Delete position">
                        <i class="fas fa-trash-alt"></i> Remove
                    </button>
                </td>
            </tr>
        `;
    }).join("");

    tbody.querySelectorAll("button[data-remove-symbol]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            await removeStock(btn.getAttribute("data-remove-symbol"));
        });
    });
}

function renderPortfolioStats(stocks) {
    const stats = qs("portfolioStats");
    if (!stats) return;

    const totalValue = stocks.reduce((sum, item) => sum + Number(item.current_value || 0), 0);
    const totalCost = stocks.reduce((sum, item) => sum + (Number(item.buy_price || 0) * Number(item.shares || 0)), 0);
    const totalPL = totalValue - totalCost;
    const totalPLPercent = totalCost > 0 ? (totalPL / totalCost) * 100 : 0;
    const isUp = totalPL >= 0;

    stats.innerHTML = `
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Positions</p>
            <p class="text-2xl font-heading font-extrabold text-slate-900 dark:text-slate-100 font-mono">${stocks.length}</p>
        </div>
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Portfolio Net Worth</p>
            <p class="text-2xl font-heading font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">${formatCurrency(totalValue)}</p>
        </div>
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Invested Capital</p>
            <p class="text-2xl font-heading font-extrabold text-slate-800 dark:text-slate-200 font-mono">${formatCurrency(totalCost)}</p>
        </div>
        <div class="section-card space-y-1">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Net Profit / Loss</p>
            <p class="text-2xl font-heading font-extrabold font-mono ${isUp ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}">
                ${isUp ? "+" : ""}${formatCurrency(totalPL)} (${totalPLPercent.toFixed(2)}%)
            </p>
        </div>
    `;
}

function openPortfolioModal() {
    setHidden(qs("addStockModal"), false);
}

function closePortfolioModal() {
    setHidden(qs("addStockModal"), true);
    if (qs("modalSymbol")) qs("modalSymbol").value = "";
    if (qs("modalShares")) qs("modalShares").value = "";
    if (qs("modalBuyPrice")) qs("modalBuyPrice").value = "";
    if (qs("modalNotes")) qs("modalNotes").value = "";
}

async function addStockFromPortfolioModal() {
    const symbol = (qs("modalSymbol")?.value || "").trim().toUpperCase();
    const shares = parseInt(qs("modalShares")?.value || "0", 10);
    const buyPrice = parseFloat(qs("modalBuyPrice")?.value || "0");
    const notes = (qs("modalNotes")?.value || "").trim();

    if (!symbol || shares <= 0 || buyPrice <= 0) {
        await window.showAlertDialog("Please provide symbol, positive shares, and valid buy price.", "Invalid Input");
        return;
    }

    try {
        const response = await fetch("/api/portfolio/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol, shares, buy_price: buyPrice, notes })
        });
        const result = await response.json();
        if (!result.ok) throw new Error(result.error || "Failed to add stock.");
        closePortfolioModal();
        await loadPortfolio();
        await window.showAlertDialog(result.message || `${symbol} added to portfolio.`, "Position Created");
    } catch (error) {
        await window.showAlertDialog(error.message || "Could not add position.", "Error");
    }
}

async function removeStock(symbol) {
    const confirmed = await window.showConfirmDialog(`Are you sure you want to remove ${symbol} position from your portfolio?`, "Remove Position");
    if (!confirmed) return;

    try {
        const response = await fetch(`/api/portfolio/remove/${symbol}`, { method: "DELETE" });
        const result = await response.json();
        if (!result.ok) throw new Error(result.error || "Failed to remove stock.");
        await loadPortfolio();
        await window.showAlertDialog(result.message || `${symbol} position removed.`, "Position Removed");
    } catch (error) {
        await window.showAlertDialog(error.message || "Could not remove stock position.", "Error");
    }
}

function initDashboardPage() {
    if (!qs("dashboardPage")) return;

    const searchBtn = qs("searchBtn");
    const symbolInput = qs("symbolInput");
    const periodSelect = qs("periodSelect");
    const currencyToggle = qs("currencyToggle");
    const addBtn = qs("addToPortfolioBtn");

    if (searchBtn) {
        searchBtn.addEventListener("click", () => {
            const value = (symbolInput?.value || "").trim();
            if (!value) return;
            loadDashboardData(value);
        });
    }

    if (symbolInput) {
        symbolInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                searchBtn?.click();
            }
        });
    }

    document.querySelectorAll(".quick-symbol-btn").forEach((chip) => {
        chip.addEventListener("click", () => {
            const sym = chip.getAttribute("data-symbol");
            if (symbolInput) symbolInput.value = sym;
            loadDashboardData(sym);
        });
    });

    if (periodSelect) {
        periodSelect.addEventListener("change", () => {
            loadDashboardData(activeSymbol);
        });
    }

    if (currencyToggle) {
        currencyToggle.addEventListener("click", () => {
            showINR = !showINR;
            currencyToggle.innerHTML = showINR
                ? '<i class="fas fa-dollar-sign text-indigo-600 dark:text-indigo-400"></i> Show in USD'
                : '<i class="fas fa-rupee-sign text-emerald-600 dark:text-emerald-400"></i> Show in INR';
            if (currentLiveData) updateStatsCards(currentLiveData);
            if (currentHistoricalData) updateCharts(currentHistoricalData);
            refreshMarketOverview();
        });
    }

    if (addBtn) {
        addBtn.addEventListener("click", addFromDashboard);
    }

    loadDashboardData("AAPL");
    refreshMarketOverview();
    setInterval(refreshMarketOverview, 10000);
}

function initPortfolioPage() {
    if (!qs("portfolioPage")) return;
    qs("openAddStockModalBtn")?.addEventListener("click", openPortfolioModal);
    qs("cancelAddStockModalBtn")?.addEventListener("click", closePortfolioModal);
    qs("closeAddStockModalBtn")?.addEventListener("click", closePortfolioModal);
    qs("submitAddStockBtn")?.addEventListener("click", addStockFromPortfolioModal);
    qs("addStockModal")?.addEventListener("click", (event) => {
        if (event.target === qs("addStockModal")) closePortfolioModal();
    });

    loadPortfolio();
    setInterval(loadPortfolio, 30000);
}

document.addEventListener("DOMContentLoaded", async () => {
    initThemeToggle();
    initDialogSystem();
    await fetchINRRate();
    setInterval(fetchINRRate, 3600000);
    initDashboardPage();
    initPortfolioPage();
    initAuthForms();
    initFlashToDialog();
    initMobileNav();
});

function initMobileNav() {
    const btn = qs("mobileNavBtn");
    const panel = qs("mobileNav");
    if (!btn || !panel) return;

    const setOpen = (open) => {
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        setHidden(panel, !open);
        btn.innerHTML = open ? '<i class="fas fa-xmark"></i>' : '<i class="fas fa-bars"></i>';
    };

    let open = false;
    btn.addEventListener("click", () => {
        open = !open;
        setOpen(open);
    });

    panel.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => setOpen(false));
    });
}

function initAuthForms() {
    const loginForm = document.querySelector("form[action$='/auth/login']");
    const registerForm = document.querySelector("form[action$='/auth/register']");

    [loginForm, registerForm].forEach((form) => {
        if (!form) return;
        form.querySelectorAll("input[type='password']").forEach((input) => {
            if (input.parentNode.querySelector(".password-toggle-btn")) return;
            input.classList.add("pr-10");

            const toggle = document.createElement("button");
            toggle.type = "button";
            toggle.className = "password-toggle-btn absolute right-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs z-10";
            toggle.innerHTML = '<i class="fas fa-eye"></i>';
            
            input.parentNode.appendChild(toggle);

            toggle.addEventListener("click", () => {
                const isPassword = input.type === "password";
                input.type = isPassword ? "text" : "password";
                toggle.innerHTML = isPassword ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
            });
        });
    });
}

function initFlashToDialog() {
    const flashEls = document.querySelectorAll(".flash");
    if (!flashEls.length) return;

    const messages = Array.from(flashEls).map((el) => el.innerText.trim()).filter(Boolean);
    if (!messages.length) return;

    const combined = messages.join("\n");
    flashEls.forEach((el) => el.parentNode && el.parentNode.removeChild(el));
    window.showAlertDialog(combined, "Notification");
}