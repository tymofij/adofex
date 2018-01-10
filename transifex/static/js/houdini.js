$(document).ready(function() {
  $('.houdini_toggler').click(function() {
    var houdini = $(this).next(".houdini");
    if ( houdini.is(':hidden') ) {
      houdini.show("slide");
    } else {
      houdini.hide("slide");
    }
  })
});
