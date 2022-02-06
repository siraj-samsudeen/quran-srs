$(document).ready(function () {
    // the update button could be clicked multiple times if the reload is slow
    // Hence disable it when the form is submitted
    $('form.card').on('submit', function () {
        $("button:contains('Update')").prop("disabled", true)
    })
})