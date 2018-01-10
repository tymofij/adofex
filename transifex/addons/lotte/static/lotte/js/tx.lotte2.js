/*
Class to store the Status (in the client-side) of a Lotte instance that a
translator opens up.

For not it's only used for ActionLog purposes on the server side, whenever
the Save & Exit button is pressed in Lotte.
*/
function LotteStatus(){
    /* Set to true whenever someone pushes a translation to the server */
    this.updated = false;
}
lotteStatus = new LotteStatus();

function _canonical_lang_code(lang_code) {
    if (lang_code.indexOf('_') != -1 || lang_code.indexOf('-') != -1) {
        lang_code = lang_code.substring(0, 2);
    }
    return lang_code;
}

function auto_translate_wrapper(text, src_lang, dest_lang, callback) {
    var result = '';
    data = {
        'q': text,
        'source': _canonical_lang_code(src_lang),
        'target': dest_lang,
    };
    $.getJSON(autotranslate_url, data, function(response) {
        if (response.error) {
           result = {
               'error': response.error.message
           }
        } else {
            if (autotranslate_type == 'GT') {
              result = {
                  'translation': response.data.translations[0].translatedText
              }
            }
            else if (autotranslate_type = 'BT'){
              result = {
                 'translation': response[0].TranslatedText
              }
            }
        }
        callback(result);
    });
}

function auto_translate_supported(source, target, callback) {
    $.getJSON(supportedlangs_url, {'target': target}, function(response) {
        if (!response.error) {
            if (autotranslate_type == "GT"){
              source = _canonical_lang_code(source)
              $.each(response.data.languages, function(k, v) {
                  if (source == v.language) {
                      callback();
                      return false;
                  }
              })
            }
            else if (autotranslate_type == "BT"){
              source = _canonical_lang_code(source)
              target = _canonical_lang_code(target)
              if ($.inArray(source, response)>=0 && $.inArray(target, response)>=0) {
                callback();
                return false;
              }
            }
        }
    });
}

function saveButtonClickHandler() {
    table_row_id = parseInt($(this).attr("id").split("_")[1]); // Get the id of current save button
    this_stringset.push(this_stringset.strings[table_row_id], table_row_id);
}

function refreshSpellcheckDiv() {
  new_str = "";
  $.each(str_as_list, function(index, value){
    if ($.inArray(index, error_indices) > -1) {
      new_str += '<a class="bad_word" href="#" error_index=' + index + '>'+ value + '</a>';
    }
    else
      new_str += value;
  });
  $spellcheckDiv.html(new_str);
  $spellcheckDiv.html(function(index, old) {
    return old.replace(/\n/g, '\n<br />');
  });
  $spellcheckDiv.whitespaceHighlight();
  $spellcheckTextarea.val(str_as_list.join(""));
  $spellcheckTextarea.keyup();
  $('a.bad_word').bind('click', showSuggestionBox);
}

function spellcheckButtonClickHandler(e) {
    if (typeof $suggestBox != 'undefined')
      $suggestBox.remove();
    if (typeof $spellcheckButtonClicked != 'undefined') {
      $spellcheckButtonClicked.unbind('click');
      $spellcheckButtonClicked.bind('click', spellcheckButtonClickHandler);
    }
    $('div.spellcheckdiv').siblings('textarea').show();
    $('div.spellcheckdiv').remove();
    $spellcheckButtonClicked = $(this);
    table_row_id = parseInt($(this).attr("id").split("_")[1]); // Get the id of current spellcheck button
    var string = this_stringset.strings[table_row_id].translated_strings.other;
    $spellcheckTextarea = $(this).parents('tr').find('textarea.translation.default_translation');
    $.ajax({
      type: 'POST',
      url: spellcheck_url,
      data: JSON.stringify({'text': string}),
      dataType: 'json',
      cache: false,
      error: function(XHR, status, error) {
        alert('Sorry, there was an error in processing the request.');
      },
      success: function(json) {
        if (!json.length) {
          alert("There is no incorrectly spelled word.");
          return;
        }
        str_as_list = [];
        bad_words = {};
        error_indices = [];
        var start=0;
        for (i in json) {
          str_as_list.push(string.substr(start, json[i][0][0]-start));
          str_as_list.push(string.substr(json[i][0][0], json[i][0][1]));
          start = json[i][0][0] + json[i][0][1];
          error_indices.push(str_as_list.length-1);
          bad_words[str_as_list.length-1] = [json[i][1], json[i][2]];
        }
        str_as_list.push(string.substr(start));
        $spellcheckDiv = $('<div></div>')
          .addClass('spellcheckdiv')
          .height($spellcheckTextarea.height())
          .width($spellcheckTextarea.innerWidth());
        $spellcheckTextarea.hide();
        $spellcheckDiv.insertAfter($spellcheckTextarea);
        refreshSpellcheckDiv();
        $spellcheckButtonClicked.unbind('click');
        $spellcheckButtonClicked.bind('click', destroySpellcheckDiv);
      }
    });
}

