function handleEvents(event) {
    // Apply logic to each row that has any checked checkboxes
    document.querySelectorAll('tbody tr').forEach(row => {
        const hasChecked = row.querySelector('input[type="checkbox"]:checked');
        if (hasChecked) {
            updateVisibility(hasChecked);
        }
    });
};

document.addEventListener('htmx:load', handleEvents);
document.addEventListener('DOMContentLoaded', handleEvents);


function updateVisibility(checkbox) {
    const row = checkbox.closest('tr');
    const cells = Array.from(row.querySelectorAll('td')).slice(3); // Skip first three cell (page, count and button)
    const isGraduated = row.querySelector('input[name="is_checked"]').checked
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
    const earliestChecked = Math.max(...checkedPositions);
    const latestChecked = Math.min(...checkedPositions);

    cells.forEach((cell, index) => {
        const checkbox = cell.querySelector('input[type="checkbox"]');
        const span = cell.querySelector('span');

        if (checkbox.checked) {
            // Always show checked checkboxes
            checkbox.classList.remove('hidden');
            span.classList.add('hidden');
        } else if (isGraduated) {
            // If the row is graduated, show all unchecked checkboxes
            checkbox.classList.add('hidden');
            span.classList.remove('hidden');

        } else {
            // Hide unchecked checkboxes that are before earliest or between earliest and latest
            if (index > earliestChecked || (index < earliestChecked && index > latestChecked)) {
                checkbox.classList.add('hidden');
                span.classList.remove('hidden');
            } else {
                checkbox.classList.remove('hidden');
                span.classList.add('hidden');
            }
        }
    });
}



// This function is to handle the shift + click selection of checkboxes
// So that the user can select multiple checkboxes in a row
// Where they want to select the related pages at once 
function handleShiftClick(e, clsName) {
    // Custom event which will add data in the backend for the checkboxes
    const event = new Event('change', {
        bubbles: true,
        cancelable: true
    });
    // Handle shift+click selection
    if (e.shiftKey) {
        const checkboxes = [...document.querySelectorAll('.' + clsName)];
        const currentCheckboxIndex = checkboxes.indexOf(e.target);

        // loop through the checkboxes backwards untll we find one that is checked
        for (let i = currentCheckboxIndex; i >= 0; i--) {

            if (i != currentCheckboxIndex && checkboxes[i].checked) { break; }
            if (!checkboxes[i].disabled) {
                // If the checkbox is not disabled, check it and dispatch the event
                checkboxes[i].checked = true;
                checkboxes[i].dispatchEvent(event);
            }
        }
    }

}