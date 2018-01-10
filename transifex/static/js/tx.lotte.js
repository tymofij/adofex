/* TranslationString class which stores information about one translation string */
function TranslationString(parent, id, source_string, translated_string, context,occurrence) {
    this.parent = parent;
    this.id = id;
    this.context = context;
    this.occurrence = occurrence;
    this.source_string = source_string;
    this.translated_string = translated_string;
    this.modified = false;
    this.toString = function() {
        return "TranslationString(" + this.id + ", '" + this.source_string + "', '" + this.translated_string + "');";
    }

    this.checkVar = function(v) {
        return (typeof v === 'undefined' || !v); // Check whether v is undefined or empty
    }

    this.isModified = function() {
        return this.modified;
    }
    this.isUntranslated = function() {
        return this.checkVar(this.translated_string);
    }
    this.isTranslated = function() {
        return !this.checkVar(this.translated_string);
    }
    this.translate = function(new_string) {
        if (new_string != this.translated_string) {
            this.translated_string = new_string;
            this.modified = true;
            this.parent.updateStats(true); // Issue statistics update with delay
        }
    }

    this.push = function() {
        this.parent.push(this);
    }

    this.flagString = function() {
        if (this.modified) {
            return "fuzzy";
        } else if (this.checkVar(this.translated_string)) {
            return "untranslated";
        } else {
            return "translated";
        }
    }
}