function destroySpellcheckDiv() {
  if (typeof $suggestBox != 'undefined')
    $suggestBox.remove();
  $spellcheckDiv.siblings('textarea').show();
  $spellcheckDiv.remove();
  $spellcheckButtonClicked.unbind('click');
  $spellcheckButtonClicked.bind('click', spellcheckButtonClickHandler);
}

function showSuggestionBox(e) {
  e.preventDefault();
  var offset = $(this).offset();
  var index = parseInt($(this).attr('error_index'));
  offset.top = offset.top + 16;
  e.preventDefault();
  $('div.spellcheck-suggestbox').remove();
  $suggestBox = $('<div></div>').addClass('spellcheck-suggestbox');
  $suggestBox.hide();
  var $suggestWords = $('<div></div>').addClass('spellcheck-suggestbox-words');
  $suggestBox.append($suggestWords);
  var $suggestFoot = $('<div></div>').addClass('spellcheck-suggestbox-foot');
  $suggestBox.append($suggestFoot);
  $('body').append($suggestBox);
  var suggested_words = bad_words[parseInt($(this).attr('error_index'))][1];
  $.each(suggested_words, function(i, value) {
    $suggestWords.append('<a class="suggested_word spellcheck-word-highlight" error_index=' + index + ' href="#">'+value+'</a>');
  });
  $suggestFoot.append('<a class="ignore spellcheck-word-highlight" bad_word="' + bad_words[index][0] + '"error_index=' + index + ' href="#">Ignore</a>');
  $suggestFoot.append('<a class="ignore_all spellcheck-word-highlight" bad_word="' + bad_words[index][0] + '" error_index=' + index + ' href="#">Ignore all</a>');
  $suggestBox.css({
    opacity: 1,
    width: "auto",
  });
  $suggestBox.offset(offset);
  $suggestBox.fadeIn(200);
  $('a.suggested_word').bind('click', replaceWord);
  $('a.ignore').bind('click', ignoreWord);
  $('a.ignore_all').bind('click', ignoreAll);
  $(document).bind('click', function(e) {
    (!$(e.target).hasClass('spellcheck-word-highlight') &&
     !$(e.target).parents().filter('.spellcheck-suggestbox').length) &&
     !$(e.target).hasClass('bad_word') &&
      $suggestBox.remove();
  });
}

function ignoreWord(e) {
  e.preventDefault();
  var index = parseInt($(this).attr('error_index'));
  str_as_list[index] = bad_words[index][0];
  error_indices.splice(error_indices.indexOf(index), 1);
  delete bad_words[index];
  refreshSpellcheckDiv();
  $suggestBox.remove();
  if (!error_indices.length)
    destroySpellcheckDiv();
}

function ignoreAll(e) {
  e.preventDefault();
  error_indices = [];
  bad_words = {};
  refreshSpellcheckDiv();
  $suggestBox.remove();
  destroySpellcheckDiv();
}

function replaceWord(e) {
  e.preventDefault();
  var index = parseInt($(this).attr('error_index'));
  str_as_list[index] = $(this).text();
  error_indices.splice(error_indices.indexOf(index), 1);
  delete bad_words[index];
  refreshSpellcheckDiv();
  $suggestBox.remove();
  if (!error_indices.length)
    destroySpellcheckDiv();
}

function undoButtonClickHandler() {
    var table_row_id = parseInt($(this).attr("id").split("_")[1]); // Get the id of current undo button
    var string = this_stringset.strings[table_row_id];
    var undo_value = string.load_default;
    var tr = $(this).parents('tr');
    tr.find('span.rule').each(function(i){
        rule = $(this).attr('rule');
        string.translate(undo_value[rule], rule);
        $(this).next('textarea').focus().val(undo_value[rule]).keyup();
    });
    // Save the new value
    string.push();
    $(this).addClass('inactive');
    $(this).unbind('click');
}

