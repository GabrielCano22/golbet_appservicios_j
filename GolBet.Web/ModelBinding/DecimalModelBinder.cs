using System.Globalization;
using Microsoft.AspNetCore.Mvc.ModelBinding;

namespace GolBet.Web.ModelBinding;

// Accept either decimal separator without treating dots as thousands separators in es-CO.
public sealed class DecimalModelBinder : IModelBinder
{
    public Task BindModelAsync(ModelBindingContext bindingContext)
    {
        var value = bindingContext.ValueProvider.GetValue(bindingContext.ModelName);
        if (value == ValueProviderResult.None) return Task.CompletedTask;
        bindingContext.ModelState.SetModelValue(bindingContext.ModelName, value);
        var text = value.FirstValue?.Trim().Replace(',', '.');
        if (decimal.TryParse(text, NumberStyles.AllowLeadingSign | NumberStyles.AllowDecimalPoint,
            CultureInfo.InvariantCulture, out var number))
            bindingContext.Result = ModelBindingResult.Success(number);
        else
            bindingContext.ModelState.TryAddModelError(bindingContext.ModelName,
                "Ingrese una cuota válida, por ejemplo 2,50 o 2.50.");
        return Task.CompletedTask;
    }
}

public sealed class DecimalModelBinderProvider : IModelBinderProvider
{
    public IModelBinder? GetBinder(ModelBinderProviderContext context)
        => context.Metadata.ModelType == typeof(decimal) ? new DecimalModelBinder() : null;
}
