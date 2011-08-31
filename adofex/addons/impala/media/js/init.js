// makes footer stick to the bottom of the screen
function positionFooter() {
    $("#footer").css({
        position:
            $(document.body).height() < $(window).height() ? "fixed" : "relative"
    })
}

$(document).ready(positionFooter);
$(window).resize(positionFooter)
// dynamic content might change page height quite unexpectedly
setInterval(positionFooter, 750)
