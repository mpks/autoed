const check_icon = '<i class="fa-solid fa-square-check" style="color: green;"> </i>';

function toggleColumns(columnId) {
    const table = document.getElementById('expandableTable');
    const headerRow = table.querySelector('thead tr');
    const bodyRows = table.querySelectorAll('tbody tr');
    //const firstRowCells = document.querySelectorAll('table tr:first-child th');
    const firstRowCells = document.querySelectorAll('table th');

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
        
        let resized_widths = gather_widths_of_resizable(firstRowCells);

        // Collapse columns
        columnsToToggle[columnId].forEach((newCol, idx) => {
            headerRow.removeChild(headerRow.children[columnIndex - 1 - idx]);
            bodyRows.forEach(row => {
                row.removeChild(row.children[columnIndex - 1 - idx]);
            });

        });

        adjustTableWidth(resized_widths, 0);

    } else {

        let resized_widths = gather_widths_of_resizable(firstRowCells);

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
            adjustTableWidth(resized_widths, 0);
        });
    }
}


function gather_widths_of_resizable(headerRow) {

    // const resizable_cells = headerRow.querySelectorAll('.resizable');
    const dictionary = {};
    
    headerRow.forEach(cell => {
        if (cell.classList.contains('resizable')) {
            if (cell.id) {
                const cellWidth = cell.offsetWidth;
                dictionary[cell.id] = cellWidth;
            }   
        }
    });
    console.log('ROW', dictionary);
    return dictionary;
}

function adjustTableWidth(resized_widths, offset) {

  const table = document.querySelector('table');
  const cells = table.querySelectorAll('th');

  console.log('Starting width:', table.style.width)
  let newTableWidth = 0;

  cells.forEach((cell, cell_index, cellsList) => {
    let cellWidth = 1;
    
    if (cell.classList.contains('resizable')) {
        // Use offsetWidth for resizable cells
        if (cell.id) {
            console.log('Passing to A')
            const old_width = resized_widths[cell.id];
            cellWidth = old_width;
            cell.style.width = `${old_width}px`;
        } else {
            console.log('Passing to B')
            cellWidth = cell.offsetWidth;
        }
    } else if (cell.id == 'data_index_id') {
        cellWidth = 50;
        cell.style.width = `${cellWidth}px`;

    } else if (cell.classList.contains('unit_cell')) {
        cellWidth = 100;
        cell.style.width = `${cellWidth}px`;

    } else if (cell.classList.contains('space_group')) {
        cellWidth = 50;
        cell.style.width = `${cellWidth}px`;

    } else if (cell.classList.contains('expandable')) {
     /* (cell.id == 'default_id' || cell.id == 'user_id' ||
               cell.id == 'ice_id' || cell.id == 'max_lattices_id' || 
               cell.id == 'real_space_indexing_id') { */
        cellWidth = 60;   /* Also set it in .expandable style */
        cell.style.width = `${cellWidth}px`;
      
    } else {
      // Use computed style width for non-resizable cells
        cellWidth = get_adjustable_width(cell);
    }
    console.log('cell', cellWidth, cell);
    
    newTableWidth += cellWidth;
  });

  console.log('Summed all widths to: ', newTableWidth);
  const frozenCorner1cell = Array.from(cells).filter(cell => cell.classList.contains('frozen-corner1'))[0];
  const width_before_adjust = get_adjustable_width(frozenCorner1cell);
  console.log('Corner1 width before adjust:', width_before_adjust);
  console.log('Table width before adjust:', table.style.width);

  table.style.width = `${newTableWidth}px`;
  console.log('Table width set to:', `${newTableWidth}`, table.style.width);

  console.log('Resizing the frozen corner to:', width_before_adjust);
  frozenCorner1cell.style.width = `${width_before_adjust}px`;

  console.log('Did table width changed:', table.style.width);
  console.log('Did adjustable changed:', get_adjustable_width(frozenCorner1cell));
}

function get_adjustable_width(cell) {
    const computedStyle = window.getComputedStyle(cell);
    cellWidth = parseFloat(computedStyle.width);
    return cellWidth;
}


