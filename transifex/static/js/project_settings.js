$(document).ready(function (){
	$(".tipsy_enable").tipsy({'html':true, 'gravity':'s'});

  if($('input#id_project-tags').length>0) {
		$('input#id_project-tags').relatedTagsCloud();
	}
	
	var fieldColumnsa = {
    "fieldsLeft": [
        "project-slug",
        "project-description",
 				"project-source_language",
 				"project-private",
 				"project-fill_up_resources",
 				"project-logo"
    ],
    "fieldsRight": [
        "project-name",
        "project-license",
 				"project-maintainers"
    ]
	};
	$("#project-forma").dualtxf(fieldColumnsa);

  var fieldColumnsb = {
    "fieldsLeft": [
        "project-homepage",
 				"project-feed",
 				"project-long_description"
    ],
    "fieldsRight": [
        "project-trans_instructions",
 				"project-bug_tracker",
 				"project-webhook",
 				"project-auto_translate_select_service",
 				"project-auto_translate_api_key"
    ]
	};
  $("#project-formb").dualtxf(fieldColumnsb);
	
  
	if($("#project-edit-advanced ul.errorlist").length>0){
		$(".tx-form #project-edit-advanced").slideDown("fast",function(){$(".side-menu").css('height',$(".psettings-content").height());}); }			$(".side-menu").css('height',$(".psettings-content").height()+$("#project-tags").height());
  
  /* Prevent form submit when enter is pressed in maintainers input field */
  $('input#id_project-maintainers_text').bind('keypress', function(e){
      if (e.which == 13)
      return false;
  });
  
	$('.tx-form .required, .tx-form .field-helptext').each(function(){
		$(this).appendTo($(this).siblings('label'));
	});
  $(".txf-checkbox").each(function(){
    $(this).find("span.field-helptext").appendTo($(this));
  });

	/*Check if there are errors in the slidable form. If yes then slides down*/
	$('.tx-form #display-advform').click(function(){
		$(this).toggleClass("active");
		$(".tx-form #project-edit-advanced").slideToggle("fast",function(){$(".side-menu").css('height',$(".psettings-content").height());});
	});

  $("select#id_project-source_language").chosen();
});


