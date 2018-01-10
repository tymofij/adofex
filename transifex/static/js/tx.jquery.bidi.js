/* Regular expression to identify RTL chars */
UNICODE_RTL = /[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\u200F]/;

(function($){
    /* Align textareas properly when loaded.
     * Also detect content change in textarea
     * on 'keyup' event and align textarea
     * accordingly.
     * Usage:
     *      $('textarea').bidi();
     *  or
     *      $('textarea').bidi({'css_class': 'foo'});
     */
    $.fn.bidi = function(options) {
        var settings = $.extend({
            'css_class': 'rtl',
            'parent_css_class': 'rtl_wrapper',
        }, options);
        var css_class = settings.css_class;
        var parent_css_class = settings.parent_css_class;
        this.each(function() {
            var textarea = $(this);
            var text = textarea.val();
            if (text) {
                if (UNICODE_RTL.test(text)) {
                    textarea.addClass(css_class);
                    textarea.parent().addClass(parent_css_class);
                }
                else{
                    textarea.removeClass(css_class);
                    textarea.parent().removeClass(parent_css_class);
                }
            }
            textarea.bind('keyup', function(e){
                /* Function to check for RTL content in textarea on some event
                 * and change the orientation of the textarea accordingly
                 */
                var textarea = $(this);
                var text = textarea.val();
                if (text && UNICODE_RTL.test(text)){
                  textarea.addClass(css_class);
                  textarea.parent().addClass(parent_css_class);
                }
                else{
                  textarea.removeClass(css_class);
                  textarea.parent().removeClass(parent_css_class);
                }
            });
        });
    };
})(jQuery);
