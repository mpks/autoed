function toggleColumns(columnId) {
    const table = document.getElementById('expandableTable');
    const headerRow = table.querySelector('thead tr');
    const bodyRows = table.querySelectorAll('tbody tr');

    // Define columns to expand or collapse
    const columnsToToggle = {
        'default_id': ['space_group', 'unit_cell'],
        'user_id': ['space_group', 'unit_cell'],
        'ice_id': ['space_group', 'unit_cell'],
        'max_lattices_id': ['space_group', 'unit_cell'],
        'real_space_indexing_id': ['space_group', 'unit_cell']
    };
    
    const ExpandTitle = {
        'unit_cell': 'Unit<br>cell',
        'space_group': 'Space<br>group'
    }

    const DefaultValue = {
        'unit_cell': '11.2  13.4  15.6 (60 70 120)',
        'space_group': 'P 1'
    }
    
    // Check if the columns are already added
    const isExpanded = headerRow.querySelector(`th.${columnId}_extra`);
    const columnIndex = Array.from(headerRow.children).findIndex(th => th.id === columnId);

    if (isExpanded) {
        // Collapse columns
        columnsToToggle[columnId].forEach((newCol, idx) => {
            headerRow.removeChild(headerRow.children[columnIndex - 1 - idx]);
            bodyRows.forEach(row => {
                row.removeChild(row.children[columnIndex - 1 - idx]);
            });
        });
    } else {
        // Expand columns
        columnsToToggle[columnId].forEach((newCol, idx) => {
            
            // Expand the first row
            const newTh = document.createElement('th');
            newTh.innerHTML = ExpandTitle[newCol];
            newTh.classList.add(`${columnId}_extra`, 'frozen_row', `${newCol}`);
            headerRow.insertBefore(newTh, headerRow.children[columnIndex]);
            
            // Expand all the other rows
            bodyRows.forEach(row => {
                const newTd = document.createElement('td');
                newTd.innerText = DefaultValue[newCol];
                newTd.classList.add('expanded_data', `${newCol}`)
                row.insertBefore(newTd, row.children[columnIndex]);
            });
        });
    }
}

