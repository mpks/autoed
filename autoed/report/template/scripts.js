import { getPipelineNames, addPipelineToTable, fetchData,
         toggleColumn, populateTable, DataSorter, sortByDatabase,
         sortByABC, activateResizable
        } from "./misc.js";


async function main() {

  const all_data = await fetchData('report_data/autoed_database.json');
  const pipelineNames = getPipelineNames(all_data);

  activateResizable();

  const sortButtons = []

  for (const pipeline of pipelineNames) {
      addPipelineToTable(pipeline);
      toggleColumn(pipeline);
      sortButtons[pipeline] = new DataSorter(pipeline, all_data,
                                                  pipelineNames);
  };
    
  populateTable(all_data, pipelineNames);

  // Add sorting functionality to buttons in Indexed columns
  for (const pipeline of pipelineNames) {
      var sortButton = document.getElementById(`sort_${pipeline}`);
      sortButton.addEventListener(
          'click', function() { sortButtons[pipeline].sort() });
  }
  
  // Add sorting functionality to Index column buttons
  const sorter = new sortByDatabase(all_data, pipelineNames);
  const sort_N_button = document.getElementById('sort_button_N');
  sort_N_button.addEventListener('click', 
      function() { sorter.sort() }
  ); 
 
  // Add sorting functionality to Dataset name buttons
  const nameSorter = new sortByABC(all_data, pipelineNames);
  const sort_dataset_button = document.getElementById('sort_button_dataset');
  sort_dataset_button.addEventListener('click', 
      function() { nameSorter.sort() }
  ); 

}


main();
