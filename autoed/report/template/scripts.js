
function toggleColumn() {
    const myDiv = document.getElementById('default');
    if (myDiv.style.display === 'none') {
      myDiv.style.display = 'block';
    } else {
      myDiv.style.display = 'none';
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
      column.style.height = totalHeight + 'px';
    });
  });
}

activate_resizable();
adjust_column_height();
//set_the_width_of_second_column();
