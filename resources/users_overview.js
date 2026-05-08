$(document).ready(function () {
    let active_status = $(
        'body.template-usergroup-userprefs select[name="users.active:records"]',
    );
    active_status.on("change", function () {
        let el = $(this);
        if (el.val() === "inactive") {
            el.addClass("border border-danger");
            el.removeClass("border-success");
        } else if (el.val() === "active") {
            el.addClass("border border-success");
            el.removeClass("border-danger");
        }
    });

    let float_buttons = (entries, observer) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                $("#usersoverview-submit-sticky").hide();
            } else {
                $("#usersoverview-submit-sticky").show();
            }
        });
    };

    // use IntersectionObserver
    let observer = new IntersectionObserver(float_buttons, {
            root: document.getElementById("users_manage_table_wrapper"),
            rootMargin: "0px",
            threshold: 1,
        }),
        target = document.getElementById("usersoverview-submit");

    if ("#users_manage") {
        $("#users_manage input, #users_manage select").change(function () {
            observer.observe(target);
        });
    }

    $('body.template-usergroup-userprefs a[data-bs-toggle="popover"]').click(
        function (event) {
            event.stopPropagation();
        },
    );
});
