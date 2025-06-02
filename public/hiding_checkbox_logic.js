function handleEvents(event) {
    // Apply logic to each row that has any checked checkboxes
    isGlobalChecked = document.getElementById("showAll").checked
    if (!isGlobalChecked) {
        document.querySelectorAll('tbody tr').forEach(row => {
            const hasChecked = row.querySelector('input[type="checkbox"]:checked');
            if (hasChecked) {
                updateVisibility(hasChecked);
            }
        });
    };
};

document.addEventListener('htmx:load', handleEvents);
document.addEventListener('DOMContentLoaded', handleEvents);

function updateVisibility(checkbox) {
    const row = checkbox.closest('tr');
    const cells = Array.from(row.querySelectorAll('td')).slice(2, -1); // Skip first two cell (page and count)

    // Get all checked checkboxes in this row
    const checkedCells = cells.filter(cell => cell.querySelector('input[type="checkbox"]').checked);

    if (checkedCells.length === 0) {
        // If no checkboxes are checked, show all checkboxes and hide all spans
        cells.forEach(cell => {
            cell.querySelector('input[type="checkbox"]').classList.remove('hidden');
            cell.querySelector('span').classList.add('hidden');
        });
        return;
    }

    // Find earliest and latest checked positions
    const checkedPositions = checkedCells.map(cell => cells.indexOf(cell));
    const earliestChecked = Math.min(...checkedPositions);
    const latestChecked = Math.max(...checkedPositions);

    cells.forEach((cell, index) => {
        const checkbox = cell.querySelector('input[type="checkbox"]');
        const span = cell.querySelector('span');

        if (checkbox.checked) {
            // Always show checked checkboxes
            checkbox.classList.remove('hidden');
            span.classList.add('hidden');
        } else {
            // Hide unchecked checkboxes that are before earliest or between earliest and latest
            if (index < earliestChecked || (index > earliestChecked && index < latestChecked)) {
                checkbox.classList.add('hidden');
                span.classList.remove('hidden');
            } else {
                checkbox.classList.remove('hidden');
                span.classList.add('hidden');
            }
        }
    });
}

function toggleShowAll(globalCheckbox) {
    const showAll = globalCheckbox.checked;
    const allCheckboxes = document.querySelectorAll('tbody input[type="checkbox"]');
    const allSpans = document.querySelectorAll('tbody span');

    if (showAll) {
        // Show all checkboxes, hide all spans
        allCheckboxes.forEach(checkbox => checkbox.classList.remove('hidden'));
        allSpans.forEach(span => span.classList.add('hidden'));
    } else {
        // Reapply visibility rules for each row
        document.querySelectorAll('tbody tr').forEach(row => {
            const firstCheckbox = row.querySelector('input[type="checkbox"]');
            if (firstCheckbox) {
                updateVisibility(firstCheckbox);
            }
        });
    }
}