/* we can't actually disable the last_name field (or even change it to type="hidden" because
 the form validator doesn't like that. So just hide it with css and make a new dummy field that
 is disabled and copies the last_name field's value
 */
$(document).ready(function () {
    $.each(
        ["personal-information", "user-information"],
        function (template_index, template_value) {
            $.each(
                ["fullname", "first_name", "last_name", "email"],
                function (field_index, field_value) {
                    let el = $(
                        "body.template-" +
                        template_value +
                        " #form-widgets-" +
                        field_value,
                    );
                    if (el.length) {
                        el.addClass("d-none");
                        el.after(
                            '<input type="text" name="fake_' +
                            field_value +
                            '" class="form-control" id="fake_' +
                            field_value +
                            '" />',
                        );
                        let fake_el = $("#fake_" + field_value);
                        fake_el.val(el.val());
                        fake_el.attr("disabled", "disabled");
                    }
                },
            );
        },
    );
});
