/*
 * Name: tx.infinitescrollbehaviour.js
 *
 * Description: This jQuery plugin adds a container div to the target element
 * (used as a scroll content container) as well asa jScrollPane scrollbar
 * The target elements loads more data, via AJAX, utilizing the infinitescroll
 * plugin.
 *
 * DEPENDENCIES:
 * - jquery
 * - jquery.infinitescroll.js
 * - jquery.mousewheel.js
 * - mwheelIntent.js
 * - jquery.jscrollpane.js
 * - jquery.jscrollpane.css
*/

(function ($, window, undefined){

  $.fn.infscrollbehaviour = function(options, infScrollOptions){
    var  opts = $.extend({}, $.fn.infscrollbehaviour.defaults, options);

    return this.each(function(){
      var $this = $(this)
        , $jScrollWrapper;

       /* ================== Table Container ================== */

      var $jScrollWrapper = $('<div class="jscrollwrapper"></div>')
      .css({  'min-width': opts.scrollWidth, //use min-width because width breaks with jscrollpane
              'height': opts.scrollHeight,
              'overflow-y': 'scroll',
              'overflow-x': 'visible',
              'padding-bottom': '20px'
          });

       //get reference to scrollwrapper with the new content it containes
       $jScrollWrapper = $this.wrap($jScrollWrapper).parent();


      /* ================== jScrollPane Scrolling Behaviour =====================*/


      //start jscrollpane for beautiful scrollbars
      $jScrollWrapper
        .on('jsp-scroll-y', jscrollBehaviour)
        .jScrollPane();


      function jscrollBehaviour(event, scrollPositionY, isAtTop, isAtBottom){
        if(isAtBottom){
          $jScrollWrapper.off('jsp-scroll-y');
          $(opts.infScrollSelector).infinitescroll('retrieve');
        }
      }

    /* ================== Infinite Scroll ================== */


	// hide pagination the first time, cause infinite scroll can't manage to ;-)
    $(infScrollOptions.navSelector).hide();

    /* call infinite scroll plugin to load more rows when user reaches end of page
     * To see what the available infScrollOptions are , visit infinitescroll documentation
     * or take a peak at at the jquery.infinitescroll.js file.
    */
    $(opts.infScrollSelector).infinitescroll( infScrollOptions, function(newElements){

       // redraw scrollbar and reassign scroll listener and handler
        if(typeof $jScrollWrapper !== 'undefined'){
          $jScrollWrapper.css('padding-bottom', '0px');
          $jScrollWrapper.data('jsp').reinitialise();
          $jScrollWrapper.on('jsp-scroll-y', jscrollBehaviour);
        }

      });


      //wait for drawing cause our bar is sensitive :-)
      setTimeout(function(){
        $jScrollWrapper.data('jsp').reinitialise();

        $jScrollWrapper.find('.jspVerticalBar').animate({opacity:0.2}, 0);

        //pause infinitescroll
        $('#stat-row-container').infinitescroll('pause');
      },50)


      /* ================== Document Scrolling Behavior =====================*/
      $jScrollWrapper
        .on('mouseleave.scrollbehaviour', function(){
          $('.jscrollwrapper .jspVerticalBar').stop().animate({opacity:0.2}, 300)
        })
        .on('mouseenter.scrollbehaviour', function(){
          $('.jscrollwrapper .jspVerticalBar').stop().animate({opacity:1}, 200)
        })
        .on('mousewheel.scrollbehaviour', function(event, delta){
          event.stopPropagation()
          event.preventDefault();
        })

    });
  }

  /* ================== Default Options =====================*/

  $.fn.infscrollbehaviour.defaults = {
    infScrollSelector: "#stat-row-container",
    scrollWidth: '980px',
    scrollHeight: '520px'
  };


})(jQuery, window, document)




