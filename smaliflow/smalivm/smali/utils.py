def parse_method_parameters(parameters_line: str) -> list[str]:
    parameters: list[str] = []

    parameter = None
    for i in parameters_line:
        if (
            parameter is not None
            and len(parameter) >= 2
            and parameter[-2] == "["
            and parameter[-1] != "["
            and parameter[-1] != "L"
        ):
            parameters.append(parameter)
            parameter = None
        if parameter is not None:
            if i == ";":
                parameters.append(parameter + ";")
                parameter = None
                continue
            else:
                parameter += i
                continue
        if i == "L" or i == "[":
            parameter = i
        else:
            parameters.append(i)
    if parameter is not None and len(parameter) > 0:
        parameters.append(parameter)

    return parameters