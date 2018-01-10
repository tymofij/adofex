
/* Global functions */
function json_request(type, url, struct, callback) {
    if (callback) {
        var fp = function(xmlhttpreq, textStatus) {
//            alert(textStatus + ": " + xmlhttpreq.responseText);
            callback(textStatus, JSON.parse(xmlhttpreq.responseText));
        }
    } else {
        var fp = null;
    }
    $.ajax({
        contentType : 'application/json', /* Workaround for django-piston */
        url: url,
        global : false,
        type : type,
        dataType: 'text', /* Workaround for django-piston */
        data: JSON.stringify(struct), /* Workaround for django-piston */
        complete: fp
    });
}

/*
Code related to disassociation of project from a project hub. It's used in the
Access control page.
*/

associate_classes = Array('connect', 'undo');

function hub_associate_project_toggler_handler(data, textStatus){

    obj = $('#association-' + String(data.outsourced_project_slug));

    if (data.error){
        obj.attr('title', data.error);
        obj.removeClass('waiting');
        obj.addClass(data.style);
    }else{
        obj.attr('title', data.title);
        obj.click(bind_hub_associate_project_toggler(obj, data.outsourced_project_slug, data.url))
        obj.removeClass('waiting');
        obj.addClass(data.style);
        obj.html(data.title);
    }
}

function bind_hub_associate_project_toggler(obj, project_slug, url){
    return function(){
        hub_associate_project_toggler(obj, project_slug, url);
    }
}

function hub_associate_project_toggler(obj, project_slug, url){
    obj.onclick = null;
    o = $(obj);
    o.unbind('click');
    for (cls in associate_classes){
        if (o.hasClass(associate_classes[cls])){
            o.removeClass(associate_classes[cls]);
        }
    }
    o.addClass('waiting'); /* will be removed in the callback */
    $.post(
        url=url, 
        data = {outsourced_project_slug:project_slug},
        callback=hub_associate_project_toggler_handler,
        type='json');
}
