function scrollToPlace(event) {
    const table = document.querySelector('#watch_list_table_area');
    const targetColumn = table.querySelector('.column_to_scroll');
    
    if (table && targetColumn) {
        // Get root font size for rem calculation
        const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const leftOffset = 7 * rootFontSize; // 7rem in pixels
        
        const scrollPosition = targetColumn.offsetLeft - leftOffset;
        table.scrollLeft = Math.max(0, scrollPosition);
    }
};

document.addEventListener('htmx:load', scrollToPlace);
document.addEventListener('DOMContentLoaded', scrollToPlace);

