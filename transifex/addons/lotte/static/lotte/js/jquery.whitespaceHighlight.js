(function ($){

    var methods = {
        highlight : function( options ) {

            return this.each(function(){
                var new_value = "";
                // The string which will be marked.
                var elem = $(this);
                var string = elem.html();

                // [\f\n\r\t\v\u00A0\u2028\u2029]
                var reWhiteSpaceStartSpace = new RegExp(/(^\u00A0+)|(^\u0020+)/g);
                var reWhiteSpaceEndSpace = new RegExp(/(\u00A0+$)|(\u0020+$)/g);
                var reWhiteSpaceSpace = new RegExp(/\u00A0{2,}|\u0020{2,}/g);
                var reWhiteSpaceNewLine = new RegExp(/\n/g);
                var reOtherWhiteSpace = new RegExp(/[\f\r\t\v\u2028\u2029]/g);

                // First trim spaces (if startswith, endwith space chars)
                var matchedStartSpace = reWhiteSpaceStartSpace.exec(string);
                var startSpaces;
                if(matchedStartSpace){
                    startSpaces = matchedStartSpace[0].replace(
                        new RegExp(/\u00A0|\u0020/g),
                        '<span class="whitespace space" title="Space"> </span>');
                    // left trim
                    string = string.replace(reWhiteSpaceStartSpace, "");
                }
                var matchedEndSpace = reWhiteSpaceEndSpace.exec(string);
                var endSpaces;
                if(matchedEndSpace){
                    endSpaces = matchedEndSpace[0].replace(
                        new RegExp(/\u00A0|\u0020/g),
                        '<span class="whitespace space" title="Space"> </span>');
                    // right trim
                    string = string.replace(reWhiteSpaceEndSpace, "");
                }

                // Find the middle space sequences
                var matchedSpace = string.match(reWhiteSpaceSpace);
                var seqs = [];
                if(matchedSpace){
                    for (i=0; i<matchedSpace.length; i++){
                        seqs[i] = matchedSpace[i].replace(
                            new RegExp(/\u00A0|\u0020/g),
                            '<span class="whitespace space" title="Space"> </span>');
                    }
                    splitted = string.split(reWhiteSpaceSpace)
                    string = "";
                    for (i=0; i<seqs.length; i++){
                        string += splitted[i]+seqs[i];
                    }
                    // Concat the last piece (Always step into this if)
                    if(i == splitted.length-1)
                        string += splitted[i]
                }

                // Join the start, end spaces
                if(startSpaces)
                    string = startSpaces + string
                if(endSpaces)
                    string = string + endSpaces;

                var matchedNewLine = reWhiteSpaceNewLine.exec(string);
                // Mark the whitespace chars with <span> tags.
                string = string.replace(reWhiteSpaceNewLine,
                    '<span class="whitespace newline" title="New line">⏎</span>'+matchedNewLine);

                var matchedOther = reOtherWhiteSpace.exec(string);
                string = string.replace(reOtherWhiteSpace,
                    '<span class="whitespace other" title="Tab">&raquo</span>');

                // Put back the html code
                elem.html(string);
            });
        },
        // WARNING: This function is NOT CHAINABLE!!!
        reset : function(){
                var obj = $('<div>'+this.html()+'</div>');
                // Restrict searching in obj context searching
                $(".whitespace.space", obj).replaceWith(' ');
                // Empty it, as we have included the original new line after span!!!
                $(".whitespace.newline", obj).replaceWith('');
                // Reset tab space
                $(".whitespace.other[title='Tab']", obj).replaceWith('\t');

                // TODO: Reset all the other whitespace chars!!!
                return obj.html();
        }
    };

    $.fn.whitespaceHighlight = function(method){

        // Method calling logic
        if ( methods[method] ) {
          return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
          return methods.highlight.apply( this, arguments );
        } else {
          $.error( 'Method ' +  method + ' does not exist.' );
        }

    }

})(jQuery);