/* TranslationString class which stores information about one translation string */
function TranslationString(parent, id, source_strings, translated_strings, source_entity, context, occurrence) {

    // The StringSet holding it
    this.parent = parent;

    // The id of the default source string!
    this.id = id;

    // The context of the SE
    this.context = context;

    // The occurrence of the SE
    this.occurrence = occurrence;

    // The source strings (includes the default and the plurals)
    this.source_strings = source_strings

    // The translation (includes the default and the plurals)
    this.translated_strings = translated_strings

    // The corresponding source_entity string (we call it "Key")
    this.source_entity = source_entity;

    // holds the previous values at each given time (these values are updated on save)
    this.previous = jQuery.extend(true, {}, this.translated_strings);

    // For undo purposes!
    this.load_default = jQuery.extend(true, {}, this.translated_strings);

    // are any of the textareas modified?
    this.modified = false;

    this.toString = function() {
        return "TranslationString(" + this.id + ", '" + this.source_strings + "', '" + this.translated_strings + "');";
    }

    // Check whether textarea values are undefined or empty
    this.checkVar = function(v) {
        for(key in v){
            if(typeof v[key] === 'undefined' || !v[key]){
                return true;
            }
        }
        return false;
    }

    this.isModified = function() {
        return this.modified;
    }
    this.isUntranslated = function() {
        return this.checkVar(this.translated_strings);
    }
    this.isTranslated = function() {
        return !this.checkVar(this.translated_strings);
    }
    this.translate = function(new_string, rule) {
        if (new_string != this.translated_strings[rule]) {
            if (!this.modified){
                if (this.translated_strings[rule] == "") {
                    this.parent.untranslated_modified += 1;
                } else {
                    this.parent.translated_modified += 1;
                }
            }
            this.translated_strings[rule] = new_string;
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
        } else if (this.checkVar(this.translated_strings)) {
            return "untranslated";
        } else {
            return "translated";
        }
    }
}


