django.jQuery(document).ready(function(){
    django.jQuery('#id_feed_url').blur(function(){
        if(django.jQuery('#id_name')[0].value==""){
            django.jQuery.getJSON("/feedtitle/?url="+escape(django.jQuery('#id_feed_url')[0].value), function(data){
                django.jQuery('#id_name')[0].value=data;
                django.jQuery('#id_name').change();
            });
        }
    });
});
