function switch_extra_columns_by_default(){
//    toggleColumn('default');
//    toggleColumn('user');
}

function toggleColumn(column_id) {
    const indDiv = document.getElementById(`${column_id}_indexed`);
    toggle_div(indDiv);
    const ucDiv = document.getElementById(`${column_id}_unit_cell`);
    toggle_div(ucDiv);
    const groupDiv = document.getElementById(`${column_id}_space_group`);
    toggle_div(groupDiv);
}

function toggle_div(someDiv) {
    if (someDiv.style.display === 'none') {
      someDiv.style.display = 'block';
    } else {
      someDiv.style.display = 'none';
    }
}

function activate_resizable(){
    const resizable = document.querySelector('.resizable');
    const resizer = document.querySelector('.resizer');

    let isResizing = false;

    resizer.addEventListener('mousedown', function(e) {
      isResizing = true;
    });

    document.addEventListener('mousemove', function(e) {
      if (isResizing) {
        const newWidth = e.clientX - resizable.getBoundingClientRect().left;
        resizable.style.width = newWidth + 'px';
      }
    });

    document.addEventListener('mouseup', function() {
      isResizing = false;
    });
}


function set_the_width_of_second_column() {
  window.addEventListener('load', function() {
  const div1 = document.getElementById('col1');
  const div2 = document.getElementById('col2');

  const div1Height = div1.offsetHeight;
  div2.style.height = div1Height + 'px';
});
}

function adjust_column_height() {
  window.addEventListener('load', function() {

    const columns = document.querySelectorAll('.column');
    columns.forEach(column => {
      const items = column.querySelectorAll('.cell');
      let totalHeight = 0;
      items.forEach(item => {
        totalHeight += item.offsetHeight;
      });
      totalHeight = totalHeight + 0;
      column.style.height = totalHeight + 'px';
    });
  });
}

function clearTable(){

  console.log('In clear table');
  var cells = document.querySelectorAll('.cell:not(.header)');
  console.log('Selected cells: ', cells);

  cells.forEach(function(cell) {
    console.log('Removing', cell);
    cell.parentNode.removeChild(cell);
  });
}

function error_icon(title = null){

    let err_icon;
    if (title != null) {
        err_icon = `<i title="${title}" class="fa-solid fa-triangle-exclamation info" style="color: red;"></i>`;
    } else {
        err_icon = `<i title="None" class="fa-solid fa-triangle-exclamation info" style="color: red;"></i>`;
    }
    return err_icon;
}

function check_icon(title = null){

    let chck_icon;
    if (title) {
        chck_icon = `<i title="${title}" class="fa-solid fa-square-check info" style="color: green;"> </i>`;
    } else {
        chck_icon = '<i title="None" class="fa-solid fa-square-check info" style="color: green;"> </i>';
    } 
    return chck_icon;
}

function snow_icon(title = null){
    let icon;
    if (title) {
        icon = `<i title="${title}" class="fa-regular fa-snowflake info" style="color: #4d8dff;"> </i>`;
    } else {
        icon = `<i title="None" class="fa-regular fa-snowflake info" style="color: #4d8dff;"> </i>`;
    } 
    return icon;
}


function populateTable(data) {

    if (!data) {
        console.error('No data to populate the table.');
        return;
    }

    var table = document.getElementById('table');

    let index = 1;
    for (const [dataset_name, values] of Object.entries(data)) {
        
        add_cell('col1', dataset_name, index, values);
        add_cell('col2', dataset_name, index, values);
        add_cell('default', dataset_name, index, values);
        add_cell('user', dataset_name, index, values);
        add_cell('ice', dataset_name, index, values);
        add_cell('real_space_indexing', dataset_name, index, values);
        index++;
    }
    
    // var column_2 = document.getElementById('col2');
    // var resizer = document.createElement('div');
    // resizer.classList.add('resizer');
    // column_2.appendChild(resizer);
}

