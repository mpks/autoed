var missing_data_icon = `<i class="fa-solid fa-circle-xmark" style="color: #BFBFBF;"></i>`;
var failed_to_parse_icon = `<i class="fa-solid fa-circle-question" style='color: gray;'></i>`;



export function toggleColumn(column_id) {
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



function makeHeaderCell(pipelineName, idSuffix,
                        cellText, cellClasses, headerClasses) {

    const table = document.getElementById("table");
    const cell = document.createElement("div");
    const header = document.createElement("div");

    header.innerHTML = cellText;

    cell.id = `${pipelineName}${idSuffix}`;
    cell.classList.add(...cellClasses);
    header.classList.add(...headerClasses);
    header.id = `${pipelineName}${idSuffix}_header`;

    cell.appendChild(header);
    table.appendChild(cell);
    return [cell, header];
}



export function addPipelineToTable(pipeline) {

    const [indexCell, indexHeader] = makeHeaderCell(
        pipeline, '_indexed', "Indexed <br>",
        ['column'], ['cell', 'header']);
    makeHeaderCell(pipeline, '_unit_cell', "Unit cell",
                   ['column'], ['cell', 'header']);

    makeHeaderCell(pipeline, '_space_group', "Space<br>group",
                   ['column'], ['cell', 'header']);
    const [cell, header] = makeHeaderCell(
        pipeline, '', pipeline, ['column', 'expandable'],
        ['cell', 'header', 'color_header']);

    header.onclick = function(){ toggleColumn(pipeline) };

    // Add sort button to Indexed column
    const sortButton = document.createElement("span");
    sortButton.classList.add('sort-icon');
    sortButton.classList.add('clickable-span');
    sortButton.id = `sort_${pipeline}`;
    sortButton.style = "color: orange; text-align: center;";
    sortButton.innerHTML = "&nbsp;&nbsp;&#x25B2;&#x25BC;";
    indexHeader.appendChild(sortButton);
}



export function activateResizable(){
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
  var cells = document.querySelectorAll('.cell:not(.header)');
  cells.forEach(function(cell) {
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



function image_icon(file_location){
    const img_icon = ` <a href="${file_location}" target="_blank"><i class="fa-solid fa-camera info" style="color: #aebafb;"> </i>`;
    return img_icon;
}



function check_icon(title = null, location = null, color="green"){

    let chck_icon;
    if (title) {
        if (location) {
            chck_icon = ` <a href="${location}" target="_blank"><i title="${title}" class="fa-solid fa-square-check info" style="color: ${color};"> </i>`;
        } else {
            chck_icon = ` <i title="${title}" class="fa-solid fa-square-check info" style="color: ${color};"> </i>`;
        }
    } else {
        if (location) {
        chck_icon = `<a href="${location}" target="_blank"><i title="None" class="fa-solid fa-square-check info" style="color: ${color};"> </i>`;
        } else {
        chck_icon = `<i title="None" class="fa-solid fa-square-check info" style="color: ${color};"> </i>`;
        }
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



export function populateTable(data, pipelines) {

    if (!data) {
        console.error('No data to populate the table.');
        return;
    }

    var table = document.getElementById('table');

    let index = 1;
    for (const [dataset_name, values] of Object.entries(data)) {
        
        add_cell('col1', dataset_name, index, values);
        add_cell('col2', dataset_name, index, values);
        add_cell('beam', dataset_name, index, values);
        add_cell('spots', dataset_name, index, values);
        
        for (const pipeline of pipelines) {
            add_cell(pipeline, dataset_name, index, values);
        }
        index++;
    }
    
}



function add_cell(column_name, dataset_name, index, values) {
    
  var column = document.getElementById(column_name); 
  var cell = document.createElement('div');

  cell.classList.add('cell');

  if (column_name == 'col1') {

      // Add index number to the first column
      cell.innerText = index;

  } else if (column_name == 'col2') {

      cell.classList.add("frozen_column_02");
      cell.innerHTML = strip_dataset_name(dataset_name);

  } else if (column_name == 'beam') {

      if (values['beam_image'] != null) {
          cell.innerHTML = image_icon(values['beam_image']);
      } else {
          cell.innerHTML = ' ';
      }

  } else if (column_name == 'spots') {

      if (values['spots_image'] != null) {
          cell.innerHTML = image_icon(values['spots_image']);
      } else {
          cell.innerHTML = ' ';
      }

  } else {
      add_checkmark(cell, values, column_name);
      add_expandable_info(column_name, values);
  }

  column.appendChild(cell);

}



function check_for_ice(uc) {
    // 001 
    let com1 = Math.abs(uc[0] - 4.4) < 0.2 &&
                Math.abs(uc[1] - 4.4) < 0.2 &&
                Math.abs(uc[2] - 7.2) < 0.6 &&
                Math.abs(uc[3] - 90) < 2 &&
                Math.abs(uc[4] - 90) < 2 &&
                Math.abs(uc[5] - 120) < 9

    // 010 
    let com2 = Math.abs(uc[0] - 4.4) < 0.2 &&
                Math.abs(uc[1] - 7.2) < 0.6 &&
                Math.abs(uc[2] - 4.4) < 0.2 &&
                Math.abs(uc[3] - 90) < 2 &&
                Math.abs(uc[4] - 120) < 9 &&
                Math.abs(uc[5] - 90) < 2
    // 100 
    let com3 = Math.abs(uc[0] - 7.2) < 0.6 &&
                Math.abs(uc[1] - 4.4) < 0.2 &&
                Math.abs(uc[2] - 4.4) < 0.2 &&
                Math.abs(uc[3] - 120) < 9 &&
                Math.abs(uc[4] - 90) < 2 &&
                Math.abs(uc[5] - 90) < 2
    
    return com1 || com2 || com3
}



function add_checkmark(cell, values, name) {

  let run_status = 'no_data';
  let tooltip = '';
  let link = '';

  if (name in values) {
      run_status = values[name]['status'];
      tooltip = values[name]['tooltip'];
      link = values[name]['link'];
  };

  let xia2_report_location = null;

  if (run_status == 'OK') {
      if (name == 'ice'){
          cell.innerHTML = snow_icon(tooltip);
      } else {
          // Check if unit cell is close to that of ice
          // and color the check mark in blue
          let uc = values[name]['unit_cell']
          let color = "green"

          if (check_for_ice(uc)) {
              color = "#4d8dff";
          };

          cell.innerHTML = check_icon(tooltip, link, color);
      }
  } else if (run_status == 'process_error') {
      if (name == 'ice'){
          cell.innerHTML = ` `;
      } else {
          cell.innerHTML = error_icon(tooltip);
      }
  } else if (run_status == 'no_data') {
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

  // Write the percentage of indexed spots, the unit cell and space
  // group into the table

  var run_status = 'no_data';

  if (column_name in values) {
      var result = values[column_name];
      var run_status = result['status'];
  }

  var uc_cell = document.createElement('div');
  var space_group = document.createElement('div');
  var indexed = document.createElement('div');

  uc_cell.classList.add('cell');
  space_group.classList.add('cell');
  indexed.classList.add('cell');
  indexed.classList.add('info');

  if (run_status == 'OK') {

    var uc = result.unit_cell
    
    if  (result.indexed !== null && result.total_spots !== null){
        var index_percent = result.indexed * 100. / result.total_spots;
        var index_str = `${formatNumber(index_percent, 0, 3)}%`;
        var index_tooltip = `${result.indexed} / ${result.total_spots}`;
    } else {
        var index_str = ` ??`;
        var index_tooltip = `? / ?`;
    }
    let uc_str = `&nbsp;${formatNumber(uc[0], 1, 4)}&nbsp; `;
    uc_str += `${formatNumber(uc[1], 1, 4)}&nbsp; `;
    uc_str += `${formatNumber(uc[2], 1, 4)}\&nbsp; `;
    uc_str += `\(${formatNumber(uc[3], 0, 3)} `;
    uc_str += `${formatNumber(uc[4], 0, 3)} `;
    uc_str += `${formatNumber(uc[5], 0, 3)}\)`;
    uc_cell.innerHTML = uc_str;
    space_group.innerHTML = `&nbsp;` + result.space_group;

    indexed.innerHTML = index_str;
    indexed.title = index_tooltip;

  } else {
    uc_cell.innerHTML = ` `;
    indexed.innerHTML = ` `;
    space_group.innerHTML = ` `;
  }

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

  let selectElement = document.getElementById("session_select");
  if (selectElement.value == 'all') {
      const filtered_string = path_array.slice(index+1, -1).join('/')
      return filtered_string
  } else {
      const filtered_string = path_array.slice(index+3, -1).join('/')
      return filtered_string
  }
}



export async function fetchData(url) {

    try {
         const response = await fetch(url);
         if (!response.ok) {
            throw new Error('Network response was not ok ' +
                            response.statusText);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Failed to fetch data:', error);
        return null;
    }
}



function get_percent(entry, pipeline) {
    var  percent = 0.0;
    if (pipeline in entry) {
        percent = 100. * entry[pipeline].indexed / entry[pipeline].total_spots;
        if (isNaN(percent)) { percent = 0.0; }
    }
    return percent;
}



function sortByIndexed(pipeline, data) {
    let original_data = Object.entries(data);
    original_data.sort(([, a], [, b]) => get_percent(b, pipeline) - get_percent(a, pipeline)); 
    let sorted_data = Object.fromEntries(original_data);
    return sorted_data;
}



export function DataSorter(pipeline, data, allPipelines) {
  this.pipeline = pipeline;
  this.sortedData = sortByIndexed(pipeline, data);
  this.reversed = Object.fromEntries(Object.entries(this.sortedData).reverse());
  this.allPipelines = allPipelines;
  this.sortedAscending = false;
  
  this.sort = function() {
      this.sortedAscending = !this.sortedAscending;
      clearTable();
      if (this.sortedAscending) {
         populateTable(this.sortedData, allPipelines);
      } else {
         populateTable(this.reversed, allPipelines);
      }
  };

}



export function sortByDatabase(data, allPipelines) {
  // Sort data based on how they are written in the database
  this.original_data = data;
  let reversed_temp = Object.entries(data).reverse();
  this.reversed = Object.fromEntries(reversed_temp);
  this.sortedAscending = true;

  this.sort = function() {
      this.sortedAscending = !this.sortedAscending;
      clearTable();
      if (this.sortedAscending) {
         populateTable(this.original_data, allPipelines);
      } else {
         populateTable(this.reversed, allPipelines);
      }
  };
}



export function sortByABC(data, allPipelines) {

  this.sorted = sortByName(data);
  let reversed_temp = Object.entries(this.sorted).reverse();
  this.reversed = Object.fromEntries(reversed_temp);
  this.sortedAscending = true;

  this.sort = function() {
      this.sortedAscending = !this.sortedAscending;
      clearTable();
      if (this.sortedAscending) {
         populateTable(this.reversed, allPipelines);
      } else {
         populateTable(this.sorted, allPipelines);
      }
  };
}



function sortByName(data) {
  let original_data = Object.entries(data);
  original_data.sort((a, b) => {
      let str1 = strip_dataset_name(a[0]);
      let str2 = strip_dataset_name(b[0]);
      return str1.localeCompare(str2, undefined, { numeric: true });
  });
    
  let sorted_data = Object.fromEntries(original_data);
  return sorted_data;
}



function extractUniqueDatasetNames(in_data) {

  let data = Object.entries(in_data);
  const uniqueNames = new Set();

  data.forEach(([key, value]) => {
    const parts = key.split('/');
    
    // Find the first occurrence of the year in the path
    // This is considered a starting point for the session
    const yearRegex = /\b\d{4}\b/;
    let yearIndex = parts.findIndex(part => yearRegex.test(part));
    if (yearIndex !== -1 && yearIndex + 1 < parts.length) {
      // Extract the dataset name from the year part, and the next part
      const datasetName = `${parts[yearIndex]}/${parts[yearIndex + 1]}`;
      uniqueNames.add(datasetName);
    }
  });

  return Array.from(uniqueNames);
}



export function getPipelineNames(in_data) {
  // Goes through JSON database and finds all the pipeline names
  let data = Object.entries(in_data);
  const uniquePipelines = new Set();
  data.forEach(([datasetName, datasetValue]) => {
      let dataValues = Object.entries(datasetValue);
      dataValues.forEach(([key, value]) => {
          if (typeof value == 'object') {
              if ("title" in value) {
                  uniquePipelines.add(value.title);
              };
          };
      });
  });
  return uniquePipelines
}
