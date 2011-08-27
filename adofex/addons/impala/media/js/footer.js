// sets initial footer position, updates it on resizes
$(window).bind("load", function() {
  positionFooter();

  function positionFooter() {
    $("#footer").css({
       position:
         $(document.body).height() < $(window).height() ? "fixed" : "relative"
       })
    }
    $(window).resize(positionFooter)
});