function add_cell(column_name, dataset_name, index, values) {
    
    var column = document.getElementById(column_name); 

    var cell = document.createElement('div');
    cell.classList.add('cell');

    if (column_name == 'col1') {
        cell.innerText = index;
    } else if (column_name == 'col2') {

        cell.classList.add("frozen_column_02");
        cell.innerHTML = strip_dataset_name(dataset_name);

    } else if (column_name == 'default') {

        add_checkmark(cell, values, column_name);
        add_expandable_info(column_name, values);

    } else if (column_name == 'user') {

        add_checkmark(cell, values, column_name);
        add_expandable_info(column_name, values);

    } else if (column_name == 'ice') {

        add_checkmark(cell, values, column_name);
        add_expandable_info(column_name, values);

    } else if (column_name == 'real_space_indexing') {

        add_checkmark(cell, values, column_name);
        add_expandable_info(column_name, values);
        
    } else {

        cell.innerText = 'OK';
    }

    column.appendChild(cell);
}

function add_checkmark(cell, values, name) {

        const status = values[name]['status'];
        const tooltip = values[name]['tooltip'];

        if (status == 'OK') {
            if (name == 'ice'){
            cell.innerHTML = snow_icon(title=tooltip);
            } else {
            cell.innerHTML = check_icon(title=tooltip);
            }
        } else if (status == 'process_error') {
            if (name == 'ice'){
            cell.innerHTML = ` `;
            } else {
            cell.innerHTML = error_icon(title=tooltip);
            }
        } else if (status == 'no_data') {
            cell.innerHTML = `<i title="Missing data" class="fa-solid fa-circle-xmark" style="color: #BFBFBF;"> </i>`;

        } else {
            cell.innerHTML = `<i title="Failed to parse output" class="fa-solid fa-circle-question" style='color: gray;'></i>`;

        }
}

function formatNumber(num, decimals, width) {
    // Convert the number to a string with one decimal place
    let formatted = num.toFixed(decimals);

    // Pad the string with a space if it's less than 4 characters long
    while (formatted.length < width) {
        formatted = '&nbsp;'.repeat(width - formatted.length) + formatted;
    }

    return formatted;
}

function add_expandable_info(column_name, values) { 

  var result = values[column_name];

  var uc_cell = document.createElement('div');
  var space_group = document.createElement('div');
  var indexed = document.createElement('div');

  uc_cell.classList.add('cell');
  space_group.classList.add('cell');
  indexed.classList.add('cell');

  if (result['status'] == 'OK') {
    var uc = result.unit_cell
    let uc_str = `&nbsp;${formatNumber(uc[0], 1, 4)}&nbsp; `;
    uc_str += `${formatNumber(uc[1], 1, 4)}&nbsp; `;
    uc_str += `${formatNumber(uc[2], 1, 4)}\&nbsp; `;
    uc_str += `\(${formatNumber(uc[3], 0, 3)} `;
    uc_str += `${formatNumber(uc[4], 0, 3)} `;
    uc_str += `${formatNumber(uc[5], 0, 3)}\)`;
    uc_cell.innerHTML = uc_str;
    console.log('UNIT', uc_str);
    space_group.innerHTML = `&nbsp;` + result.space_group;
    indexed.innerHTML = 'NONE';
  } else {
    let uc_str = `---&nbsp; `;
    uc_str += `---&nbsp; `;
    uc_str += `---&nbsp; `;
    uc_str += `\(---`;
    uc_str += `---`;
    uc_str += `---\)`;
    // uc_cell.innerHTML = uc_str;
    // space_group.innerHTML = '---';
    uc_cell.innerHTML = ` `;
    indexed.innerHTML = ` `;
  }
  console.log('VALS', result.unit_cell);
  var indexed_column = document.getElementById(`${column_name}_indexed`);
  var uc_column = document.getElementById(`${column_name}_unit_cell`);
  var sg_column = document.getElementById(`${column_name}_space_group`);
  uc_column.appendChild(uc_cell);
  sg_column.appendChild(space_group);
  indexed_column.appendChild(indexed);
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


async function initializeTable() {
    console.log('Initializing table');
    const data = await fetchData('autoed_database.json');
    console.log('Data', data);
    populateTable(data);
    console.log('Table populated');
}


  // switch_extra_columns_by_default();
  activate_resizable();
  initializeTable();
  // adjust_column_height();
  // clearTable();
  console.log('Done')


//set_the_width_of_second_column();
