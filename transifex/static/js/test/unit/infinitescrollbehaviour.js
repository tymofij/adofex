$(function(){
	module('txn.infinitescrollbehaviour.js');
	test('DOM Behabiour', function() {
		options = {
		    infScrollSelector: "#stat-row-container",
		    scrollWidth: '980px',
		    scrollHeight: '520px'
		  };

	    infScrollOptions = {
	        navSelector     : ".pagination",
	        nextSelector    : ".pagination a:first",
	        itemSelector    : "#stat-row-container tr",
	        debug           : false,
	        loading: {
	          finishedMsg   : "",
	          msgText       : "Fetching more resources.." ,
	      }
	    };
	 $("#t01").infscrollbehaviour(options, infScrollOptions);

	equal( $('.pagination').css('display'), 'none', 'Pagination should be hidden');
	equal( $('.jscrollwrapper').css('min-width'), options.scrollWidth, 'jscrollwrapper min-width should much passed options');
	equal( $('.jscrollwrapper').css('height'), options.scrollHeight, 'jscrollwrapper height should much passed options');

	})

})