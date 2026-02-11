from decimal import Decimal, ROUND_HALF_UP


def round_decimal(value):
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)


def get_array_param(request, param_name):
    raw_values = request.query_params.getlist(param_name)
    processed_values = []
    for val in raw_values:
        if "," in val:
            processed_values.extend(val.split(","))
        else:
            processed_values.append(val)
    return [v.strip() for v in processed_values if v.strip()]
