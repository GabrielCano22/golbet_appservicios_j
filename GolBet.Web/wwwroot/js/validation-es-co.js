(function ($) {
    $.extend($.validator.messages, {
        required: "Este campo es obligatorio.",
        number: "Ingrese un número válido.",
        date: "Ingrese una fecha válida.",
        url: "Ingrese una URL válida.",
        maxlength: $.validator.format("Máximo {0} caracteres."),
        range: $.validator.format("Ingrese un valor entre {0} y {1}.")
    });

    $.validator.methods.number = function (value, element) {
        return this.optional(element) || /^[+-]?\d+(?:[.,]\d+)?$/.test(value.trim());
    };
    $.validator.methods.range = function (value, element, bounds) {
        var number = Number(value.trim().replace(",", "."));
        return this.optional(element) || (Number.isFinite(number) && number >= bounds[0] && number <= bounds[1]);
    };
})(jQuery);
