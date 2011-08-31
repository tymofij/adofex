// sets initial footer position, updates it on resizes

function positionFooter() {
    // Lotte breaks it, loading content afterwards
    // and I do not want to put listeners there
    if (typeof lotteStatus == "undefined")
        $("#footer").css({
            position:
                $(document.body).height() < $(window).height() ? "fixed" : "relative"
        })
}

$(window).bind("load", function() {
  positionFooter();

  $(window).resize(positionFooter)
});
