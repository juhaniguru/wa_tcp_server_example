import re


def render_simple_template(template_string, data):
    """
    Renders a simplified Jinja-like template.

    Args:
        template_string: The template string.
        data: A dictionary containing the variables.

    Returns:
        The rendered template string.
    """

    def replace_variable(match):
        variable_name = match.group(1).strip()
        return str(data.get(variable_name, ""))

    def process_for_loop(match):
        loop_content = match.group(0)
        loop_parts = re.findall(r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}', loop_content, re.DOTALL)

        if not loop_parts:
            return loop_content  # return original content if no matches.

        variable_name, iterable_name, inner_content = loop_parts[0]
        iterable = data.get(iterable_name, [])
        if not isinstance(iterable, list):
            return ""

        result = ""
        for item in iterable:
            local_data = {**data, variable_name: item}  # Create local data with loop variable.
            result += render_simple_template(inner_content, local_data)  # Recursive call.
        return result

    # Handle for loops first (important!)
    while True:
        loop_match = re.search(r'{%\s*for\s+\w+\s+in\s+\w+\s*%}.*?{%\s*endfor\s*%}', template_string, re.DOTALL)
        if not loop_match:
            break
        template_string = template_string.replace(loop_match.group(0), process_for_loop(loop_match))

    # Handle variable replacements
    template_string = re.sub(r'{{(.*?)}}', replace_variable, template_string)

    return template_string


# Example Usage:

template_list = """
<ul>
{% for item in items %}
  <li>{{ item }}</li>
{% endfor %}
</ul>
"""

data_list = {"items": ["apple", "banana", "cherry"]}
rendered_list = render_simple_template(template_list, data_list)
print("List Example:")
print(rendered_list)



