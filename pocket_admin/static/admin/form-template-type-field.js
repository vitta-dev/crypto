jQuery(document).ready(function() {

    function tpl_hide_show_dictionary(obj){
        var value = obj.val();
        var id = obj.attr('id').replace('id_tpl_fields-', '').replace('-type', '');

        if(value == '12') { // показываем список словарей
            $('#id_tpl_fields-'+id+'-dictionary').closest('.related-widget-wrapper').show();
            $('#id_tpl_fields-'+id+'-employee_role').closest('.related-widget-wrapper').hide();
        }
        else if(value == '13'){
            $('#id_tpl_fields-'+id+'-employee_role').closest('.related-widget-wrapper').show();
            $('#id_tpl_fields-'+id+'-dictionary').closest('.related-widget-wrapper').hide();
        }
        else {
            $('#id_tpl_fields-'+id+'-dictionary').closest('.related-widget-wrapper').hide();
            $('#id_tpl_fields-'+id+'-employee_role').closest('.related-widget-wrapper').hide();
        }
    }


    $('.template-field-type').on('click', function(event){
        event.preventDefault()
        tpl_hide_show_dictionary($(this));
    }).each(function () {
        tpl_hide_show_dictionary($(this));
    });



    function hide_show_dictionary(obj){
        var value = obj.val();
        var id = obj.attr('id').replace('id_block_fields-', '').replace('-type', '');


        if(value == '12') { // показываем список словарей
            //$('#id_block_fields-'+id+'-dictionary').closest('.field-box').show();
            $('#id_block_fields-'+id+'-dictionary').closest('.related-widget-wrapper').show();
            //$('#id_block_fields-'+id+'-employee_role').closest('.field-box').hide();
            $('#id_block_fields-'+id+'-employee_role').closest('.related-widget-wrapper').hide();
        }
        else if(value == '13'){
            $('#id_block_fields-'+id+'-employee_role').closest('.related-widget-wrapper').show();
            $('#id_block_fields-'+id+'-dictionary').closest('.related-widget-wrapper').hide();
        }
        else {
            $('#id_block_fields-'+id+'-dictionary').closest('.related-widget-wrapper').hide();
            $('#id_block_fields-'+id+'-employee_role').closest('.related-widget-wrapper').hide();
        }
    }


    $('.block-field-type').on('click', function(){
        event.preventDefault(event);
        hide_show_dictionary($(this));
    }).each(function () {
        hide_show_dictionary($(this));
    });







});
