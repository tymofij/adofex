//Adjust panel height
$.fn.adjustPanel = function(){
    $(this).find("ul, .subpanel").css({ 'height' : 'auto'}); //Reset sub-panel and ul height

    var windowHeight = $(window).height(); //Get the height of the browser viewport
    var panelsub = $(this).find(".subpanel").height(); //Get the height of sub-panel
    var panelAdjust = windowHeight - 100; //Viewport height - 100px (Sets max height of sub-panel)
    var ulAdjust =  panelAdjust - 25; //Calculate ul size after adjusting sub-panel

    if ( panelsub > panelAdjust ) {	 //If sub-panel is taller than max height...
        $(this).find(".subpanel").css({ 'height' : panelAdjust }); //Adjust sub-panel to max height
        $(this).find("ul").css({ 'height' : panelAdjust}); ////Adjust subpanel ul to new size
    } else { //If sub-panel is smaller than max height...
        $(this).find("ul").css({ 'height' : 'auto'}); //Set sub-panel ul to auto (default size)
    }
};

//Execute function on load
$("#chatpanel").adjustPanel(); //Run the adjustPanel function on #chatpanel
$("#alertpanel").adjustPanel(); //Run the adjustPanel function on #alertpanel

//Each time the viewport is adjusted/resized, execute the function
$(window).resize(function () {
    $("#chatpanel").adjustPanel();
    $("#alertpanel").adjustPanel();
});