async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch data:', error);
        return null;
    }
}

function error_icon(title = null){
    let err_icon = `<i class="fa-solid fa-triangle-exclamation" style="color: red;"></i>`;
    if (title) {
        let err_icon = `<i title="${title}" class="fa-solid fa-triangle-exclamation" style="color: red;"></i>`;
    }
    return err_icon;
}

function strip_dataset_name(dataset_name) {

    const path_array = dataset_name.split('/');
    const yearRegex = /^\d{4}$/; // Regular expression for four digits
    
    let index = 0;
    for (let i = 0; i < path_array.length; i++) {
         if (yearRegex.test(path_array[i])) {
            index = i;
            break;
         }
    }
    
    const filtered_string = path_array.slice(index+3, -1).join('/')
    return filtered_string
}


function populate_cell(dataset_name, row, values, column_name) {


        
    // Create the default cell
    let defaultCell = document.createElement('td');

    if (column_name == 'dataset'){
        
        defaultCell.innerHTML = strip_dataset_name(dataset_name); 
        defaultCell.classList.add('frozen_col1')
        defaultCell.classList.add('resizable')
        row.appendChild(defaultCell);
        return
    }

    if (column_name in values) {
        
        if (values[column_name].sucess) {
            defaultCell.innerHTML = check_icon;
        } else {
            defaultCell.innerHTML = error_icon(values[column_name].tooltip);
        }

    } else {
        defaultCell.textContent = 'NO DATA';
    }
    
    defaultCell.classList.add('cell_value')

    row.appendChild(defaultCell);

}

function make_columns_resizable(){

  document.addEventListener('DOMContentLoaded', () => {
  const table = document.querySelector('#expandableTable');
  const resizableCols = table.querySelectorAll('th.resizable, td.resizable');

  resizableCols.forEach(col => {
    const resizer = document.createElement('div');
    resizer.classList.add('resizer');
    col.appendChild(resizer);
    
    resizer.addEventListener('mousedown', initResize);
  });

  function initResize(event) {
    const resizer = event.target;
    const cell = resizer.parentElement.tagName === 'TH' ? resizer.parentElement : resizer.parentElement;
    const startX = event.clientX;
    const startWidth = cell.offsetWidth;
    const startTableWidth = table.offsetWidth;

    function doResize(event) {
      const newWidth = startWidth + (event.clientX - startX);
      cell.style.width = `${newWidth}px`;

      // Adjust the table width to accommodate the new column width
      const newTableWidth = startTableWidth + (event.clientX - startX);
      table.style.width = `${newTableWidth}px`;
      table.style.overflow = 'auto';
    }

    function stopResize() {
      document.removeEventListener('mousemove', doResize);
      document.removeEventListener('mouseup', stopResize);
    }

    document.addEventListener('mousemove', doResize);
    document.addEventListener('mouseup', stopResize);
  }
  });
}

function populateTable(data) {
    if (!data) {
        console.error('No data to populate the table.');
        return;
    }

    const tableBody = document.querySelector('#expandableTable tbody');
    tableBody.innerHTML = ''; // Clear any existing rows

    let index = 1;
    for (const [dataset, values] of Object.entries(data)) {
        const row = document.createElement('tr');

        const indexCell = document.createElement('td');
        indexCell.textContent = index;
        indexCell.classList.add('frozen_col')
        row.appendChild(indexCell);
        
        // console.log(index, values['default'].tooltip)

        populate_cell(dataset, row, values, 'dataset') 
        populate_cell(dataset, row, values, 'default') 
        populate_cell(dataset, row, values, 'user') 
        populate_cell(dataset, row, values, 'ice') 
        populate_cell(dataset, row, values, 'max_lattices') 
        populate_cell(dataset, row, values, 'real_space_indexing') 

        // Append the row to the table body
        tableBody.appendChild(row);
        index++;
    }
}

async function initializeTable() {
    const data = await fetchData('autoed_database.json');
    console.log(data);
    populateTable(data); 
    console.log('Success!');
}



initializeTable();
//make_columns_resizable();
