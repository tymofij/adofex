
function toggle_entries(entries_status){
    /*
    Toggle entries of the online translation form filtering the rows by the
    status of each entry.
    */
    $('.'+entries_status).each(function(){
        if($("input[name='show_"+entries_status+"']").is(':checked')){
            $(this).removeClass('hidden_field');
        } else {
            $(this).addClass('hidden_field');
        }
    })
};

$(document).ready(function(){

  $(".tablesorter.teamlist").tablesorter({
    sortList: [[1,1],[0,0]],
    textExtraction: function(node) {
      switch (node.cellIndex){
          case 0:
              return $("a:first", node).text();
          // Stats column
          case 1:
              return $(".stats_string_resource", node).text();
          // Last update column
          case 2:
              return $("span", node).attr('unixdate');
          default: return node.innerHTML;
      }
    }        
  });
  
  $(".tablesorter.resdetail").tablesorter({
    sortList: [[1,1]],
    headers: {
      1: { sorter: 'percent' },
      2: { sorter: 'number' },

    },
    textExtraction: function(node) {  
      switch (node.cellIndex){
        case 0:
            return $("span:first strong", node).text();
        // Stats column
        case 1:
          return $(".stats_string_resource", node).text();
        // Last update column
        case 2:
          return $("span", node).attr('unixdate');
        // Priority column
        default: return node.innerHTML;
      }
    } 
  });

  $(".tablesorter.reldetail").tablesorter({
      sortList: [[1,1]],
      widgets: ['zebra'],
      headers: {
          1: { sorter: 'percent' },
          2: { sorter: 'number' }
      },
      textExtraction: function(node) {
          switch (node.cellIndex){
              case 0:
                  return $("a:first", node).text();
              // Stats column
              case 1:
                  return $(".stats_string_resource", node).text();
              // Last update column
              case 2:
                  return $("span", node).attr('unixdate');
              default: return node.innerHTML;
          }
      }
  });
    
    
  $(".tablesorter.langdetail").tablesorter({
    sortList: [[1,1]], 
    headers: {
      1: { sorter: 'percent' },
      2: { sorter: 'number' },
      3: { sorter: 'number' }
    },
    textExtraction: function(node) {  
      switch (node.cellIndex){
        case 0:
            return $("span:first", node).text();
        // Stats column
        case 1:
            return $(".stats_string_resource", node).text();
        // Last update column
        case 2:
            return $("span", node).attr('unixdate');
        // Priority column
        case 3:
            return $(".priority_sort", node).text()
        default: return node.innerHTML;
      }
    } 
  });





  // ordering for Web editing form table
  $("#trans_web_edit").tablesorter({
      widgets: ['zebra'],
      headers: {
          2: { sorter: false },
          4: { sorter: false },
          5: { sorter: false },
          6: { sorter: false },
      },
  });

});
