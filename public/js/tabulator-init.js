/**
 * Tabulator Table Initialization
 *
 * This module provides shared initialization logic for all Tabulator tables in the app.
 * Tables are configured via window.tabulatorConfigs[mode_code] objects set by Python.
 */

(function() {
    'use strict';

    // Constants (mirrored from Python constants.py)
    var INIT_DELAY_MS = 100;
    var MOBILE_BREAKPOINT_PX = 768;
    var PAGE_SIZE_MOBILE = 5;
    var PAGE_SIZE_DESKTOP = 10;
    var PAGE_SIZES = [5, 10, 25, 50, 100];
    var RATING_COLORS = {
        "1": "#dcfce7",   // green-100 for Good
        "0": "#fef9c3",   // yellow-100 for Ok
        "-1": "#fee2e2"   // red-100 for Bad
    };

    /**
     * Load user preferences from localStorage
     */
    function loadPrefs(prefsKey) {
        try {
            return JSON.parse(localStorage.getItem(prefsKey)) || {};
        } catch(e) {
            return {};
        }
    }

    /**
     * Save preferences to localStorage
     */
    function savePrefs(prefsKey, prefs) {
        localStorage.setItem(prefsKey, JSON.stringify(prefs));
    }

    /**
     * Create the Page column formatter (shared by all tables)
     */
    function pageFormatter(cell) {
        var data = cell.getRow().getData();
        return '<a href="/page_details/' + data.item_id + '" class="font-mono font-bold hover:underline">' + cell.getValue() + '</a>';
    }

    /**
     * Create the Start Text column formatter with tap-to-reveal for consecutive pages
     */
    function startTextFormatter(cell) {
        var data = cell.getRow().getData();
        if (data.is_consecutive) {
            return '<span class="reveal-dots text-gray-400 cursor-pointer select-none" data-text="' +
                   (data.start_text || '-').replace(/"/g, '&quot;') + '">● ● ●</span>';
        }
        return data.start_text || '-';
    }

    /**
     * Create rating dropdown formatter for mode tables
     */
    function createRatingFormatter(config) {
        return function(cell) {
            var data = cell.getRow().getData();
            var rating = data.rating;
            var select = document.createElement('select');
            select.className = 'select select-bordered select-sm w-full';
            select.setAttribute('data-testid', 'rating-select-' + data.item_id);
            select.innerHTML = '<option value="">-</option><option value="1">Good</option><option value="0">Ok</option><option value="-1">Bad</option>';

            if (rating !== null) {
                select.value = rating.toString();
            }

            // Set background color based on rating
            if (rating !== null && RATING_COLORS[rating.toString()]) {
                select.style.backgroundColor = RATING_COLORS[rating.toString()];
            }

            select.onchange = function() {
                var newRating = this.value === "" ? null : parseInt(this.value);
                var meta = window['modeTableMeta_' + config.mode_code] || {};

                fetch(config.rate_url, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        item_id: data.item_id,
                        rating: newRating,
                        plan_id: meta.plan_id
                    })
                }).then(function(response) {
                    if (response.ok) {
                        response.json().then(function(result) {
                            // Update cell color
                            if (result.rating !== null && RATING_COLORS[result.rating.toString()]) {
                                select.style.backgroundColor = RATING_COLORS[result.rating.toString()];
                            } else {
                                select.style.backgroundColor = "";
                            }
                            // Update pages revised indicator
                            updatePagesIndicator(result);
                        });
                    }
                });
            };
            return select;
        };
    }

    /**
     * Create checkbox formatter for NM table
     */
    function createCheckboxFormatter(config) {
        return function(cell) {
            var data = cell.getRow().getData();
            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'checkbox checkbox-success';
            checkbox.setAttribute('data-testid', 'memorized-checkbox-' + data.item_id);
            checkbox.checked = data.is_memorized_today;

            checkbox.onchange = function() {
                fetch(config.toggle_url, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ item_id: data.item_id })
                }).then(function(response) {
                    if (response.ok) {
                        response.json().then(function(result) {
                            checkbox.checked = result.is_memorized_today;
                        });
                    }
                });
            };
            return checkbox;
        };
    }

    /**
     * Update pages revised indicator in header
     */
    function updatePagesIndicator(result) {
        var todayEl = document.querySelector('[data-testid="pages-today"]');
        var yesterdayEl = document.querySelector('[data-testid="pages-yesterday"]');
        if (todayEl && result.pages_revised_today !== undefined) {
            todayEl.textContent = result.pages_revised_today;
        }
        if (yesterdayEl && result.pages_revised_yesterday !== undefined) {
            yesterdayEl.textContent = result.pages_revised_yesterday;
        }
    }

    /**
     * Setup tap-to-reveal event delegation on table
     */
    function setupTapToReveal(tableId) {
        var el = document.getElementById(tableId);
        if (el) {
            el.addEventListener("click", function(e) {
                if (e.target.classList.contains("reveal-dots")) {
                    var text = e.target.getAttribute("data-text");
                    e.target.textContent = text;
                    e.target.classList.remove("reveal-dots", "cursor-pointer");
                    e.target.classList.add("text-base");
                }
            });
        }
    }

    /**
     * Build column definitions based on config
     */
    function buildColumns(config, prefs) {
        var columns = [
            // Row selection column
            {
                title: "",
                formatter: "rowSelection",
                titleFormatter: "rowSelection",
                headerSort: false,
                width: 40,
                hozAlign: "center",
                responsive: 0
            },
            // Page column
            {
                title: "Page",
                field: "page",
                sorter: "number",
                headerFilter: "number",
                width: 70,
                responsive: 0,
                formatter: pageFormatter
            },
            // Surah column
            {
                title: "Surah",
                field: "surah",
                sorter: "string",
                headerFilter: "input",
                minWidth: 100,
                responsive: 2,
                visible: prefs.columns ? prefs.columns.surah !== false : true
            }
        ];

        // Juz column (only for non-NM modes)
        if (config.has_juz_column) {
            columns.push({
                title: "Juz",
                field: "juz",
                sorter: "number",
                headerFilter: "number",
                width: 60,
                hozAlign: "center",
                responsive: 2,
                visible: prefs.columns ? prefs.columns.juz !== false : true
            });
        }

        // Start Text column
        columns.push({
            title: "Start Text",
            field: "start_text",
            sorter: "string",
            minWidth: 150,
            responsive: 1,
            visible: prefs.columns ? prefs.columns.start_text !== false : true,
            formatter: startTextFormatter
        });

        // Action column (rating or checkbox)
        if (config.action_type === 'rating') {
            columns.push({
                title: "Rating",
                field: "rating",
                headerSort: false,
                width: 100,
                responsive: 0,
                formatter: createRatingFormatter(config)
            });
        } else if (config.action_type === 'checkbox') {
            columns.push({
                title: "Memorized",
                field: "is_memorized_today",
                headerSort: false,
                width: 100,
                responsive: 0,
                hozAlign: "center",
                formatter: createCheckboxFormatter(config)
            });
        }

        return columns;
    }

    /**
     * Initialize a mode table with the given configuration
     */
    function initModeTable(config) {
        if (typeof Tabulator === 'undefined') {
            setTimeout(function() { initModeTable(config); }, INIT_DELAY_MS);
            return;
        }

        var prefsKey = 'tabulator_prefs_' + config.mode_code;
        var prefs = loadPrefs(prefsKey);

        var table = new Tabulator('#' + config.table_id, {
            ajaxURL: config.api_url,
            ajaxResponse: function(url, params, response) {
                // Store metadata from response
                window['modeTableMeta_' + config.mode_code] = {
                    plan_id: response.plan_id,
                    current_date: response.current_date,
                    is_plan_finished: response.is_plan_finished
                };
                return response.items;
            },
            layout: "fitDataStretch",
            responsiveLayout: "hide",
            pagination: true,
            paginationSize: prefs.pageSize || (window.innerWidth < MOBILE_BREAKPOINT_PX ? PAGE_SIZE_MOBILE : PAGE_SIZE_DESKTOP),
            paginationSizeSelector: PAGE_SIZES,
            paginationCounter: "rows",
            placeholder: config.placeholder || "No pages to review",
            selectable: true,
            selectableRangeMode: "click",
            columns: buildColumns(config, prefs),
            initialSort: prefs.sort ? [prefs.sort] : [{column: "page", dir: "asc"}]
        });

        // Save page size preference
        table.on("pageSizeChanged", function(size) {
            var p = loadPrefs(prefsKey);
            p.pageSize = size;
            savePrefs(prefsKey, p);
        });

        // Save sort preference
        table.on("dataSorted", function(sorters) {
            if (sorters.length > 0) {
                var p = loadPrefs(prefsKey);
                p.sort = {column: sorters[0].field, dir: sorters[0].dir};
                savePrefs(prefsKey, p);
            }
        });

        // Store table reference globally
        window['modeTable_' + config.mode_code] = table;

        // Selection handling for bulk actions
        table.on("rowSelectionChanged", function(data, rows) {
            var count = rows.length;
            var bulkBar = document.getElementById("bulk-bar-" + config.mode_code);
            var countEl = document.getElementById("bulk-count-" + config.mode_code);

            if (bulkBar) {
                bulkBar.style.display = count > 0 ? "flex" : "none";
                if (countEl) countEl.textContent = count;
            }
            window['selectedItems_' + config.mode_code] = data.map(function(row) {
                return row.item_id;
            });
        });

        // Setup tap-to-reveal
        setupTapToReveal(config.table_id);
    }

    /**
     * Handle bulk rating action for mode tables
     */
    window.handleBulkRate = function(modeCode, rating) {
        var selectedItems = window['selectedItems_' + modeCode];
        if (!selectedItems || selectedItems.length === 0) return;

        var meta = window['modeTableMeta_' + modeCode] || {};
        var config = window.tabulatorConfigs[modeCode];

        fetch(config.bulk_rate_url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                item_ids: selectedItems,
                rating: parseInt(rating),
                plan_id: meta.plan_id
            })
        }).then(function(r) {
            if (r.ok) {
                r.json().then(function(result) {
                    updatePagesIndicator(result);
                    // Refresh table and deselect
                    var table = window['modeTable_' + modeCode];
                    table.setData(config.api_url);
                    table.deselectRow();
                });
            }
        });
    };

    /**
     * Handle bulk mark action for NM table
     */
    window.handleBulkMark = function() {
        var selectedItems = window.selectedItems_NM;
        if (!selectedItems || selectedItems.length === 0) return;

        var config = window.tabulatorConfigs.NM;

        fetch(config.bulk_mark_url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ item_ids: selectedItems })
        }).then(function(r) {
            if (r.ok) {
                var table = window.modeTable_NM;
                table.setData(config.api_url);
                table.deselectRow();
            }
        });
    };

    /**
     * Initialize report table (simpler config)
     */
    function initReportTable(config) {
        if (typeof Tabulator === 'undefined') {
            setTimeout(function() { initReportTable(config); }, INIT_DELAY_MS);
            return;
        }

        var prefsKey = 'tabulator_prefs_report';
        var prefs = loadPrefs(prefsKey);

        var modeNames = {
            'FC': 'Full Cycle',
            'SR': 'SRS',
            'DR': 'Daily',
            'WR': 'Weekly',
            'FR': 'Fortnightly',
            'MR': 'Monthly',
            'NM': 'New Memorization'
        };

        var table = new Tabulator('#' + config.table_id, {
            ajaxURL: config.api_url,
            ajaxResponse: function(url, params, response) {
                return response.items;
            },
            layout: "fitDataStretch",
            responsiveLayout: "hide",
            pagination: true,
            paginationSize: prefs.pageSize || (window.innerWidth < MOBILE_BREAKPOINT_PX ? PAGE_SIZE_MOBILE : PAGE_SIZE_DESKTOP),
            paginationSizeSelector: PAGE_SIZES,
            paginationCounter: "rows",
            placeholder: "No revisions found",
            groupBy: "date",
            groupHeader: function(value, count, data, group) {
                var dateTotal = data[0] ? data[0].date_total : 0;
                var d = new Date(value);
                var formatted = d.toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'});
                return formatted + " <span class='badge badge-primary ml-2'>" + dateTotal + " pages</span>";
            },
            columns: [
                { title: "Date", field: "date", visible: false },
                {
                    title: "Mode",
                    field: "mode_code",
                    width: 120,
                    responsive: 0,
                    formatter: function(cell) {
                        var code = cell.getValue();
                        return modeNames[code] || code;
                    }
                },
                { title: "Count", field: "count", width: 80, hozAlign: "center", responsive: 0 },
                {
                    title: "Pages",
                    field: "page_range",
                    minWidth: 150,
                    responsive: 1,
                    formatter: function(cell) {
                        var data = cell.getRow().getData();
                        if (data.revision_ids) {
                            return '<a href="/revision/bulk_edit?ids=' + data.revision_ids + '" class="link link-primary">' + cell.getValue() + '</a>';
                        }
                        return cell.getValue();
                    }
                }
            ],
            initialSort: prefs.sort ? [prefs.sort] : []
        });

        table.on("pageSizeChanged", function(size) {
            var p = loadPrefs(prefsKey);
            p.pageSize = size;
            savePrefs(prefsKey, p);
        });

        table.on("dataSorted", function(sorters) {
            if (sorters.length > 0) {
                var p = loadPrefs(prefsKey);
                p.sort = {column: sorters[0].field, dir: sorters[0].dir};
                savePrefs(prefsKey, p);
            }
        });

        window.reportTable = table;
    }

    // Store configs globally for reference
    window.tabulatorConfigs = window.tabulatorConfigs || {};

    // Auto-init tables when configs are set
    window.initTabulatorTable = function(config) {
        window.tabulatorConfigs[config.mode_code] = config;

        if (config.type === 'report') {
            initReportTable(config);
        } else {
            initModeTable(config);
        }
    };

    /**
     * Sync column toggle checkboxes with saved preferences
     */
    window.syncColumnToggles = function(modeCode, columns) {
        var prefsKey = 'tabulator_prefs_' + modeCode;
        var prefs = loadPrefs(prefsKey);

        if (prefs.columns) {
            columns.forEach(function(col) {
                var toggle = document.getElementById('col-toggle-' + col + '-' + modeCode);
                if (toggle && prefs.columns[col] === false) {
                    toggle.checked = false;
                }
            });
        }
    };

    /**
     * Handle column visibility toggle
     */
    window.toggleColumn = function(modeCode, columnName, checked) {
        var table = window['modeTable_' + modeCode];
        if (table) {
            if (checked) {
                table.showColumn(columnName);
            } else {
                table.hideColumn(columnName);
            }

            var prefsKey = 'tabulator_prefs_' + modeCode;
            var p = loadPrefs(prefsKey);
            p.columns = p.columns || {};
            p.columns[columnName] = checked;
            savePrefs(prefsKey, p);
        }
    };

})();
