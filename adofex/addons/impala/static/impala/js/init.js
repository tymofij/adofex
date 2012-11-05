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

// hack to make people who log in from home page (projects) go directly to dashboard
$(function(){
    var a = $("#header_secnav > a").first()
    if (a.attr('href') == "/accounts/signin/?next=/projects/") {
        a.attr('href', "/accounts/signin/?next=/projects/myprojects/")
    }
})