/* StringSet class which stores list of translation strings and maps them to visible table */
function StringSet(json_object, push_url, from_lang, to_lang) {

    /* hold the current editing textarea object */
    this.current_box = null;
		this.current_string = null;
		this.current_row = null;
		this.must_push = null;
		this.current_id = null;
/*    The target language*/
    this.to_lang = to_lang;
    /* True if there is error during saving translations */
    this.error = null;

/*    This array contains all the TranslationString objects of StringSet */
/*    IMPORTANT! This keeps the table row index as a key!!! */
    this.strings = []

    this_stringset = this;

/*    Timer for stats */
    this.update_stats_timer = null;

/*    Initialize strings from JSON data*/
    var i = 0;
    for(var index in json_object['aaData']) {
      var row = json_object['aaData'][index];
      this_stringset.strings[i] = new TranslationString(this, row[0], row[2]["source_strings"], row[3], row[1], null, null);
      i++;
    }
    this.filtered = this.strings;

    /* StringSet.bindToTable(target_table_id) */
    this.bindToTable = function(target_table_id) {
        this.bound_table = $("table#" + target_table_id);
    }

    // Method for pushing one or more TranslationStrings of this StringSet
    this.push = function(ts, textarea_id, callback) {
        var messages = false;
        this_stringset = this;
        var to_update = [];
        if (ts) { /* Pushing one TranslationString instance */
            to_update[0] = {'id':ts.id,
                            'translations':ts.translated_strings,}; // translations includes all plurals!
        } else { /* Pushing all TranslationString instances from current StringSet */
            for (i=0; i<this.strings.length; i++)
                if (this_stringset.strings[i].modified == true) {
                    to_update.push( {'id':this.strings[i].id,
                                     'translations':this.strings[i].translated_strings,}); // translations includes all plurals!
                }
        }
        if (to_update.length == 0) {
            if (typeof callback === 'undefined')
                alert("Alrighty, all strings have been saved already");
        } else {

            $("div#notification-container div").html("Saving...");
            $("div#notification-container").fadeIn("slow");

            $.ajax({
                url: push_url,
                data: JSON.stringify({strings: to_update}),
                dataType : "text", // "json" is strict and we get 500
                type: "POST",
                contentType: "application/json",
                async: false,
                success: function(data, textStatus){ // jquery 1.4 includes xmlhtttpreq

                    var json_response_dict = JSON.parse(data);
                    var textarea_container = $("textarea#translation_" + textarea_id).parents("div.translation_wrapper");
                    // Update the object classes, and the overall statistics
                    if(ts) {
                        var status_code = json_response_dict[ts.id]['status'];
                        if (status_code == 200){
                            ts.modified = false;
                            if (ts.isUntranslated()) {
                                stringset.translated -= 1;
                                stringset.untranslated += 1;
                            } else if (ts.checkVar(ts.previous)) {
                                stringset.translated += 1;
                                stringset.untranslated -= 1;
                            }
                            // Deep copy of the array
                            ts.previous = jQuery.extend(true, {}, ts.translated_strings);

                            // Hide the error div if it is visible
                            if ( json_response_dict[ts.id]['message'] != null ) {
                                messages=true;
                                textarea_container.parents('td.trans').find('div.error_notes').text(json_response_dict[ts.id]['message']);
                                textarea_container.parents('td.trans').find('div.error_notes').addClass('warning_notes');
                                textarea_container.parents('td.trans').find('div.error_notes').show();
                            } else
                                textarea_container.parents('td.trans').find('div.error_notes').hide();
                                stringset.error = false;
                        }else{ // Handle the error
                            textarea_container.parents('td.trans').find('div.error_notes').text(json_response_dict[ts.id]['message']);
                            textarea_container.parents('td.trans').find('div.error_notes').show();
                            stringset.error = true;
                        }
                    } else {
                        /* For save_all button */
                        for (j=0; j<this_stringset.strings.length; j++) {
                            if (this_stringset.strings[j].modified) {
                                if(json_response_dict[this_stringset.strings[j].id]['status'] == 200){
                                    if ( this_stringset.strings[j].isUntranslated()) {
                                        stringset.translated -= 1;
                                        stringset.untranslated += 1;
                                    } else if ( this_stringset.strings[j].checkVar(
                                        this_stringset.strings[j].previous)) {
                                        stringset.translated += 1;
                                        stringset.untranslated -= 1;
                                    }
                                    this_stringset.strings[j].modified = false;
                                    // Deep copy of the array
                                    this_stringset.strings[j].previous =  jQuery.extend(true, {}, this_stringset.strings[j].translated_strings);

                                    if ( json_response_dict[this_stringset.strings[j].id]['message'] != null ) {
                                        messages=true;
                                        $('textarea#translation_'+j).parents('td.trans').find('div.error_notes').text(json_response_dict[this_stringset.strings[j].id]['message']);
                                        $('textarea#translation_'+j).parents('td.trans').find('div.error_notes').addClass('warning_notes');
                                        $('textarea#translation_'+j).parents('td.trans').find('div.error_notes').show();
                                    } else {
                                        // Hide the error div if it is visible
                                        $('textarea#translation_'+j).parents('td.trans').find('div.error_notes').hide();
                                    }
                                    stringset.error = false;
                                }else{ // Handle the error
                                    messages=true;
                                    $('textarea#translation_'+j).parents('td.trans').find('div.error_notes').text(json_response_dict[this_stringset.strings[j].id]['message']);
                                    $('textarea#translation_'+j).parents('td.trans').find('div.error_notes').show();
                                    stringset.error = true;
                                }
                            }
                        }
                    }
                    // Update the color classes now
                    this_stringset.updateColors_Buttons();
                    stringset.translated_modified = 0;
                    stringset.untranslated_modified = 0;
                    // Update the stats too!
                    this_stringset.updateStats(true);
                    // Change status to updated=True
                    lotteStatus.updated=true;
                },
                error: function() {
                    alert("Error saving new translation.");
                },
                complete: function(){
                    setTimeout('$("div#notification-container").fadeOut();',1000);
                }
            });
        }
        if (typeof callback === 'function') {
            if ( ! messages )
                callback(lotteStatus.updated);
            else
                alert("There were a few warnings or errors. Check them out before exiting lotte.");
        }
    }

    /* Update the color classes for textareas and show/hide save buttons */
    this.updateColors_Buttons = function() {
        $('tr td textarea.default_translation', this.bound_table).each(function (i) {
            var textarea = $(this);
            var id = parseInt(textarea.attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            var string = this_stringset.strings[id];
            var new_class = this_stringset.strings[id].flagString();
            var source_entity_id = $('#sourceid_' + id).text();
            var review_checkbox = $('#review_source_' + source_entity_id);
            /* Apply the new class to the default string and all its siblings! */
            textarea.parents('td.trans').find('textarea').removeClass("fuzzy translated untranslated").addClass(new_class);

            /* Toggle per string save button */
            button_save = $("span#save_"+id);
           	button_spellcheck = $("span#spellcheck_"+id);
            if (string.modified) {
                button_save.removeClass('inactive');
                button_save.unbind('click');
                button_save.bind('click', saveButtonClickHandler);
            }
            else{
                if (string.isTranslated()) {
                    review_checkbox.removeAttr('disabled');
                }
                button_save.addClass('inactive');
                button_save.unbind('click');
            }
            str = string.translated_strings.other.toString();
            if (enable_spellcheck && str != ""){
                button_spellcheck.removeClass('inactive');
                button_spellcheck.unbind('click');
                button_spellcheck.bind('click', spellcheckButtonClickHandler);
            }
            else{
                button_spellcheck.addClass('inactive');
                button_spellcheck.unbind('click');
            }
        });
    };

    /* Bind textarea keyup marking */
    this.bindKeyupTextArea = function() {
        var edit_handler = function() {
            var textarea = $(this);
            var id;
            if(textarea.hasClass('default_translation')){
              id = parseInt(textarea.attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            }else{
              id = parseInt(textarea.parents('td.trans').find('.default_translation').attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            }
            string = this_stringset.strings[id];
            string.translate(textarea.val(), textarea.prev('span.rule').attr('rule'));
            if (string.modified) {
                // Automatically set edited textareas to fuzzy
                textarea.parents('td.trans').find('textarea').removeClass("fuzzy translated untranslated").addClass("fuzzy");
				var saveButton = textarea.parents('tr').find('span#save_' + id);
                saveButton.removeClass('inactive');
                saveButton.unbind('click');
                saveButton.bind('click', saveButtonClickHandler);
				var undoButton = textarea.parents('tr').find('span#undo_' + id);
                undoButton.removeClass('inactive');
                undoButton.unbind('click');
                undoButton.bind('click', undoButtonClickHandler);
				if (enable_spellcheck){
               		var spellcheckButton = textarea.parents('tr').find('span#spellcheck_' + id);
                    spellcheckButton.removeClass('inactive');
                    spellcheckButton.unbind('click');
                    spellcheckButton.bind('click', spellcheckButtonClickHandler);
                }
                var source_entity_id = $('#sourceid_' + id).text();
                var review_checkbox = $('#review_source_' + source_entity_id);
                review_checkbox.removeAttr('checked');
                review_checkbox.attr('disabled', 'disabled');
            }
        }

        $('tr td textarea.translation', this.bound_table).keyup(edit_handler);
        $('tr td textarea.translation', this.bound_table).bind('paste', edit_handler);
        $('tr td textarea.translation', this.bound_table).change(edit_handler);
    }

    /* Bind save button events */
    this.bindSaveButton = function() {
        $('tr td.notes span.save', this.bound_table).click(saveButtonClickHandler);
    }

    /* Bind spellcheck button */
    this.bindSpellcheckButton = function() {
       $('tr td.notes span.spellcheck', this.bound_table).bind('click',spellcheckButtonClickHandler);
    }
    // Bind the current textbox focus event
    // Make the focused textarea current in the StringSet!
    this.bindFocusTextArea = function() {
        $('tr td textarea.translation', this.bound_table).focus(function() {
            if(window.autosuggestions) {
                var suggestions_tab = $(this).parents('tr').find('.show_suggestions');
                var previous_suggestions_tab = stringset.current_box && stringset.current_box.parents('tr').find('.show_suggestions');
                if(! previous_suggestions_tab || (previous_suggestions_tab.get(0) != suggestions_tab.get(0))) {
                    // close all open tabs
                    $('.tabs_trigger.current').click();

                    // open current string's suggestion tab
                    var suggestions_tab = $(this).parents('tr').find('.show_suggestions');
                    suggestions_tab.click();

                    // scroll page to focused textarea
                    $(document).scrollTop($(this).offset().top - 54);
                }
            }

            stringset.current_box = $(this);
            var textarea = stringset.current_box;
            var id;
            if(textarea.hasClass('default_translation')){
              id = parseInt(textarea.attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            }else{
              id = parseInt(textarea.parents('td.trans').find('.default_translation').attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            }
            if (id != this_stringset.current_id) {
           		this_stringset.pushModifiedString();
            }
            stringset.current_id = id;
        });
    }

    /* Bind undo button events */
    this.bindUndoButton = function() {
        $('tr td.notes span.undo', this.bound_table).click(undoButtonClickHandler);
    }

    // saves last modified stringset
		this.pushModifiedString = function() {
				if ( this_stringset.current_string && this_stringset.must_push ) {
					if ( this_stringset.current_string.modified && this_stringset.must_push ) {
	            /* add timeout and then submit. using the id, this timeout can be canceled */
	            $.doTimeout(this_stringset.current_id.toString(), 1, function(){
	                /* push the string to server */
	                this_stringset.push();
	            });
	        }
				}
		}
		// Auto save on some specific clicks on textarea focusout
		this.pushOnClick = function() {
				$(document).click(function (e) {
						if ($(e.target).parents().filter('tr').length && $(e.target).parents('tr').children('td.trans').length){
              var id = parseInt($(e.target).parents("tr").find("textarea.translation").attr("id").split("_")[1]);
							switch (id) {
								case this_stringset.current_id : break;
							default :
								this_stringset.pushModifiedString();
							}
						}
						else {
							if (!($(e.target).hasClass('spellcheck-badwords') || $(e.target).parents('div').hasClass('spellcheck-badwords')
								|| ($(e.target).parents('div').hasClass('spellcheck-suggestbox'))))
								this_stringset.pushModifiedString();
						}
					})
		}
    // Bind the onblur autosave event
    this.bindBlurTextArea = function() {
        $('tr td textarea.translation', this.bound_table).blur(function() {
            var id;
            var textarea = $(this);
            if(textarea.hasClass('default_translation')){
              id = parseInt(textarea.attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            }else{
              id = parseInt(textarea.parents('td.trans').find('.default_translation').attr("id").split("_")[1]); // Get the id of current textarea -> binding index
            }
			stringset.current_id = id;
            /* Auto-save should be called only if either all textareas are
               filled in or when none of them for an entry are filled. This
               is mostly helpful in cases of plural entries */
            var textareas_filled = 0
            var textareas = textarea.parents('td.trans').find('textarea')
            textareas.each(function(index) {
                if ( this.value != "")
                    textareas_filled += 1;
            });
            if ( textareas_filled == textareas.length || textareas_filled == 0 )
                must_push = true
            else
                must_push = false
            stringset.current_string = this_stringset.strings[id];
            stringset.must_push = must_push;
            stringset.current_row = $(this).parents('tr');
						this_stringset.pushOnClick();

        });
    }

    // Unbind events
    this.unbindBlurTextArea = function() {
        $('tr td textarea.translation', this.bound_table).unbind("blur");
    }
    this.unbindSaveButton = function() {
        $('tr td.notes span.save', this.bound_table).unbind("click");
    }
    this.unbindUndoButton = function() {
        $('tr td.notes span.undo', this.bound_table).unbind("click");
    }

    /* StringSet.bindStats(target_table_id) */
    this.bindStatsAndFilter = function(target_table_id) {
        table = $("table#" + target_table_id);
        this.bound_stats = table
        $('tr td input[type="checkbox"]', table).click(function(){
//            this_stringset.filter();
//            this_stringset.updateView();
        });
    };

    this.translated_modified = 0;
    this.untranslated_modified = 0;

    /* StringSet.updateStats(later=false) */
    this.updateStats = function(later) {
        later = false;
        if (later) {
            clearTimeout(this.update_stats_timer);
            this.update_stats_timer = window.setTimeout(function() { this_stringset.updateStats(); }, 1000);
        } else {
            this.modified = 0;
            for (i=0; i<this.strings.length; i++) {
                j = this.strings[i];
                if (j.modified) {
                    this.modified += 1;
                }
            }

            translated = this.translated - this.translated_modified;
            untranslated = this.untranslated - this.untranslated_modified;
            reviewed = this.reviewed;

            if (this.bound_stats) {
                total = translated + untranslated + this.modified;
                $('#total_sum', this.bound_stats).html(total);
                $('#total_translated', this.bound_stats).html(translated);
                $('#total_translated_perc', this.bound_stats).html(sprintf("%.02f%%", translated*100.0/total));
                $('#total_fuzzy', this.bound_stats).html(this.modified);
                $('#total_fuzzy_perc', this.bound_stats).html(sprintf("%.02f%%", this.modified*100.0/total));
                $('#total_untranslated', this.bound_stats).html(untranslated);
                $('#total_untranslated_perc', this.bound_stats).html(sprintf("%.02f%%", untranslated*100.0/total));
                $('#total_reviewed', this.bound_stats).html(reviewed);
                $('#total_reviewed_perc', this.bound_stats).html(sprintf("%.02f%%", reviewed*100.0/total));
            }
        }
    }

    this.toolbar = function(){
        $('#stringset_table tr').mouseover(function() {
            // button panel
            var obj = $(this).find('.lotte-actions');
            var pos;

            pos = $(this).find("textarea.default_translation").offset();
            w = obj.width();
            // IE8 fix
            if (pos) {
                if(jQuery.browser.msie || (jQuery.browser.webkit && jQuery.browser.version >  534.29) || jQuery.browser.opera){
                  obj.css({top: 4, left: - w + 4});
                }else{
                  obj.css({top:pos.top - 4, left:pos.left - w - 2});
                }
            }

            // show bottom tabs
            var obj2 = $(this).find('.row_tabs');
            obj2.css({'visibility': 'visible'});
        }).mouseout(function() {
            var obj = $(this).find('.lotte-actions');
            obj.css({top:-10000 ,left:-10000});

            // show bottom tabs
            var obj2 = $(this).find('.row_tabs');
            // If there is no tab 'current'
            if(obj2.find('.current').length==0)
                obj2.css({'visibility': 'hidden'});
        });

        // Bind click events for tools
        // 1.Machine translation
        $('.lotte-actions a.suggest').hide();
        auto_translate_supported(source_lang, target_lang, function() {
            $('.lotte-actions a.suggest').show();
            $('.lotte-actions a.suggest').click(function() {
                var a=$(this), str=a.html();
                a.removeClass("action");
                a.addClass("action_go");
                var plural_orig = $('.msg .source_string_plural', a.parents('tr'));
                var orig=$('.msg .source_string', a.parents('tr')).whitespaceHighlight("reset");
                if(plural_orig.length > 0)
                  orig = orig.substring(orig.indexOf('</span>')+7);
                // Get the default (other) translation textarea and corresponding string object
                var default_textarea = $('textarea.default_translation', a.parents('tr'));
                // Get the id of current textarea -> binding index
                var id = parseInt(default_textarea.attr("id").split("_")[1]);
                var string = this_stringset.strings[id];
                $('textarea.translation', a.parents('tr')).each(function(){
                    var trans=$(this);
                    orig = unescape(orig).replace(/<br\s?\/?>/g,'\n').replace(/<code>/g,'').replace(/<\/code>/g,'').replace(/&gt;/g,'>').replace(/&lt;/g,'<');
                    auto_translate_wrapper(orig, source_lang, target_lang, function(result) {
                        if (!result.error) {
                            trans.val(unescape(result.translation).replace(/&#39;/g,'\'').replace(/&quot;/g,'"').replace(/%\s+(\([^\)]+\))\s*s/g,' %$1s '));
                            /* Mark the translated field as modified */
                            string.translate(trans.val(), trans.prev('span.rule').attr('rule'));
                            if (string.modified) {
                                trans.removeClass("fuzzy translated untranslated").addClass("fuzzy"); // Automatically set edited textarea to fuzzy
                                trans.siblings('textarea').removeClass("fuzzy translated untranslated").addClass("fuzzy");
                                // TODO: Check for autosave and handle it.
                                if (enable_spellcheck){
                                	$('tbody tr td.notes span#spellcheck_' + id).removeClass('inactive');
                                	$('tbody tr td.notes span#spellcheck_' + id).unbind('click');
                                	$('tbody tr td.notes span#spellcheck_' + id).bind('click', spellcheckButtonClickHandler);
                                }
                                $('tbody tr td.notes span#save_' + id).removeClass('inactive');
                                $('tbody tr td.notes span#save_' + id).unbind('click');
                                $('tbody tr td.notes span#save_' + id).bind('click', saveButtonClickHandler);
                                $('tbody tr td.notes span#undo_' + id).removeClass('inactive');
                                $('tbody tr td.notes span#undo_' + id).unbind('click');
                                $('tbody tr td.notes span#undo_' + id).bind('click', undoButtonClickHandler);
                                trans.focus();
                            }
                        } else {
                            a.before($('<span class="alert">' + result.error + '</span>'));
                        }
                        a.removeClass("action_go");
                        a.addClass("action");
                        trans.keyup();
                    });
                });
                return false;
            });
        });

        // 2. Copy source string
        $('.lotte-actions a.copy_source').click(function() {
            var a=$(this);
            var plural_orig = $('.msg .source_string_plural', a.parents('tr'));
            var orig=$('.msg .source_string', a.parents('tr')).whitespaceHighlight("reset");
            var pluralized = false;
            if(plural_orig.length > 0){
              pluralized = true;
              orig = orig.substring(orig.indexOf('</span>')+7);
              plurals_dict = {};
              plural_orig.each(function(index, element){
                var s = $(element).whitespaceHighlight("reset");
                s = s.substring(s.indexOf('</span>')+7);
                var rule = $(element).attr('rule');
                plurals_dict[rule] = s;
              });
            }
            // Get the default (other) translation textarea and corresponding string object
            var default_textarea = $('textarea.default_translation', a.parents('tr'));
            // Get the id of current textarea -> binding index
            var id = parseInt(default_textarea.attr("id").split("_")[1]);
            var string = this_stringset.strings[id];
            $('textarea.translation', a.parents('tr')).each(function(){
                var trans=$(this);
                trans.val(html_unescape(orig));
                if (pluralized) {
                  var rule = trans.prev('span').attr('rule');
                  var s = plurals_dict[rule];
                  if (s){
                    s = html_unescape(s);
                    trans.val(s);
                  }
                }
                /* Mark the translated field as modified */
                string.translate(trans.val(), trans.prev('span.rule').attr('rule'));
                if (string.modified) {
                    trans.removeClass("fuzzy translated untranslated").addClass("fuzzy"); // Automatically set edited textarea to fuzzy
                    trans.siblings('textarea').removeClass("fuzzy translated untranslated").addClass("fuzzy");
                    // TODO: Check for autosave and handle it.
                    if (enable_spellcheck){
                    	$('tbody tr td.notes span#spellcheck_' + id).removeClass('inactive');
                    	$('tbody tr td.notes span#spellcheck_' + id).unbind('click');
                        $('tbody tr td.notes span#spellcheck_' + id).bind('click', spellcheckButtonClickHandler);
                    }
                    $('tbody tr td.notes span#save_' + id).removeClass('inactive');
                    $('tbody tr td.notes span#save_' + id).unbind('click');
                    $('tbody tr td.notes span#save_' + id).bind('click', saveButtonClickHandler);
                    $('tbody tr td.notes span#undo_' + id).removeClass('inactive');
                    $('tbody tr td.notes span#undo_' + id).unbind('click');
                    $('tbody tr td.notes span#undo_' + id).bind('click', undoButtonClickHandler);
                    trans.keyup();
                    trans.focus();
                }
            });
        });

        // 3 Show details row trigger
        $('a.tabs_trigger').click(function(){
                for (var i=0; i < toolbars.length; i++) {
                    if (toolbars[i][1](this) == true)
                        break;
                }
                return false;
        });

        // Bind sliding animation, and positioning for each button in the toolbar
        $('.lotte-actions p').each(function(){
            // panel buttons replacement for cross-browsing reasons
            w = $('a', this).width();
            $(this).css({right: - w - 14});
            // hover animation
            $(this).hoverIntent({
                sensitivity: 7,
                interval: 160,
                over: function(){
                    $(this).animate({right:0}, {duration:'fast'});
                },
                timeout: 0,
                out: function() {
                    w = $('a', this).width();
                    $(this).animate({right: - w - 14}, {duration:'fast'});
                }
            });
        });

    }

}

lotte_tabs = function(that) {
    /*
    Function for handling the default tabs of Lotte for each row. Extra tabs
    from addons can be added too, requiring a piece of code like this. For
    solving this issue, we created a global `toolbars` array that holds JS
    functions that must be executed in order. This function must be always in
    the end of the list.

    See StringSet.toolbar for more details. The var `toolbars` is instantiated
    in lotte/template/translate.html and addons can insert functions in it
    through a hook called 'tab_lotte.html' within the 'function' block.
    */
    var nTr = $(that).parents('tr');

    if(!$(that).hasClass('current') && $(that).hasClass('show_details')){

        // Close any previously opened tabs
        var previous_open = $(that).parents('.row_tabs').find('.current');
        if(previous_open!=0){
            nTr.next('tr.metatr').remove();
            previous_open.removeClass('current');
        }

        nTr.after('<tr class="metatr details"><td colspan="4" class="inject_here"><div style="text-align:center"><span class="i16 action_go">loading ...</span></div></td></tr>');
        var source_id = parseInt(nTr.find('.source_id').text());

        // Get the details and inject them.
        var tab_details_urlp = tab_details_urlp_tmpl.replace('1111111111', source_id)
        nTr.next(".details").find("td.inject_here").load(tab_details_urlp, function(response, status, xhr) {
            if (status == "error") {
            var msg = "Sorry but there was an error: ";
            alert(msg + xhr.status + " " + xhr.statusText);
            }
        });

        // Put 1px border around tab
        nTr.css({'border-bottom':'1px solid #EEE'});

        // Fix 'current' class
        if(!$(that).hasClass('current'))
            $(that).addClass('current');

    }else if(!$(that).hasClass('current') && $(that).hasClass('show_suggestions')){

        // Close any previously opened tabs
        var previous_open = $(that).parents('.row_tabs').find('.current');
        if(previous_open!=0){
            nTr.next('tr.metatr').remove();
            previous_open.removeClass('current');
        }

        nTr.after('<tr class="metatr suggestions"><td colspan="4" class="inject_here"><div style="text-align:center"><span class="i16 action_go">loading ...</span></div></td></tr>');
        var source_id = parseInt(nTr.find('.source_id').text());

        // Get the details and inject them.
        var tab_suggestions_urlp = tab_suggestions_urlp_tmpl.replace('1111111111', source_id)
        nTr.next(".suggestions").find("td.inject_here").load(tab_suggestions_urlp, function(response, status, xhr) {
            if (status == "error") {
            var msg = "Sorry but there was an error: ";
            alert(msg + xhr.status + " " + xhr.statusText);
            }
        });

        // Put 1px border around tab
        nTr.css({'border-bottom':'1px solid #EEE'});

        // Fix 'current' class
        if(!$(that).hasClass('current'))
            $(that).addClass('current');

    }else{
        // Close any previously opened tabs
        var previous_open = $(that).parents('.row_tabs').find('.current');
        if(previous_open!=0){
            nTr.next('tr.metatr').remove();
            previous_open.removeClass('current');
        }

        // Put back the 3px border
        nTr.css({'border-bottom':'3px solid #EEE'});

        // Fix 'current' class
        if($(that).hasClass('current'))
            $(that).removeClass('current');
    }
}