/* StringSet class which stores list of translation strings and maps them to visible table */
function StringSet(json, push_url, from_lang, to_lang) {
/*    bindings[table_row_index] = TranslationString();*/
    this.to_lang = to_lang;
    this.bindings = [];

/*    Visible table offset*/
    this.offset = 0;

/*    Timer for stats */
    this.update_stats_timer = null;
    this.strings = []
    this_stringset = this;
/*    Initialize strings from JSON data*/
    var i = 0;
    for(var index in json[0]['strings']) {
      var string = json[0]['strings'][index];
      this_stringset.strings[i] = new TranslationString(this, string['id'], string['original_string'], string['translations'][to_lang], string['context'], string['occurrence']);
      i++;
    }
    this.filtered = this.strings;

    /* StringSet.bindToTable(target_table_id) */
    this.bindToTable = function(target_table_id) {
        this.bound_table = $("table#" + target_table_id);
    }

    this.push = function(ts) {
        this_stringset = this;
        var to_update = [];
        if (ts) { /* Pushing one TranslationString instance */
            to_update[0] = {'string':ts.source_string,'context':ts.context,'value':ts.translated_string, "occurrence":ts.occurrence};
        } else { /* Pushing all TranslationString instances from current StringSet */
            for (i=0; i<this.strings.length; i++)
                if (this_stringset.strings[i].modified == true) {
                    to_update.push( {"string":this.strings[i].source_string,"context":this.strings[i].context,"value":this.strings[i].translated_string, "occurrence":this.strings[i].occurrence});
				}
        }
        if (to_update == {} && to_add == {}) {
        } else {
            $.ajax({
				url: push_url,
				type: 'PUT',
				contentType: "application/json",
				dataType: 'text',
				data: JSON.stringify({language:this_stringset.to_lang, strings:to_update}),
				success: function(stat, dict){
				    /* This is a final variable accessed outside of callback */
				    if(ts)
				        ts.modified = false;
				    else
				        /* For save_all button */
    					for (j=0; j<this_stringset.strings.length; j++) {
    							this_stringset.strings[j].modified = false;
    					}
					this_stringset.updateView();
					this_stringset.updateStats();
				}
			});
		}
	}

    this.updateView = function() {
        /* The view subset of strings is based on table size */
        /* We clone tbody here so we can replace the old one in all at once not row by row */
        var table_body = $("tbody", this.bound_table).clone();
        var table_rows = $("tr", table_body);
        var items_per_view = table_rows.length;

        /* Push stuff from this.strings to the table */
        for(i=0; i< items_per_view; i++) {
            table_row = table_rows[i];
            if (i + this.offset < this.filtered.length) {
                s = this.filtered[i + this.offset];
                this.bindings[i] = s; // Bind string to table row
                $("td.num", table_row).html(s.id); // Set string number
                $("td.msg", table_row).text(s.source_string); // Set source string
                textarea = $("td.trans textarea", table_row);
                textarea.val(s.translated_string);
                textarea.removeClass("fuzzy translated untranslated").addClass(s.flagString());

                /* Toggle per string save button */
                button_save = $("td.notes span.save", table_row);
                if (s.modified)
                    button_save.show();
                else
                    button_save.hide();

                $(table_row).show();
            } else {
                this.bindings[i] = null;
                $(table_row).hide();
            }

        }
        $("tbody", this.bound_table).replaceWith(table_body);

        /* Bind textarea editing to strings */
        var this_stringset = this;
        $('tr td textarea', table_body).keyup(function() {
            id = parseInt($(this).attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            string = this_stringset.bindings[id];
            string.translate($(this).val());
            if (string.modified) {
                $(this).removeClass("fuzzy translated untranslated").addClass("fuzzy"); // Automatically set edited textarea to fuzzy
                $('tbody tr td.notes span#save_' + id).show();
            }
        });

        /* Bind save button events */
        $('tr td.notes span.save', table_body).click(function() {
            table_row_id = parseInt($(this).attr("id").split("_")[1]); // Get the id of current save button
            this_stringset.bindings[table_row_id].push();
        });

        /* Bind Machine translation */
        if (is_supported_lang && is_supported_source_lang) {
            $('tr td.suggest_container a.suggest', table_body).click(function() {
                var a=$(this), str=a.html();
                a.removeClass("action");
                a.addClass("action_go");
                orig=$('.msg', a.parents('tr')).html();
                trans=$('textarea', a.parents('tr'));
                orig = unescape(orig).replace(/<br\s?\/?>/g,'\n').replace(/<code>/g,'').replace(/<\/code>/g,'').replace(/&gt;/g,'>').replace(/&lt;/g,'<');
                google.language.translate(orig, source_lang, target_lang, function(result) {
                    if (!result.error) {
                        trans.val(unescape(result.translation).replace(/&#39;/g,'\'').replace(/&quot;/g,'"').replace(/%\s+(\([^\)]+\))\s*s/g,' %$1s '));
                        /* Mark the translated field as modified */
                        id = parseInt(trans.attr("id").split("_")[1]); // Get the id of current textarea -> binding index
                        string = this_stringset.bindings[id];
                        string.translate(trans.val());
                        if (string.modified) {
                            trans.removeClass("fuzzy translated untranslated").addClass("fuzzy"); // Automatically set edited textarea to fuzzy
                            $('tbody tr td.notes span#save_' + id).show();
                        }
                    } else {
                        a.before($('<span class="alert">'+result.error.message+'</span>'))
                    }
                    a.removeClass("action_go");
                    a.addClass("action");
                });
                return false;
            });
        } else {
            $('tr td.suggest_container', table_body).hide()
        }

        /* Bind mouseenter/leave event on textarea for tools */
        $('tr td textarea', table_body).each(function(){
          $(this).qtip({
             content: links[$(this).attr('id').split('translation_')[1]],
             position: 'topRight',
             hide: {
                fixed: true // Make it fixed so it can be hovered over
             },
             style: {
                'font-size': '0.8em',
                padding: '10px', // Give it some extra padding
                border: {
                width: 0,
                radius: 0
                },
             }
          });
        });

    }

    /* StringSet.filter(); */
    this.filter = function(filter_string) {
        j = 0;

        conModified = false;
        conTranslated = false;
        conUntranslated = false;

        $('tr td input[type=checkbox]:checked', this.bound_stats).each(function(){
            if ($(this).attr("id") == "only_translated") {
                conTranslated = true;
            }
            if ($(this).attr("id") == "only_fuzzy") {
                conModified = true;
            }
            if ($(this).attr("id") == "only_untranslated") {
                conUntranslated = true;
            }
        });

        this.filtered = [];

        for (i=0; i<this.strings.length; i++) {
            s = this.strings[i];
            status_passed = (conModified && s.isModified() ||
                (!s.isModified()) && (conUntranslated && s.isUntranslated() ||
                conTranslated && s.isTranslated()))
            if (status_passed) {
                // The user has specified search string, so filter among passed strings
                if (filter_string)
                    if ((!s.source_string ||
                         s.source_string.search(filter_string) == -1) &&
                        (!s.translated_string ||
                         s.translated_string.search(filter_string) == -1))
                        continue; // Jump to next for loop
                this.filtered[j] = s;
                j++;
            }
        }
        this.offset = 0; /* Reset offset */
        this.updateView(); /* Refresh view */
        this.updatePagination(); /* Refresh pagination */
    }

    /* StringSet.bindPagination(target_div_id) */
    this.bindPagination = function(target_div_id) {
        var container = $("#" + target_div_id);
        this.bound_pagination = container;
    }


    /* StringSet.updatePagination()
    * Updates bound pagination div
    */
    this.updatePagination = function() {
        var items_per_view = $("tbody tr", this.bound_table).length;
        var pages = Math.ceil(this.filtered.length/items_per_view);
        var this_stringset = this;
        this.bound_pagination.paginate({
            'count' : pages,
            'display' : 25, /* How many page selectors to show */
            'border' : true,
            'start' : 1, /* Initial page */
            'text_color' : '#333333',
            'background_color' : '#f5f5f5',
            'border_color' : '#cccccc',
            'text_hover_color' : '#000000',
            'background_hover_color' : '#ffffff',
            'border_hover_color' : '#000000',
            'onChange' : function(offset) {
                this_stringset.offset = (offset-1)*items_per_view;
                this_stringset.updateView();
            }
        });
    }


    /* StringSet.bindSearchField(target_input_text_id) */
    this.update_search_timer = null;
    this.bindSearchField = function(target_id){
        var this_stringset = this;
        var target_elem = $("input#" + target_id);
        target_elem.keyup(function(){
           clearTimeout(this_stringset.update_search_timer);
           this_stringset.update_search_timer = window.setTimeout(function() { this_stringset.filter($(target_elem).val()); }, 1000);
        });

    };

    /* StringSet.bindStats(target_table_id) */
    this.bindStatsAndFilter = function(target_table_id) {
        this_stringset = this; /* Workaround for this overriding */
        table = $("table#" + target_table_id);
        this.bound_stats = table
        $('tr td input[type="checkbox"]', table).click(function(){
            this_stringset.filter();
            this_stringset.updateView();
        });
    };

    /* StringSet.updateStats(later=false) */
    this.updateStats = function(later) {
        var this_stringset = this;
        if (later) {
            clearTimeout(this.update_stats_timer);
            this.update_stats_timer = window.setTimeout(function() { this_stringset.updateStats(); }, 1000);
        } else {
            this.translated = 0;
            this.untranslated = 0;
            this.modified = 0;
            for (i=0; i<this.strings.length; i++) {
                j = this.strings[i];
                if (j.modified) {
                    this.modified += 1;
                } else if (j.checkVar(j.translated_string)) {
                    this.untranslated += 1;
                } else {
                    this.translated += 1;
                }
            }
            if (this.bound_stats) {
                $('#total_sum', this.bound_stats).html(stringset.strings.length);
                $('#total_translated', this.bound_stats).html(stringset.translated);
                $('#total_translated_perc', this.bound_stats).html(sprintf("%.02f%%", stringset.translated*100.0/stringset.strings.length));
                $('#total_fuzzy', this.bound_stats).html(stringset.modified);
                $('#total_fuzzy_perc', this.bound_stats).html(sprintf("%.02f%%", stringset.modified*100.0/stringset.strings.length));
                $('#total_untranslated', this.bound_stats).html(stringset.untranslated);
                $('#total_untranslated_perc', this.bound_stats).html(sprintf("%.02f%%", stringset.untranslated*100.0/stringset.strings.length));
            }
        }
    }

}


